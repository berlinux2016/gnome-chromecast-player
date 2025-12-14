# GNOME Chromecast Player v2.0.0 🎉

**Release Date:** December 14, 2025

A major feature release with new productivity features, keyboard shortcuts, and critical bug fixes!

## ✨ New Features

### 📁 Recent Files
- **Automatic history tracking** of the last 10 opened videos
- **Quick access** via clock icon in header bar
- **One-click reopening** of recently watched videos
- **Clear history** option in menu
- Persistent storage in `~/.config/video-chromecast-player/recent_files.json`

### ⚡ Playback Speed Shortcuts
- **`[` key** - Decrease playback speed
- **`]` key** - Increase playback speed
- **10 speed levels** from 0.25x to 3.0x
- **Visual feedback** with status label
- Perfect for learning videos and tutorials

### 🎬 Frame-by-Frame Navigation
- **`,` key** - Step one frame backward
- **`.` key** - Step one frame forward
- **Precision navigation** at 25 FPS (0.04s per frame)
- **Auto-pause** for detailed video analysis
- Ideal for screenshots and precise editing

### ⌨️ Shortcuts Help Dialog
- **`H` key** - Display comprehensive keyboard shortcuts overview
- **6 categories** organized by function:
  - Wiedergabe (Playback)
  - Lautstärke & Audio (Volume & Audio)
  - Ansicht (View)
  - A-B Loop & Export
  - Navigation
  - Hilfe (Help)
- **Scrollable list** with clear descriptions
- **Professional design** with monospace fonts for key labels

## 🐛 Critical Bug Fixes

### Play/Pause Button Handler Issues
- **Fixed crash** when switching between Chromecast and local playback
- **Replaced unsafe `disconnect_by_func()`** with handler ID tracking
- **Eliminated memory leaks** from signal handlers
- **Consistent button state** across all playback scenarios
- **Improved mode switching** (Local ↔ Chromecast)

### Chromecast Streaming Improvements
- **Better error handling** during streaming initialization
- **Reliable button states** when starting/stopping Chromecast
- **Fixed position tracking** when switching modes
- **Improved pipeline ready detection** before seeking

## 📦 Installation

### Quick Install (Fedora/RHEL)

Download and extract the source:
```bash
wget https://github.com/berlinux2016/gnome-chromecast-player/releases/download/v2.0.0/gnome-chromecast-player-2.0.0.tar.gz
tar -xzf gnome-chromecast-player-2.0.0.tar.gz
cd gnome-chromecast-player-2.0.0
```

#### Option 1: Build RPM Package (Recommended)
```bash
./build-rpm.sh
sudo dnf install ~/rpmbuild/RPMS/noarch/gnome-chromecast-player-2.0.0-1.*.rpm
```

#### Option 2: Local Installation (No root required)
```bash
./install-local.sh install
```

#### Option 3: System-wide Installation
```bash
sudo make install
```

See [INSTALL.md](INSTALL.md) for detailed instructions.

## 🔧 Requirements

### Core
- Python 3.9+
- GTK4 + Libadwaita
- GStreamer 1.x with plugins

### Streaming
- pychromecast (for Chromecast support)
- yt-dlp (for YouTube streaming)
- ffmpeg (for video conversion)

### Hardware Acceleration
- **AMD/Intel GPUs:** gstreamer1-vaapi
- **NVIDIA GPUs:** gstreamer1-plugins-bad-freeworld (optional)

Install all dependencies on Fedora:
```bash
sudo dnf install python3 gtk4 libadwaita python3-gobject \
    gstreamer1 gstreamer1-plugins-{base,good,bad-free,ugly-free} \
    gstreamer1-vaapi python3-pychromecast python3-requests yt-dlp ffmpeg
```

## 📖 Documentation

- **[README.md](README.md)** - Complete feature overview and usage guide
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions
- **[BUILD-SYSTEM.md](BUILD-SYSTEM.md)** - Build system documentation for developers

## 🎯 Key Features (Overview)

- ✅ **Chromecast Streaming** with automatic format conversion
- ✅ **Hardware Acceleration** (VA-API, NVDEC)
- ✅ **YouTube Video Streaming** via URL
- ✅ **Playlist Support** with thumbnails and auto-advance
- ✅ **Recent Files** history (NEW in 2.0.0)
- ✅ **Frame-by-Frame Navigation** (NEW in 2.0.0)
- ✅ **Playback Speed Shortcuts** (NEW in 2.0.0)
- ✅ **Keyboard Shortcuts Help** (NEW in 2.0.0)
- ✅ **A-B Loop** for learning and practice
- ✅ **Video Effects** and Equalizer
- ✅ **Subtitle Support** (SRT, ASS, VTT)
- ✅ **Timeline Thumbnails** with live scrubbing
- ✅ **Bookmark/Resume** functionality
- ✅ **Screenshot Capture**

## 🔗 Links

- **Homepage:** https://github.com/berlinux2016/gnome-chromecast-player
- **Issues:** https://github.com/berlinux2016/gnome-chromecast-player/issues
- **Releases:** https://github.com/berlinux2016/gnome-chromecast-player/releases

## 📊 What's Changed

**Full Changelog:** v1.3.0...v2.0.0

### Commits
- Added Recent Files feature with history tracking
- Implemented Playback Speed keyboard shortcuts
- Added Frame-by-Frame navigation functionality
- Created Shortcuts Help Dialog (H key)
- Fixed critical Play/Pause button handler bugs
- Improved Chromecast streaming workflow
- Enhanced mode switching reliability
- Updated documentation with new features

## 🙏 Acknowledgments

Thank you to all users who reported bugs and provided feedback!

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

---

**Enjoy the new features!** 🎬🚀

If you encounter any issues, please report them on our [issue tracker](https://github.com/berlinux2016/gnome-chromecast-player/issues).
