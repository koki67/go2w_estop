from dataclasses import dataclass


@dataclass(frozen=True)
class RobotServiceConfig:
    protective_stop_topic: str
    hard_stop_topic: str
    status_topic: str
    sport_request_topic: str
    assert_rate_hz: float
    status_rate_hz: float

    @classmethod
    def from_node(cls, node) -> "RobotServiceConfig":
        config = cls(
            protective_stop_topic=str(
                node.get_parameter("protective_stop_topic").value
            ),
            hard_stop_topic=str(node.get_parameter("hard_stop_topic").value),
            status_topic=str(node.get_parameter("status_topic").value),
            sport_request_topic=str(node.get_parameter("sport_request_topic").value),
            assert_rate_hz=float(node.get_parameter("assert_rate_hz").value),
            status_rate_hz=float(node.get_parameter("status_rate_hz").value),
        )
        config.validate()
        return config

    def validate(self) -> None:
        for field_name in (
            "protective_stop_topic",
            "hard_stop_topic",
            "status_topic",
            "sport_request_topic",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must not be empty")
        if self.assert_rate_hz <= 0.0:
            raise ValueError("assert_rate_hz must be > 0")
        if self.status_rate_hz <= 0.0:
            raise ValueError("status_rate_hz must be > 0")
