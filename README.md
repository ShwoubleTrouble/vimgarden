# vimgarden

[![Release](https://img.shields.io/github/v/tag/ShwoubleTrouble/vimgarden?label=release&color=007ec6)](https://github.com/ShwoubleTrouble/vimgarden/releases)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)]()
[![Dependencies](https://img.shields.io/badge/dependencies-0%20(pure%20stdlib)-success.svg)]()

> Cultivate ancient bonsai trees in your terminal. Modal Vim controls, real-time seasons, organic ASCII art, and zero external dependencies.

## Features

- **Tokonoma Shelf**: Cultivate a collection of 3 to 5 bonsai trees simultaneously, navigating with `h`/`l` or `1`-`5`.
- **Dynamic Seasons & Weather**: Experience Spring 🌸, Summer ☀️, Autumn 🍁, and Winter ❄️ with rain auto-watering and seasonal growth synergies.
- **Tree Age & Bonsai Styling**: Trees age in real-world time (`h`, `d`, `mo`, `y`), gaining value. Shape branches using Copper Wire (`c`) into Formal (`Chokkan`), Informal (`Moyogi`), or Cascade (`Kengai`) styles.
- **Organic ASCII Art**: Detailed layered canopies (Dan-zukuri), driftwood trunks, drifting sakura petals, and ceramic pot pottery.
- **Vim Modal Navigation**:
  - `NORMAL`: `h`/`l` pot select, `w` water, `f` fertilize, `c` wire/style, `x` prune/harvest, `p` plant, `s` shop, `i` inventory, `?` guide.
  - `COMMAND`: `:w` save, `:q` quit, `:wq` / `:x` save & quit, `:q!` force quit.
- **Zero Dependencies**: Pure Python standard library (`curses`). No pip packages required.
- **Safe Persistence**: Atomic JSON saves with automatic backup copy and corruption recovery.


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
