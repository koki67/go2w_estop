#!/usr/bin/env python3
"""Robot-side virtual e-stop service for the Unitree GO2-W."""

import traceback

import rclpy
from estop_interfaces.msg import EstopStatus
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import Empty
from unitree_api.msg import Request

from go2w_estop_robot.config import RobotServiceConfig
from go2w_estop_robot.robot_adapter import RobotAdapter
from go2w_estop_robot.state_machine import Event, State, StateMachine


class EstopRobotNode(Node):
    def __init__(self) -> None:
        super().__init__("go2w_estop_robot_node")

        self.declare_parameter("protective_stop_topic", "/estop/protective_stop")
        self.declare_parameter("hard_stop_topic", "/estop/hard_stop")
        self.declare_parameter("status_topic", "/estop/status")
        self.declare_parameter("sport_request_topic", "/api/sport/request")
        self.declare_parameter("assert_rate_hz", 5.0)
        self.declare_parameter("status_rate_hz", 2.0)

        self._config = RobotServiceConfig.from_node(self)
        self._state_machine = StateMachine()

        reliable_qos = QoSProfile(depth=10)
        reliable_qos.reliability = ReliabilityPolicy.RELIABLE

        self._status_pub = self.create_publisher(
            EstopStatus, self._config.status_topic, reliable_qos
        )
        self._sport_request_pub = self.create_publisher(
            Request, self._config.sport_request_topic, 10
        )
        self._adapter = RobotAdapter(self._sport_request_pub)

        self._protective_sub = self.create_subscription(
            Empty,
            self._config.protective_stop_topic,
            self._on_protective_stop,
            reliable_qos,
        )
        self._hard_sub = self.create_subscription(
            Empty,
            self._config.hard_stop_topic,
            self._on_hard_stop,
            reliable_qos,
        )

        self._assert_timer = self.create_timer(
            1.0 / self._config.assert_rate_hz, self._assertion_timer_callback
        )
        self._status_timer = self.create_timer(
            1.0 / self._config.status_rate_hz, self._status_timer_callback
        )

        self.get_logger().info(
            "Robot service ready: "
            f"protective={self._config.protective_stop_topic}, "
            f"hard={self._config.hard_stop_topic}, "
            f"status={self._config.status_topic}, "
            f"sport_request={self._config.sport_request_topic}, "
            f"assert_rate_hz={self._config.assert_rate_hz:.1f}, "
            f"status_rate_hz={self._config.status_rate_hz:.1f}"
        )

    def _on_protective_stop(self, _msg: Empty) -> None:
        self._handle_trigger(Event.PROTECTIVE_STOP_TRIGGERED, "PROTECTIVE")

    def _on_hard_stop(self, _msg: Empty) -> None:
        self._handle_trigger(Event.HARD_STOP_TRIGGERED, "HARD")

    def _handle_trigger(self, event: Event, label: str) -> None:
        try:
            if self._state_machine.state is State.READY:
                transitioned = self._state_machine.process_event(event)
                if transitioned:
                    self.get_logger().warn(f"{label} stop triggered")
                return

            self._state_machine.process_event(Event.REPEATED_TRIGGER)
            self.get_logger().warn(
                f"Ignoring repeated {label.lower()} stop trigger while state="
                f"{self._state_machine.state.value}"
            )
        except Exception as exc:  # pragma: no cover - defensive fault path
            self._handle_internal_fault(exc)

    def _assertion_timer_callback(self) -> None:
        try:
            if self._state_machine.state not in (
                State.PROTECTIVE_STOPPING,
                State.HARD_STOPPING,
                State.STOPPED_LATCHED,
            ):
                return

            self._adapter.assert_balance_stand()
            self._state_machine.note_asserted_action(
                self._adapter.describe_current_action()
            )
            self.get_logger().debug("Asserted Balance Stand")

            if self._state_machine.state in (
                State.PROTECTIVE_STOPPING,
                State.HARD_STOPPING,
            ):
                if self._state_machine.process_event(Event.LATCH_COMMITTED):
                    self.get_logger().warn("E-stop latched; power-cycle required")
        except Exception as exc:  # pragma: no cover - defensive fault path
            self._handle_internal_fault(exc)

    def _status_timer_callback(self) -> None:
        snapshot = self._state_machine.get_snapshot()
        msg = EstopStatus()
        msg.current_state = snapshot.current_state.value
        msg.last_trigger_type = snapshot.last_trigger_type.value
        msg.latched = snapshot.latched
        msg.last_status_timestamp = self.get_clock().now().to_msg()
        msg.error_text = snapshot.error_text
        msg.asserted_robot_action = snapshot.asserted_robot_action
        self._status_pub.publish(msg)

    def _handle_internal_fault(self, exc: Exception) -> None:
        detail = f"{type(exc).__name__}: {exc}"
        self._state_machine.process_event(
            Event.INTERNAL_FAULT,
            error_text=detail,
        )
        self.get_logger().error(detail)
        self.get_logger().debug(traceback.format_exc())


def main(args=None) -> None:
    rclpy.init(args=args)
    node = EstopRobotNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
