from dataclasses import dataclass
from enum import Enum


class State(str, Enum):
    READY = "READY"
    PROTECTIVE_STOPPING = "PROTECTIVE_STOPPING"
    HARD_STOPPING = "HARD_STOPPING"
    STOPPED_LATCHED = "STOPPED_LATCHED"
    FAULT = "FAULT"


class TriggerType(str, Enum):
    NONE = "NONE"
    PROTECTIVE = "PROTECTIVE"
    HARD = "HARD"


class Event(str, Enum):
    PROTECTIVE_STOP_TRIGGERED = "PROTECTIVE_STOP_TRIGGERED"
    HARD_STOP_TRIGGERED = "HARD_STOP_TRIGGERED"
    LATCH_COMMITTED = "LATCH_COMMITTED"
    INTERNAL_FAULT = "INTERNAL_FAULT"
    REPEATED_TRIGGER = "REPEATED_TRIGGER"


@dataclass(frozen=True)
class StateMachineSnapshot:
    current_state: State
    last_trigger_type: TriggerType
    latched: bool
    error_text: str
    asserted_robot_action: str


class StateMachine:
    def __init__(self) -> None:
        self.state = State.READY
        self.last_trigger_type = TriggerType.NONE
        self.latched = False
        self.asserted_robot_action = "NONE"
        self.error_text = ""

    def process_event(self, event: Event, *, error_text: str = "") -> bool:
        if event is Event.INTERNAL_FAULT:
            changed = self.state is not State.FAULT or self.error_text != error_text
            self.state = State.FAULT
            self.error_text = error_text
            return changed

        if self.state is State.READY:
            if event is Event.PROTECTIVE_STOP_TRIGGERED:
                self.state = State.PROTECTIVE_STOPPING
                self.last_trigger_type = TriggerType.PROTECTIVE
                self.error_text = ""
                return True
            if event is Event.HARD_STOP_TRIGGERED:
                self.state = State.HARD_STOPPING
                self.last_trigger_type = TriggerType.HARD
                self.error_text = ""
                return True
            return False

        if self.state in (State.PROTECTIVE_STOPPING, State.HARD_STOPPING):
            if event is Event.LATCH_COMMITTED:
                self.state = State.STOPPED_LATCHED
                self.latched = True
                return True
            return False

        return False

    def note_asserted_action(self, action: str) -> None:
        self.asserted_robot_action = action

    def clear_asserted_action(self) -> None:
        self.asserted_robot_action = "NONE"

    def get_snapshot(self) -> StateMachineSnapshot:
        return StateMachineSnapshot(
            current_state=self.state,
            last_trigger_type=self.last_trigger_type,
            latched=self.latched,
            error_text=self.error_text,
            asserted_robot_action=self.asserted_robot_action,
        )
