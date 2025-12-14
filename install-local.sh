#!/bin/bash
#
# Local Installation Script for GNOME Chromecast Player
# This script installs the application locally without building an RPM
# Useful for development and testing
#

set -e  # Exit on error

APP_NAME="gnome-chromecast-player"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

install_app() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Installing GNOME Chromecast Player (Local)      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Create directories
    print_info "Creating directories..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICON_DIR"

    # Install main application
    print_info "Installing application files..."
    cp videoplayer.py "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/videoplayer.py"

    # Create wrapper script
    print_info "Creating launcher script..."
    cat > "$BIN_DIR/$APP_NAME" << EOF
#!/bin/bash
exec python3 "$INSTALL_DIR/videoplayer.py" "\$@"
EOF
    chmod +x "$BIN_DIR/$APP_NAME"

    # Install desktop file
    print_info "Installing desktop entry..."
    cp ${APP_NAME}.desktop "$DESKTOP_DIR/"

    # Update desktop database
    if command -v update-desktop-database &>/dev/null; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi

    # Install icon if exists
    if [ -f "${APP_NAME}.svg" ]; then
        print_info "Installing icon..."
        cp ${APP_NAME}.svg "$ICON_DIR/"

        # Update icon cache
        if command -v gtk-update-icon-cache &>/dev/null; then
            gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
        fi
    else
        print_warning "Icon file not found - skipping icon installation"
    fi

    echo ""
    print_success "Installation complete!"
    echo ""
    print_info "The application is now available as: $APP_NAME"
    print_info "Make sure $BIN_DIR is in your PATH"
    echo ""

    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        print_warning "$BIN_DIR is not in your PATH"
        echo ""
        echo "Add this line to your ~/.bashrc or ~/.zshrc:"
        echo -e "${BLUE}  export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        echo ""
    fi
}

uninstall_app() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Uninstalling GNOME Chromecast Player (Local)    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""

    print_info "Removing application files..."

    # Remove files
    rm -rf "$INSTALL_DIR"
    rm -f "$BIN_DIR/$APP_NAME"
    rm -f "$DESKTOP_DIR/${APP_NAME}.desktop"
    rm -f "$ICON_DIR/${APP_NAME}.svg"

    # Update desktop database
    if command -v update-desktop-database &>/dev/null; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi

    # Update icon cache
    if command -v gtk-update-icon-cache &>/dev/null; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi

    echo ""
    print_success "Uninstallation complete!"
    echo ""
    print_info "Configuration files remain in ~/.config/video-chromecast-player"
    print_info "To remove them, run: rm -rf ~/.config/video-chromecast-player"
    echo ""
}

# Main
case "${1:-install}" in
    install)
        cd "$(dirname "$0")"
        install_app
        ;;
    uninstall)
        uninstall_app
        ;;
    *)
        echo "Usage: $0 [install|uninstall]"
        exit 1
        ;;
esac
