"""Input finite state machine and command parser for Vim-like controls."""
from dataclasses import dataclass
from typing import Any, Optional

from vimgarden.enums import GameMode


@dataclass
class Action:
    type: str
    payload: Any = None


MODE_HINTS: dict[GameMode, str] = {
    GameMode.NORMAL: "hl:Pot w:Water f:Fert c:Style x:Prune p:Plant s:Shop i:Inv ::Cmd ?:Help",
    GameMode.SEED_SELECT: "jk:Select Enter:Plant Esc:Back",
    GameMode.SHOP: "jk:Select b:Buy Esc:Back",
    GameMode.INVENTORY: "jk:Scroll Esc:Back",
    GameMode.COMMAND: "Enter:Exec Esc:Cancel",
    GameMode.HELP: "Esc/q:Close",
}


class InputFSM:
    def __init__(self) -> None:
        self.mode: GameMode = GameMode.NORMAL
        self.cmd_buffer: str = ""
        self.selected_index: int = 0

    @property
    def hint(self) -> str:
        return MODE_HINTS.get(self.mode, "")

    def handle_key(self, key: int, context: dict[str, Any]) -> Optional[Action]:
        """Process key according to current mode."""
        if self.mode == GameMode.NORMAL:
            return self._handle_normal(key, context)
        elif self.mode == GameMode.SEED_SELECT:
            return self._handle_seed_select(key, context)
        elif self.mode == GameMode.SHOP:
            return self._handle_shop(key, context)
        elif self.mode == GameMode.INVENTORY:
            return self._handle_inventory(key, context)
        elif self.mode == GameMode.COMMAND:
            return self._handle_command(key)
        elif self.mode == GameMode.HELP:
            return self._handle_help(key)
        return None

    def _handle_normal(self, key: int, context: dict[str, Any]) -> Optional[Action]:
        # Movement & Pot selection
        if key in (ord("h"), 260):  # 'h' or KEY_LEFT
            return Action("MOVE", (-1, 0))
        elif key in (ord("l"), 261):  # 'l' or KEY_RIGHT
            return Action("MOVE", (1, 0))
        elif key in (ord("k"), 259):  # 'k' or KEY_UP
            return Action("MOVE", (0, -1))
        elif key in (ord("j"), 258):  # 'j' or KEY_DOWN
            return Action("MOVE", (0, 1))
        elif ord("1") <= key <= ord("5"):
            return Action("SELECT_POT", key - ord("1"))

        # Actions
        elif key == ord("w"):
            return Action("WATER")
        elif key == ord("f"):
            return Action("FERTILIZE")
        elif key == ord("c"):
            return Action("WIRE_STYLE")
        elif key == ord("p"):
            self.mode = GameMode.SEED_SELECT
            self.selected_index = 0
            return Action("OPEN_SEED_SELECT")

        elif key == ord("x"):
            return Action("HARVEST_OR_CLEAR")
        elif key == ord("s"):
            self.mode = GameMode.SHOP
            self.selected_index = 0
            return Action("OPEN_SHOP")
        elif key == ord("i"):
            self.mode = GameMode.INVENTORY
            self.selected_index = 0
            return Action("OPEN_INVENTORY")
        elif key == ord(":"):
            self.mode = GameMode.COMMAND
            self.cmd_buffer = ""
            return Action("NONE")
        elif key in (ord("?"),):
            self.mode = GameMode.HELP
            return Action("OPEN_HELP")

        return None

    def _handle_seed_select(self, key: int, context: dict[str, Any]) -> Optional[Action]:
        seeds = context.get("available_seeds", [])
        max_idx = max(0, len(seeds) - 1)

        if key in (27, ord("q")):  # Esc or q
            self.mode = GameMode.NORMAL
            return Action("NONE")
        elif key in (ord("k"), 259):
            self.selected_index = max(0, self.selected_index - 1)
            return Action("NONE")
        elif key in (ord("j"), 258):
            self.selected_index = min(max_idx, self.selected_index + 1)
            return Action("NONE")
        elif key in (10, 13, ord(" ")):  # Enter or Space
            if seeds and 0 <= self.selected_index < len(seeds):
                chosen_seed = seeds[self.selected_index]
                self.mode = GameMode.NORMAL
                return Action("PLANT", chosen_seed)
            self.mode = GameMode.NORMAL
            return Action("NONE")

        return None

    def _handle_shop(self, key: int, context: dict[str, Any]) -> Optional[Action]:
        items = context.get("shop_items", [])
        max_idx = max(0, len(items) - 1)

        if key in (27, ord("q"), ord("s")):
            self.mode = GameMode.NORMAL
            return Action("NONE")
        elif key in (ord("k"), 259):
            self.selected_index = max(0, self.selected_index - 1)
            return Action("NONE")
        elif key in (ord("j"), 258):
            self.selected_index = min(max_idx, self.selected_index + 1)
            return Action("NONE")
        elif key in (ord("b"), 10, 13):  # 'b' or Enter to buy
            if items and 0 <= self.selected_index < len(items):
                return Action("BUY", items[self.selected_index])
            return Action("NONE")

        return None

    def _handle_inventory(self, key: int, context: dict[str, Any]) -> Optional[Action]:
        items = context.get("inventory_items", [])
        max_idx = max(0, len(items) - 1)

        if key in (27, ord("q"), 10, 13, ord(" "), ord("i")):
            self.mode = GameMode.NORMAL
            return Action("NONE")
        elif key in (ord("k"), 259):
            self.selected_index = max(0, self.selected_index - 1)
            return Action("NONE")
        elif key in (ord("j"), 258):
            self.selected_index = min(max_idx, self.selected_index + 1)
            return Action("NONE")

        return None

    def _handle_command(self, key: int) -> Optional[Action]:
        if key == 27:  # Esc
            self.mode = GameMode.NORMAL
            self.cmd_buffer = ""
            return Action("NONE")
        elif key in (10, 13):  # Enter
            cmd = self.cmd_buffer.strip()
            self.mode = GameMode.NORMAL
            self.cmd_buffer = ""
            return self._parse_command(cmd)
        elif key in (127, 8, 263):  # Backspace
            if self.cmd_buffer:
                self.cmd_buffer = self.cmd_buffer[:-1]
            return Action("NONE")
        elif 32 <= key <= 126:  # Printable ASCII
            self.cmd_buffer += chr(key)
            return Action("NONE")

        return None

    def _parse_command(self, cmd: str) -> Action:
        if cmd in ("w", "w!"):
            return Action("SAVE")
        elif cmd in ("q", "quit"):
            return Action("QUIT", False)
        elif cmd in ("q!", "quit!"):
            return Action("QUIT", True)
        elif cmd in ("wq", "wq!", "x", "x!"):
            return Action("SAVE_AND_QUIT")
        elif cmd in ("h", "help"):
            self.mode = GameMode.HELP
            return Action("OPEN_HELP")
        else:
            return Action("UNKNOWN_CMD", cmd)

    def _handle_help(self, key: int) -> Optional[Action]:
        if key in (27, ord("q"), 10, 13, ord(" "), ord("?")):
            self.mode = GameMode.NORMAL
            return Action("NONE")
        return None
