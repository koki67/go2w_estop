"""Curses-based terminal UI for the operator-side e-stop client."""

import curses
from typing import Dict, Optional


class TerminalUI:
    def __init__(self) -> None:
        self._screen = None
        self._is_setup = False

    def setup(self) -> None:
        self._screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self._screen.keypad(True)
        self._screen.nodelay(True)
        self._is_setup = True

    def teardown(self) -> None:
        if not self._is_setup:
            return
        assert self._screen is not None
        self._screen.keypad(False)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        self._screen = None
        self._is_setup = False

    def get_key(self) -> Optional[str]:
        if self._screen is None:
            return None
        try:
            key = self._screen.getch()
        except curses.error:
            return None
        if key == -1:
            return None
        if key == ord(" "):
            return "SPACE"
        if key == 27:
            return "ESC"
        if key in (ord("q"), ord("Q")):
            return "q"
        return None

    def render(self, status_data: Dict[str, str]) -> None:
        if self._screen is None:
            return

        lines = [
            "GO2-W Virtual Emergency Stop",
            "",
            f"Connection         : {status_data['connection_state']}",
            f"Last status age    : {status_data['last_status_age']}",
            f"Current state      : {status_data['current_state']}",
            f"Last trigger       : {status_data['last_trigger_type']}",
            f"Latched            : {status_data['latched']}",
            f"Asserted action    : {status_data['asserted_robot_action']}",
            f"Expected NIC       : {status_data['expected_nic']}",
        ]
        if status_data["error_text"]:
            lines.extend(["", f"Error               : {status_data['error_text']}"])
        lines.extend(
            [
                "",
                "Keys",
                "  Space : Protective stop",
                "  Esc   : Hard stop",
                "  q     : Quit operator client",
            ]
        )

        height, width = self._screen.getmaxyx()
        self._screen.erase()
        for index, line in enumerate(lines[: max(height - 1, 1)]):
            self._screen.addnstr(index, 0, line, max(width - 1, 1))
        self._screen.refresh()
