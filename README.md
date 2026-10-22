# vimgarden

A terminal-based Zen Bonsai simulation game written in Python using `curses` with Vim-like navigation and modal controls.

## Features

- **Zen Bonsai Simulation**: Plant, water, and prune bonsai trees (Juniper, Sakura, Maple, Pine).
- **Time-Delta Growth**: Real-time growth calculation with offline progress catch-up.
- **Vim-Inspired Modal Controls**:
  - `NORMAL`: `h`/`j`/`k`/`l` movement, `w` to water, `x` to prune/harvest, `p` to plant, `s` for shop, `i` for inventory, `?` for help.
  - `COMMAND`: `:w` (save), `:q` (quit), `:wq` / `:x` (save and quit), `:q!` (force quit).
- **ASCII Art**: Large multi-stage ASCII art for every growth stage and health state.
- **Safe Persistence**: Atomic JSON saving with backup and auto-recovery.

## Requirements

- Python >= 3.10
- Terminal window of at least 80x24 characters

## Installation

```bash
git clone https://github.com/ShwoubleTrouble/vimgarden.git
cd vimgarden

# Lightweight install to ~/.local/bin/ (no pip/venv overhead):
./install.sh

# Or uninstall:
./install.sh --uninstall
```

## Running

```bash
# Via console script:
vimgarden

# Or directly as module:
python3 -m vimgarden
```

## Running Tests

```bash
python3 -m unittest discover tests
```

## License

[GPL-3.0](LICENSE)
