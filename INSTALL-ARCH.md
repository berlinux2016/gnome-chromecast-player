# Installation Guide for Arch Linux

This guide provides detailed instructions for installing Video Chromecast Player on Arch Linux.

## Quick Install (Recommended)

Run the automated installation script:

```bash
chmod +x install-arch.sh
./install-arch.sh
```

The script will automatically:
- Install all required system dependencies
- Detect your GPU and install appropriate hardware acceleration drivers
- Install Python dependencies
- Create desktop entry
- Install application icon

## Installation Methods

### Method 1: AUR Package (Coming Soon)

Once the package is submitted to AUR, you can install it with any AUR helper:

```bash
# Using yay
yay -S gnome-chromecast-player

# Using paru
paru -S gnome-chromecast-player

# Manual installation from AUR
git clone https://aur.archlinux.org/gnome-chromecast-player.git
cd gnome-chromecast-player
makepkg -si
```

### Method 2: Automated Script

Use the provided installation script:

```bash
./install-arch.sh
```

### Method 3: Manual Installation

#### Step 1: Install System Dependencies

```bash
sudo pacman -Sy
sudo pacman -S --needed \
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
```

#### Step 2: Install Hardware Acceleration

**For AMD GPUs:**
```bash
sudo pacman -S --needed \
    libva-mesa-driver \
    mesa-vdpau \
    libva-utils \
    gstreamer-vaapi
```

**For NVIDIA GPUs:**
```bash
sudo pacman -S --needed \
    libva-nvidia-driver \
    nvidia-utils
```

**For Intel GPUs:**
```bash
sudo pacman -S --needed \
    intel-media-driver \
    libva-intel-driver \
    libva-utils \
    gstreamer-vaapi
```

#### Step 3: Install Additional Codecs

```bash
sudo pacman -S --needed \
    x264 \
    x265 \
    libvpx \
    aom \
    dav1d
```

#### Step 4: Install Python Dependencies

```bash
pip3 install --user -r requirements.txt
```

This installs:
- PyGObject >= 3.42.0
- pychromecast >= 13.0.0
- zeroconf >= 0.132.0

#### Step 5: Make Executable

```bash
chmod +x videoplayer.py
```

#### Step 6: Install Desktop Entry (Optional)

```bash
# Create directories
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/scalable/apps

# Copy icon
cp icon.svg ~/.local/share/icons/hicolor/scalable/apps/video-chromecast-player.svg

# Create desktop file
cat > ~/.local/share/applications/video-chromecast-player.desktop << EOF
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
EOF

# Update databases
update-desktop-database ~/.local/share/applications
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

## Optional: YouTube Support

For YouTube video playback, install yt-dlp:

```bash
sudo pacman -S yt-dlp
```

## Verification

### Test Hardware Acceleration

**AMD/Intel (VA-API):**
```bash
vainfo
```

Expected output should show VA-API drivers and supported profiles.

**NVIDIA:**
```bash
nvidia-smi
ffmpeg -encoders | grep nvenc
```

### Test Application

```bash
./videoplayer.py
```

The application should start and display the main window.

## Troubleshooting

### Missing Dependencies

If you encounter import errors, install missing Python packages:

```bash
pip3 install --user PyGObject pychromecast zeroconf
```

### Hardware Acceleration Not Working

**For AMD/Intel:**
```bash
# Check VA-API
vainfo

# Check GStreamer VA-API plugin
gst-inspect-1.0 vaapi
```

**For NVIDIA:**
```bash
# Check NVIDIA driver
nvidia-smi

# Check NVENC support
ffmpeg -encoders | grep nvenc
```

### Chromecast Not Found

1. Check firewall settings:
   ```bash
   sudo firewall-cmd --list-all
   ```

2. Open required ports:
   ```bash
   sudo firewall-cmd --permanent --add-service=mdns
   sudo firewall-cmd --permanent --add-port=8008-8009/tcp
   sudo firewall-cmd --permanent --add-port=8765-8888/tcp
   sudo firewall-cmd --reload
   ```

3. Or use the provided script:
   ```bash
   ./fix-firewall.sh
   ```

### Desktop Entry Not Showing

Update the desktop database:

```bash
update-desktop-database ~/.local/share/applications
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

## Uninstallation

### If installed via script or manually:

```bash
# Remove application files
rm ~/.local/share/applications/video-chromecast-player.desktop
rm ~/.local/share/icons/hicolor/scalable/apps/video-chromecast-player.svg

# Remove cache and config
rm -rf ~/.cache/gnome-chromecast-player
rm -rf ~/.config/video-chromecast-player

# Update databases
update-desktop-database ~/.local/share/applications
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

### If installed via AUR:

```bash
# Using pacman
sudo pacman -R gnome-chromecast-player

# Using AUR helper
yay -R gnome-chromecast-player
# or
paru -R gnome-chromecast-player
```

## System Requirements

- **OS**: Arch Linux (or Arch-based distributions)
- **Python**: 3.9 or higher
- **GPU**: AMD, NVIDIA, or Intel (for hardware acceleration)
- **Memory**: 512 MB RAM minimum
- **Disk**: 100 MB free space

## Performance

With hardware acceleration enabled:

| Video Quality | CPU Usage | GPU Usage |
|---------------|-----------|-----------|
| 1080p H.264   | 2-5%      | 10-20%    |
| 4K H.264      | 5-10%     | 20-30%    |
| 4K HEVC       | 5-15%     | 25-35%    |

*Values may vary depending on your hardware*

## Getting Help

If you encounter issues:

1. Run the debug script:
   ```bash
   ./debug-chromecast.sh
   ```

2. Check logs:
   ```bash
   ./videoplayer.py 2>&1 | tee videoplayer.log
   ```

3. Open an issue on GitHub:
   https://github.com/berlinux2016/gnome-chromecast-player/issues

## Next Steps

After installation:

1. Read the [README.md](README.md) for usage instructions
2. Check [I18N-GUIDE.md](I18N-GUIDE.md) for language settings
3. Review [AUR-SUBMISSION-GUIDE.md](AUR-SUBMISSION-GUIDE.md) if you want to contribute

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
