#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
TARGET="$BIN_DIR/vimgarden"

# Handle uninstallation
if [[ "${1:-}" == "--uninstall" || "${1:-}" == "-u" ]]; then
    if [[ -f "$TARGET" ]]; then
        rm -f "$TARGET"
        echo "✅ vimgarden successfully removed from $BIN_DIR"
    else
        echo "ℹ️  File $TARGET not found."
    fi
    exit 0
fi

# Ensure ~/.local/bin exists
mkdir -p "$BIN_DIR"

# Create lightweight launcher
cat <<EOF > "$TARGET"
#!/usr/bin/env bash
PYTHONPATH="$REPO_DIR:\${PYTHONPATH:-}" exec python3 -m vimgarden "\$@"
EOF

chmod +x "$TARGET"
echo "✅ vimgarden successfully installed to $TARGET"

# Check PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* && ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "⚠️  Warning: $BIN_DIR is not found in your PATH!"
    echo "To run vimgarden from any terminal, add it to your shell configuration:"
    echo ""
    case "${SHELL:-}" in
        */zsh)
            echo '  echo '\''export PATH="$HOME/.local/bin:$PATH"'\'' >> ~/.zshrc'
            echo "  source ~/.zshrc"
            ;;
        */fish)
            echo "  fish_add_path ~/.local/bin"
            ;;
        *)
            echo '  echo '\''export PATH="$HOME/.local/bin:$PATH"'\'' >> ~/.bashrc'
            echo "  source ~/.bashrc"
            ;;
    esac
    echo ""
else
    echo "🚀 $BIN_DIR is already in your PATH. Run: vimgarden"
fi
