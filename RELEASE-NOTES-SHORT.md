## 🎉 What's New in v2.0.0

Major feature release with productivity enhancements and critical bug fixes!

### ✨ New Features

- **📁 Recent Files** - Quick access to last 10 opened videos
- **⚡ Playback Speed Shortcuts** - `[` and `]` keys for speed control (0.25x-3.0x)
- **🎬 Frame-by-Frame Navigation** - `,` and `.` keys for precise video analysis
- **⌨️ Shortcuts Help Dialog** - Press `H` to view all keyboard shortcuts

### 🐛 Critical Fixes

- **Fixed Play/Pause button crashes** when switching between Chromecast and local playback
- **Eliminated memory leaks** from signal handlers
- **Improved Chromecast streaming** workflow and reliability

### 📦 Installation

**Fedora/RHEL (Recommended):**
```bash
tar -xzf gnome-chromecast-player-2.0.0.tar.gz
cd gnome-chromecast-player-2.0.0
./build-rpm.sh
sudo dnf install ~/rpmbuild/RPMS/noarch/gnome-chromecast-player-2.0.0-1.*.rpm
```

**Local Install (No root):**
```bash
tar -xzf gnome-chromecast-player-2.0.0.tar.gz
cd gnome-chromecast-player-2.0.0
./install-local.sh install
```

See [INSTALL.md](https://github.com/berlinux2016/gnome-chromecast-player/blob/main/INSTALL.md) for detailed instructions.

### 🔍 Checksums

**SHA256:**
```
3658a9eed3d2ecf79953f2b543149a0612ebca581e233e3c5d5eec2fe7a1a007  gnome-chromecast-player-2.0.0.tar.bz2
0971be7b3d16d790a6b38001a2ec35f2321776b3aee9b89ccd06cf08fa65c2b2  gnome-chromecast-player-2.0.0.tar.gz
```

**Full Changelog:** https://github.com/berlinux2016/gnome-chromecast-player/compare/v1.3.0...v2.0.0
