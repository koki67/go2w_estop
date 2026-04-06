from unitree_api.msg import Request


API_BALANCE_STAND = 1002


class RobotAdapter:
    def __init__(self, sport_publisher) -> None:
        self._publisher = sport_publisher
        self._asserting = False

    def assert_balance_stand(self) -> bool:
        request = Request()
        request.header.identity.api_id = API_BALANCE_STAND
        request.parameter = ""
        self._publisher.publish(request)
        self._asserting = True
        return True

    def get_health(self) -> str:
        return "OK"

    def describe_current_action(self) -> str:
        return "BALANCE_STAND" if self._asserting else "NONE"
