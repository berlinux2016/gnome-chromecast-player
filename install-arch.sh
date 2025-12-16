#!/bin/bash
# Installation script for Video Chromecast Player on Arch Linux
# Installationsskript für Video Chromecast Player auf Arch Linux

echo "=== Video Chromecast Player Installation (Arch Linux) ==="
echo ""

# Check if running on Arch Linux
if [ ! -f /etc/arch-release ]; then
    echo "Warning: This script is optimized for Arch Linux."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update package database
echo "Updating package database..."
sudo pacman -Sy

# Install system dependencies
echo ""
echo "Installing system dependencies..."
sudo pacman -S --needed --noconfirm \
    python \
    python-pip \
    python-gobject \
    gtk4 \
    libadwaita \
    gstreamer \
    gst-plugins-base \
    gst-plugins-good \
    gst-plugins-bad \
    gst-plugins-ugly \
    gst-libav \
    ffmpeg

# Hardware acceleration detection and installation
echo ""
echo "Installing hardware acceleration support..."

# Check GPU type
if command -v nvidia-smi &>/dev/null && nvidia-smi -L | grep -q "GPU"; then
    echo "NVIDIA GPU detected - installing NVDEC/NVENC support..."
    sudo pacman -S --needed --noconfirm \
        libva-nvidia-driver \
        nvidia-utils
    echo "Note: Make sure NVIDIA proprietary drivers are installed!"
elif lspci | grep -i 'vga\|3d' | grep -qi 'amd\|radeon'; then
    echo "AMD GPU detected - installing VA-API support..."
    sudo pacman -S --needed --noconfirm \
        libva-mesa-driver \
        mesa-vdpau \
        libva-utils \
        gstreamer-vaapi
elif lspci | grep -i 'vga\|3d' | grep -qi 'intel'; then
    echo "Intel GPU detected - installing VA-API support..."
    sudo pacman -S --needed --noconfirm \
        intel-media-driver \
        libva-intel-driver \
        libva-utils \
        gstreamer-vaapi
else
    echo "No specific GPU detected - installing generic drivers..."
    sudo pacman -S --needed --noconfirm \
        libva \
        libva-utils \
        gstreamer-vaapi
fi

# Additional codec support
echo ""
echo "Installing additional codec support..."
sudo pacman -S --needed --noconfirm \
    x264 \
    x265 \
    libvpx \
    aom \
    dav1d

# Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Make executable
chmod +x videoplayer.py

# Install icon
echo ""
echo "Installing application icon..."
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR"
if [ -f "icon.svg" ]; then
    cp icon.svg "$ICON_DIR/video-chromecast-player.svg"
elif [ -f "gnome-chromecast-player.svg" ]; then
    cp gnome-chromecast-player.svg "$ICON_DIR/video-chromecast-player.svg"
fi

# Create desktop entry
echo "Creating desktop shortcut..."
DESKTOP_FILE="$HOME/.local/share/applications/video-chromecast-player.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Video Chromecast Player
Name[de]=Video Chromecast Player
Comment=Video player with Chromecast support and hardware acceleration
Comment[de]=Videoplayer mit Chromecast-Unterstützung und Hardware-Beschleunigung
Exec=$(pwd)/videoplayer.py
Icon=video-chromecast-player
Terminal=false
Categories=AudioVideo;Video;Player;GTK;GNOME;
Keywords=video;player;chromecast;cast;streaming;
StartupNotify=true
StartupWMClass=video-chromecast-player
EOL

# Update desktop database and icon cache
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# Test hardware acceleration
echo ""
echo "Testing hardware acceleration..."

if command -v nvidia-smi &>/dev/null && nvidia-smi -L | grep -q "GPU"; then
    echo ""
    echo "NVIDIA GPU Status:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null
    echo ""
    echo "NVDEC Status:"
    ffmpeg -hide_banner -encoders 2>&1 | grep -i nvenc | head -n 3 || echo "NVENC not available"
    echo ""
elif command -v vainfo &>/dev/null; then
    echo ""
    echo "VA-API Status:"
    vainfo 2>/dev/null | grep -E "Driver|VAProfile" | head -n 10
    echo ""
else
    echo "Hardware acceleration tools not found."
fi

echo ""
echo "=== Installation completed! ==="
echo ""

# GPU-specific hints
if command -v nvidia-smi &>/dev/null && nvidia-smi -L | grep -q "GPU"; then
    echo "Your NVIDIA graphics card is now configured for hardware acceleration."
    echo "Hardware acceleration: NVDEC (decoding) + NVENC (encoding)"
    echo ""
    echo "To verify hardware acceleration:"
    echo "  nvidia-smi"
    echo "  ffmpeg -encoders | grep nvenc"
elif lspci | grep -i 'vga\|3d' | grep -qi 'amd\|radeon'; then
    echo "Your AMD graphics card is now configured for hardware acceleration."
    echo "Hardware acceleration: VA-API (decoding + encoding)"
    echo ""
    echo "To verify hardware acceleration:"
    echo "  vainfo"
elif lspci | grep -i 'vga\|3d' | grep -qi 'intel'; then
    echo "Your Intel graphics card is now configured for hardware acceleration."
    echo "Hardware acceleration: VA-API (decoding + encoding)"
    echo ""
    echo "To verify hardware acceleration:"
    echo "  vainfo"
else
    echo "Generic hardware acceleration has been set up."
fi

echo ""
echo "You can now start the player with:"
echo "  ./videoplayer.py"
echo ""
echo "Or search for 'Video Chromecast Player' in your applications."
echo ""
echo "Notes:"
echo "- Hardware acceleration is enabled (automatic GPU detection)"
echo "- All common video codecs are installed (H.264, H.265, VP9, AV1, etc.)"
echo "- Make sure Chromecast and computer are on the same network"
echo ""

# Optional: Install yt-dlp for YouTube support
if ! command -v yt-dlp &>/dev/null; then
    echo "Optional: Install yt-dlp for YouTube video support?"
    read -p "Install yt-dlp? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo pacman -S --needed --noconfirm yt-dlp
        echo "yt-dlp installed successfully!"
    fi
fi
