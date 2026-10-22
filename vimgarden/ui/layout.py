"""Terminal layout calculation for single central Bonsai pot."""
from dataclasses import dataclass

from vimgarden.config import MIN_COLS, MIN_LINES


@dataclass
class LayoutInfo:
    is_valid_size: bool
    screen_h: int
    screen_w: int
    pot_start_y: int
    pot_start_x: int
    pot_w: int
    pot_h: int


def calculate_layout(screen_h: int, screen_w: int) -> LayoutInfo:
    """Calculate positioning for single central bonsai pot."""
    if screen_h < MIN_LINES or screen_w < MIN_COLS:
        return LayoutInfo(
            is_valid_size=False,
            screen_h=screen_h,
            screen_w=screen_w,
            pot_start_y=0,
            pot_start_x=0,
            pot_w=31,
            pot_h=15,
        )

    pot_w = 31
    pot_h = 15
    total_component_h = pot_h + 2  # 15 lines box + 2 lines status labels

    # Center between line 2 (under header) and line screen_h - 2 (above footer)
    available_h = (screen_h - 2) - 2
    pot_start_y = 2 + max(0, (available_h - total_component_h) // 2)
    pot_start_x = max(0, (screen_w - pot_w) // 2)

    return LayoutInfo(
        is_valid_size=True,
        screen_h=screen_h,
        screen_w=screen_w,
        pot_start_y=pot_start_y,
        pot_start_x=pot_start_x,
        pot_w=pot_w,
        pot_h=pot_h,
    )
