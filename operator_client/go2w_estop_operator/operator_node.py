#!/usr/bin/env python3
"""Operator-side virtual e-stop client for the Unitree GO2-W."""

from dataclasses import dataclass
import time

import rclpy
from estop_interfaces.msg import EstopStatus
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import Empty

from go2w_estop_operator.nic_validator import validate_nic
from go2w_estop_operator.terminal_ui import TerminalUI


@dataclass(frozen=True)
class OperatorConfig:
    protective_stop_topic: str
    hard_stop_topic: str
    status_topic: str
    expected_nic: str
    nic_exclude_prefixes: list[str]
    validate_nic_on_startup: bool
    status_stale_after_sec: float

    @classmethod
    def from_node(cls, node) -> "OperatorConfig":
        config = cls(
            protective_stop_topic=str(
                node.get_parameter("protective_stop_topic").value
            ),
            hard_stop_topic=str(node.get_parameter("hard_stop_topic").value),
            status_topic=str(node.get_parameter("status_topic").value),
            expected_nic=str(node.get_parameter("expected_nic").value),
            nic_exclude_prefixes=list(
                node.get_parameter("nic_exclude_prefixes").value
            ),
            validate_nic_on_startup=bool(
                node.get_parameter("validate_nic_on_startup").value
            ),
            status_stale_after_sec=float(
                node.get_parameter("status_stale_after_sec").value
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.expected_nic:
            raise ValueError("expected_nic must not be empty")
        if self.status_stale_after_sec <= 0.0:
            raise ValueError("status_stale_after_sec must be > 0")


class EstopOperatorNode(Node):
    def __init__(self) -> None:
        super().__init__("go2w_estop_operator_node")

        self.declare_parameter("protective_stop_topic", "/estop/protective_stop")
        self.declare_parameter("hard_stop_topic", "/estop/hard_stop")
        self.declare_parameter("status_topic", "/estop/status")
        self.declare_parameter("expected_nic", "enp97s0")
        self.declare_parameter(
            "nic_exclude_prefixes", ["docker", "veth", "br-", "virbr", "lxc"]
        )
        self.declare_parameter("validate_nic_on_startup", True)
        self.declare_parameter("status_stale_after_sec", 2.0)

        self._config = OperatorConfig.from_node(self)
        self._validate_nic()

        reliable_qos = QoSProfile(depth=10)
        reliable_qos.reliability = ReliabilityPolicy.RELIABLE

        self._protective_pub = self.create_publisher(
            Empty, self._config.protective_stop_topic, reliable_qos
        )
        self._hard_pub = self.create_publisher(
            Empty, self._config.hard_stop_topic, reliable_qos
        )
        self._status_sub = self.create_subscription(
            EstopStatus,
            self._config.status_topic,
            self._on_status,
            reliable_qos,
        )

        self._ui = TerminalUI()
        self._last_status_monotonic = None
        self._status_cache = {
            "current_state": "UNKNOWN",
            "last_trigger_type": "NONE",
            "latched": "False",
            "asserted_robot_action": "NONE",
            "error_text": "",
        }

        self.get_logger().info(
            "Operator client ready: "
            f"protective={self._config.protective_stop_topic}, "
            f"hard={self._config.hard_stop_topic}, "
            f"status={self._config.status_topic}, "
            f"expected_nic={self._config.expected_nic}, "
            f"validate_nic_on_startup={self._config.validate_nic_on_startup}"
        )

    def _validate_nic(self) -> None:
        if not self._config.validate_nic_on_startup:
            self.get_logger().warn("NIC validation disabled by parameter override")
            return

        result = validate_nic(
            self._config.expected_nic,
            self._config.nic_exclude_prefixes,
        )
        if not result.valid:
            self.get_logger().error(result.error_reason)
            self.get_logger().error(result.format_diagnostics())
            raise RuntimeError(result.error_reason)

        self.get_logger().info(
            f"NIC validation succeeded for {self._config.expected_nic}"
        )

    def _on_status(self, msg: EstopStatus) -> None:
        self._last_status_monotonic = time.monotonic()
        self._status_cache = {
            "current_state": msg.current_state,
            "last_trigger_type": msg.last_trigger_type,
            "latched": str(msg.latched),
            "asserted_robot_action": msg.asserted_robot_action,
            "error_text": msg.error_text,
        }

    def _publish_protective_stop(self) -> None:
        self._protective_pub.publish(Empty())
        self.get_logger().warn("Published protective stop")

    def _publish_hard_stop(self) -> None:
        self._hard_pub.publish(Empty())
        self.get_logger().warn("Published hard stop")

    def _build_view_model(self) -> dict[str, str]:
        connection_state = "DISCONNECTED"
        last_status_age = "never"
        if self._last_status_monotonic is not None:
            age = time.monotonic() - self._last_status_monotonic
            last_status_age = f"{age:.1f}s"
            if age <= self._config.status_stale_after_sec:
                connection_state = "CONNECTED"

        return {
            **self._status_cache,
            "connection_state": connection_state,
            "last_status_age": last_status_age,
            "expected_nic": self._config.expected_nic,
        }

    def run(self) -> None:
        self._ui.setup()
        try:
            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.05)
                key = self._ui.get_key()
                if key == "SPACE":
                    self._publish_protective_stop()
                elif key == "ESC":
                    self._publish_hard_stop()
                elif key == "q":
                    break
                self._ui.render(self._build_view_model())
        finally:
            self._ui.teardown()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = EstopOperatorNode()
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()
