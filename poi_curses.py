# Clear the screen and hold it for 3 seconds
import curses
import textwrap
from enum import Enum, auto
from typing import OrderedDict


class CursesCommands(Enum):
    NORMAL = auto()
    QUIT = auto()

class PoiCurses:
    def __init__(self, screen) -> None:
        self._screen = screen
        self._screen.nodelay(True)
        self.write_layout()
        self._state = CursesCommands.NORMAL
        self._messages = []
        self._furthest_line_written = 0

    def write_layout(self):
        # Clear screen
        layout = """POI Tracker
AGL:              Ground Speed: 






        """
        layout = textwrap.dedent(layout)
        self._screen.addstr(0, 0, layout)
    
    def write_ground_speed(self, speed):
        self._screen.addstr(1, 32, f"{str(int(speed))} kts")

    def write_agl(self, feet: float):
        self._screen.addstr(1, 5, f"{int(feet)} ft")

    def write_closest_unvisited_pois(self, pois = []):
        line_num = 3
        self._screen.addstr(line_num, 0, "Closest Unvisited POIs:")
        line_num += 1
        for m in pois:
            self._screen.addstr(line_num, 0, f"{m.name}, {m.distance:.1f} nm, {m.bearing:.0f}°")
            line_num += 1
        self._furthest_line_written = line_num
        
    def write_closest_visited_pois(self, pois = []):
        line_num = self._furthest_line_written + 1
        self._screen.addstr(line_num, 0, "Closest Visited POIs:")
        line_num += 1
        for m in pois:
            self._screen.addstr(line_num, 0, f"{m.name}, {m.distance:.1f} nm, {m.bearing:.0f}°")
            line_num += 1
        self._furthest_line_written = line_num

    def clear_messages(self):
        self._furthest_line_written = 0
        eraser = " " * curses.COLS
        start = 12
        for i in range(start, curses.LINES - 1):
            self._screen.addstr(i, 0, f"{eraser}")
            i += 1

    def _write_messages_to_screen(self):
        i = 12
        max_messages = curses.LINES - 1 - i
        # Deduplicate messages
        self._messages = list(OrderedDict.fromkeys(self._messages))
        for m in self._messages[0:max_messages]:
            self._screen.addstr(i, 0, f"{m}")
            i += 1
        if len(self._messages) > max_messages:
            self._screen.addstr(i, 0, "Additional messages truncated.")

    def write_messages(self, messages: list):
        self._messages += messages

    def write_message(self, msg):
        self._messages.append(str(msg))

    def update(self):
        self._write_messages_to_screen()
        k = self._screen.getch()
        self._messages = []
        self._screen.clear()
        self.write_layout()
        if k == ord("q") or k == 3:
            return CursesCommands.QUIT
        elif k == ord("p"):
            return CursesCommands.TOGGLE_ACCEL
        elif k == ord("w"):
            return CursesCommands.TOGGLE_VNAV_GUARD
        elif k == ord("l"):
            return CursesCommands.TOGGLE_LNAV_GUARD
        elif k == ord("r"):
            return CursesCommands.UNPAUSE
        elif k == ord("0"):
            return CursesCommands.PAUSE
        elif k == ord("1"):
            return CursesCommands.MAX_SIMRATE_1
        elif k == ord("2"):
            return CursesCommands.MAX_SIMRATE_2
        elif k == ord("3"):
            return CursesCommands.MAX_SIMRATE_4
        elif k == ord("4"):
            return CursesCommands.MAX_SIMRATE_8
        elif k == ord("5"):
            return CursesCommands.MAX_SIMRATE_16
        return CursesCommands.NORMAL
