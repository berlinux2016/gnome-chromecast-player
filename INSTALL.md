# Installation Guide - GNOME Chromecast Player

This guide explains the different installation methods for GNOME Chromecast Player.

## Quick Start

### Method 1: RPM Package (Recommended for Fedora/RHEL)

Build and install the RPM package:

```bash
./build-rpm.sh
sudo dnf install ~/rpmbuild/RPMS/noarch/gnome-chromecast-player-2.0.0-1.*.rpm
```

### Method 2: Local Installation (User-only)

Install to `~/.local` without root privileges:

```bash
./install-local.sh install
```

Make sure `~/.local/bin` is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add this line to your `~/.bashrc` or `~/.zshrc` to make it permanent.

### Method 3: System-wide Installation (Makefile)

Install system-wide using make:

```bash
sudo make install
```

Or install to a custom location:

```bash
sudo make install PREFIX=/opt/gnome-chromecast-player
```

## Detailed Installation Methods

### RPM Package Installation

#### Prerequisites

Install build dependencies:

```bash
sudo dnf install rpm-build rpmdevtools desktop-file-utils libappstream-glib
```

#### Build Process

1. **Build the RPM package:**

   ```bash
   ./build-rpm.sh
   ```

   This script will:
   - Check for build dependencies
   - Setup RPM build environment
   - Create source tarball
   - Build the RPM package

2. **Install the RPM:**

   ```bash
   sudo dnf install ~/rpmbuild/RPMS/noarch/gnome-chromecast-player-2.0.0-1.*.rpm
   ```

3. **Uninstall:**

   ```bash
   sudo dnf remove gnome-chromecast-player
   ```

#### Advantages
- Clean package management
- Automatic dependency resolution
- Easy updates and removal
- System-wide installation
- Desktop integration

### Local Installation

#### Install to ~/.local

```bash
./install-local.sh install
```

#### Uninstall from ~/.local

```bash
./install-local.sh uninstall
```

#### Advantages
- No root privileges required
- User-specific installation
- Easy to test and develop
- Won't affect system packages

#### Note
Make sure `~/.local/bin` is in your PATH. Add this to `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Makefile Installation

#### System-wide Installation

```bash
sudo make install
```

This installs to `/usr/local` by default.

#### Custom Installation Prefix

Install to a custom directory:

```bash
sudo make install PREFIX=/opt/custom
```

#### Uninstall

```bash
sudo make uninstall
```

#### Check Dependencies

```bash
make check
```

This shows which dependencies are installed and which are missing.

## Runtime Dependencies

The application requires the following packages:

### Core Requirements
- `python3` (≥ 3.9)
- `gtk4`
- `libadwaita`
- `python3-gobject`

### GStreamer
- `gstreamer1`
- `gstreamer1-plugins-base`
- `gstreamer1-plugins-good`
- `gstreamer1-plugins-bad-free`
- `gstreamer1-plugins-ugly-free`

### Hardware Acceleration
- `gstreamer1-vaapi` (for AMD/Intel GPUs)
- `gstreamer1-plugins-bad-freeworld` (for NVIDIA NVDEC, optional)

### Chromecast & Streaming
- `python3-pychromecast`
- `python3-requests`
- `yt-dlp`
- `ffmpeg`

### Install All Dependencies (Fedora)

```bash
sudo dnf install python3 gtk4 libadwaita python3-gobject \
    gstreamer1 gstreamer1-plugins-base gstreamer1-plugins-good \
    gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free \
    gstreamer1-vaapi python3-pychromecast python3-requests \
    yt-dlp ffmpeg
```

### Optional: NVIDIA Support

For NVIDIA hardware acceleration (from RPM Fusion):

```bash
sudo dnf install gstreamer1-plugins-bad-freeworld
```

## Running the Application

After installation, you can run the application by:

1. **From application menu:**
   - Search for "GNOME Chromecast Player" in your application launcher

2. **From command line:**
   ```bash
   gnome-chromecast-player
   ```

3. **Open a video file directly:**
   ```bash
   gnome-chromecast-player /path/to/video.mp4
   ```

## Troubleshooting

### Command not found

If you get "command not found" after local installation:

1. Check if `~/.local/bin` is in your PATH:
   ```bash
   echo $PATH | grep .local/bin
   ```

2. If not, add it to your `~/.bashrc`:
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Desktop entry not showing

1. Update desktop database:
   ```bash
   update-desktop-database ~/.local/share/applications
   ```

2. If icon is missing, update icon cache:
   ```bash
   gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
   ```

### Missing dependencies

Run this to check which dependencies are missing:

```bash
make check
```

## Uninstallation

### RPM Package

```bash
sudo dnf remove gnome-chromecast-player
```

### Local Installation

```bash
./install-local.sh uninstall
```

Or manually:

```bash
rm -rf ~/.local/share/gnome-chromecast-player
rm -f ~/.local/bin/gnome-chromecast-player
rm -f ~/.local/share/applications/gnome-chromecast-player.desktop
```

### Makefile Installation

```bash
sudo make uninstall
```

### Remove Configuration Files

Configuration files are stored in `~/.config/video-chromecast-player`:

```bash
rm -rf ~/.config/video-chromecast-player
```

## Building from Source (Developers)

### Clone or Extract Source

```bash
cd /path/to/gnome-chromecast-player
```

### Test Without Installing

Run directly from source:

```bash
python3 videoplayer.py
```

### Build RPM from Source

```bash
./build-rpm.sh
```

### Create Source Tarball

```bash
make -C ~/rpmbuild/SOURCES gnome-chromecast-player-2.0.0.tar.gz
```

## Support

For issues and bug reports, please visit:
https://github.com/berlinux2016/gnome-chromecast-player/issues
