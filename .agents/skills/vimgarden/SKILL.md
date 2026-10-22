---
name: vimgarden
description: >-
  Comprehensive guide and runbook for developing, testing, maintaining, and extending
  the vimgarden terminal bonsai simulation game. Use when working on game mechanics,
  simulation engine, curses UI, plant species/ASCII art, input FSM, storage, or tests.
---

# Vimgarden Development & Architecture Guide

`vimgarden` is a terminal-based Zen Bonsai simulation written in Python using `curses` with Vim-like navigation and modal controls.

---

## 1. Quick Commands

### Run the Game
```bash
python3 -m vimgarden
```
*Note: Minimum terminal size is 80 columns x 24 lines.*

### Run Tests
```bash
python3 -m unittest discover tests
```
Run an individual test file:
```bash
python3 -m unittest tests/test_simulation.py
```

---

## 2. Codebase Architecture

```text
vimgarden/
├── __main__.py          # Entry point, game loop, input handling, curses lifecycle
├── config.py            # Global constants (dimensions, tick interval, paths)
├── enums.py             # GameMode, GrowthStage, HealthState
├── models.py            # Dataclasses: PlantType, Plant, Plot, GameState
├── simulation.py        # Growth, thirst, offline catchup, watering, pruning
├── input_fsm.py         # Modal input FSM and key mappings
├── storage.py           # Atomic JSON persistence and backup recovery
├── data/
│   ├── plants_data.py   # Bonsai species definitions and balancing
│   └── ascii_art.py     # 29x13 ASCII art frames for all stages and health states
└── ui/
    ├── layout.py        # Screen centering and layout calculations
    ├── components.py    # Modals, pot rendering, header, footer
    └── renderer.py      # Main curses renderer coordinator
```

---

## 3. Adding New Bonsai Species

To introduce a new bonsai tree species:

### 1. Register in `vimgarden/data/plants_data.py`
Add a new `PlantType` entry to `PLANTS`:
```python
"cedar": PlantType(
    id="cedar",
    name="Cedar Bonsai",
    seed_price=70,
    sell_price=130,
    growth_duration=240.0,    # Total seconds to reach MATURE
    thirst_threshold=70.0,    # Seconds until THIRSTY
    wilt_threshold=210.0,     # Seconds until WILTING
    death_threshold=420.0,    # Seconds until DEAD
),
```

### 2. Add ASCII Art in `vimgarden/data/ascii_art.py`
Every art matrix must be **strictly 29 columns wide** and **13 lines high** (10 plant lines + 3 lines of `POT_BASE`):
```python
CEDAR_ART: dict[GrowthStage, dict[HealthState, list[str]]] = {
    GrowthStage.SEED: {
        HealthState.HEALTHY: _pad_art([...]),  # 10 lines + POT_BASE
        HealthState.THIRSTY: _pad_art([...]),
        HealthState.WILTING: _pad_art([...]),
        HealthState.DEAD: _pad_art([...]),
    },
    # Define for SPROUT, ADULT, MATURE stages...
}

# Register in global dict:
PLANT_ARTS["cedar"] = CEDAR_ART
```
Always wrap art line arrays in `_pad_art()` to guarantee 29 characters width padding.

---

## 4. Simulation Engine & Growth Mechanics

All simulation calculations in `simulation.py` are strictly time-delta based:

- **Growth Rates**:
  - `HEALTHY`: 1.0x growth speed.
  - `THIRSTY`: 0.25x growth speed.
  - `WILTING` / `DEAD`: 0.0x growth speed.
  - `FERTILIZER`: +50% speed boost while `fertilized_remaining_seconds > 0`.
  - `SEASONAL AFFINITY`:
    - Spring: Sakura +35% growth speed.
    - Summer: Juniper +20% growth speed.
    - Autumn: Maple +25% growth speed, +35% Zen Coins on pruning.
    - Winter: Black Pine +20% growth speed.
- **Dynamic Weather**:
  - `Rainy`: Automatically waters all living bonsai trees on the Tokonoma shelf.
- **Stage Progression**:
  - `SEED`: `0%` to `< 25%` of `growth_duration`.
  - `SPROUT`: `25%` to `< 70%` of `growth_duration`.
  - `ADULT`: `70%` to `< 100%` of `growth_duration`.
  - `MATURE`: `100%` of `growth_duration` (can be pruned).
- **Pruning (`prune_bonsai`)**:
  - Pruning a `MATURE` plant awards `sell_price` Zen coins.
  - Multiplied by tree age (+10% per game year up to +100% max).
  - Multiplied by bonsai style (Cascade/Kengai +25%, Formal/Chokkan +15%).
  - Multiplied by seasonal and decor buffs (Autumn Maple +35%, Toro Lantern +20%).
  - Rolls growth progress back to `0.70 * growth_duration` (`ADULT` stage), allowing repeat blooming.
- **Tree Age & Bonsai Styles**:
  - Trees age over time (1 game year = 360 seconds). Age is displayed on the pot badge.
  - Copper Wire tool in shop allows shaping trees (`c` key) into Formal Upright (`CHOKKAN`), Informal Upright (`MOYOGI`), and Cascade (`KENGAI`).
- **Multi-Pot Tokonoma Shelf**:

  - Starts with 3 pots (`DEFAULT_UNLOCKED_POTS`), expandable up to 5 (`MAX_POTS`) via shop purchase.
  - Navigate between pots with `h` / `l` or number keys `1` .. `5`.

- **Offline Catch-Up**:
  - Capped at `MAX_OFFLINE_SECONDS` (7 days).
  - If a plant would die during offline catch-up, `WILT_GRACE_BUFFER_SECONDS` (1 hour) holds it at `WILTING` instead of killing it immediately.

---

## 5. Input Finite State Machine (FSM)

Located in `vimgarden/input_fsm.py`:

- **Modes (`GameMode`)**:
  - `NORMAL`: Navigation (`h/l` or `1`-`5` to switch active pot), action keys (`w`: water, `f`: fertilize, `c`: wire/style, `p`: plant, `x`: prune/clear, `s`: shop, `i`: inventory, `:`: command, `?`: help).

  - `SEED_SELECT`: Seed selection modal (`j/k` or arrows to pick, `Enter` to plant, `Esc/q` to exit).
  - `SHOP`: Buying saplings, extra pots, fertilizer, and Zen decor (`b` to purchase).
  - `INVENTORY`: Viewing current sapling and supply counts.
  - `COMMAND`: Vim commands (`:w` save, `:q` quit, `:q!` force quit, `:wq` / `:x` save & quit).
  - `HELP`: Help overlay.


When adding a new keybind or mode:
1. Define the action in `InputFSM.handle_key()`.
2. Add corresponding action execution in `__main__.py`'s action dispatcher.
3. Update `MODE_HINTS` in `input_fsm.py` to reflect keys in the status line.

---

## 6. Curses UI & Rendering

Located in `vimgarden/ui/`:

- **Minimum Dimensions**: 80 columns x 24 lines (`MIN_COLS`, `MIN_LINES`). If smaller, a friendly resize notification is shown.
- **Color Pairs**:
  - `1`: Green (`COLOR_GREEN`) — Healthy plants, success messages.
  - `2`: Yellow (`COLOR_YELLOW`) — Thirsty plants, warnings, highlights.
  - `3`: Red (`COLOR_RED`) — Wilting/dead plants, errors.
  - `4`: Cyan (`COLOR_CYAN`) — Mature flowers, borders, UI headers.
  - `5`: Magenta (`COLOR_MAGENTA`) — Sakura blossoms, special accents.
  - `6`: White (`COLOR_WHITE`) — Regular text, pot outlines.
- **Atomic Refresh**: Use `noutrefresh()` during sub-component drawing, followed by a single `curses.doupdate()` at the end of the frame.

---

## 7. Storage & Migrations

Located in `vimgarden/storage.py`:

- **File Locations**:
  - Save: `~/.local/share/vimgarden/save.json`
  - Backup: `~/.local/share/vimgarden/save.json.bak`
- **Atomic Writes**: Writes to `save.json.tmp` first, flushes and syncs to disk, then atomically renames to `save.json`.
- **Corrupted Save Recovery**: If loading `save.json` fails, `storage.py` automatically falls back to `save.json.bak` and preserves the broken file as `save.json.corrupt`.
- **Backward Compatibility**: `dict_to_state()` handles legacy data (e.g. migrating vegetable IDs like `carrot` to bonsai IDs like `juniper`).

---

## 8. Testing Guidelines

Test files are located in `tests/`:
- `test_simulation.py`: Tests for growth ticks, health state transitions, offline catch-up, and pruning.
- `test_input_fsm.py`: Tests for modal transitions, key handling, and command line parsing.
- `test_storage.py`: Tests for atomic saving, corrupted file recovery, and serialization.
- `test_ui.py`: Tests for layout calculations and component helpers without opening real terminal windows.

Always run `python3 -m unittest discover tests` after modifying simulation or storage logic.

---

## 9. Language & Communication Standards

- **Strict English Requirement**: All code, docstrings, identifiers, comments, user-facing UI labels, status messages, CLI tools, scripts (`install.sh`), git commit messages, and documentation (`README.md`, specs) must be strictly written in **English**. Do not use Russian or any non-English text inside repository files or user-facing terminal outputs.

---

## 10. Versioning & Git Release Conventions

- **Semantic Versioning (`vX.Y.Z`)**: Follow semver conventions:
  - `v0.1.0`: Initial baseline release.
  - `v0.2.0`: Tokonoma multi-pot shelf, seasons, weather, tools, organic ASCII art.
- **Syncing Version Strings**:
  - Keep `pyproject.toml` (`version = "X.Y.Z"`) and `vimgarden/__init__.py` (`__version__ = "X.Y.Z"`) synchronized.
- **Dynamic Git Hash**:
  - The runtime helper `get_version_string()` in `vimgarden/__init__.py` dynamically appends the short git commit hash (e.g. `v0.2.0 (a7e8221)`) in the header and `--version` CLI output.
- **Git Tags**:
  - For milestone releases, tag the commit: `git tag -a vX.Y.Z -m "Release vX.Y.Z"` and push with `git push origin vX.Y.Z`.


