# Arch Linux Support for Video Chromecast Player

This directory contains all necessary files for running and packaging Video Chromecast Player on Arch Linux.

## 📦 New Files Created

### Installation & Packaging

1. **[install-arch.sh](install-arch.sh)** - Automated installation script for Arch Linux
   - Detects GPU (AMD/NVIDIA/Intel) and installs appropriate drivers
   - Installs all system and Python dependencies
   - Creates desktop entry and icon

2. **[PKGBUILD](PKGBUILD)** - Build script for creating Arch packages
   - Ready for AUR submission
   - Includes all dependencies and optional dependencies
   - Supports all GPU types

3. **[.SRCINFO](.SRCINFO)** - Package metadata for AUR
   - Generated from PKGBUILD
   - Required for AUR submission

4. **[AUR-SUBMISSION-GUIDE.md](AUR-SUBMISSION-GUIDE.md)** - Complete guide for submitting to AUR
   - Step-by-step instructions
   - Maintenance guidelines
   - Best practices

5. **[INSTALL-ARCH.md](INSTALL-ARCH.md)** - Detailed installation guide for Arch Linux
   - Multiple installation methods
   - Troubleshooting section
   - Performance information

### Internationalization (i18n)

6. **[i18n.py](i18n.py)** - Translation module
   - Gettext-based translation system
   - Automatic language detection
   - Support for multiple languages

7. **locale/** - Translation files directory
   - `locale/messages.pot` - Translation template
   - `locale/de/LC_MESSAGES/` - German translations
   - `locale/en/LC_MESSAGES/` - English translations

8. **[I18N-GUIDE.md](I18N-GUIDE.md)** - Internationalization guide
   - How to add translations
   - Developer guide
   - Translator guide

## 🚀 Quick Start (Arch Linux)

### Option 1: Using Installation Script

```bash
chmod +x install-arch.sh
./install-arch.sh
```

### Option 2: From AUR (Coming Soon)

```bash
yay -S gnome-chromecast-player
```

## 🌍 Supported Languages

- **English (en)** - Default language
- **German (de)** - Deutsch

The application automatically detects your system language.

## 📋 Dependencies

### Required
- python >= 3.9
- python-gobject
- gtk4
- libadwaita
- gstreamer
- gst-plugins-base/good/bad/ugly
- gst-libav
- ffmpeg

### Optional (Hardware Acceleration)
- **AMD**: libva-mesa-driver, gstreamer-vaapi
- **NVIDIA**: libva-nvidia-driver, nvidia-utils
- **Intel**: intel-media-driver, libva-intel-driver

### Optional (Features)
- yt-dlp: YouTube video support

## 📝 Next Steps

### For Users
1. Run `./install-arch.sh` to install
2. Read [README.md](README.md) for usage instructions
3. Read [INSTALL-ARCH.md](INSTALL-ARCH.md) for detailed installation info

### For Package Maintainers
1. Read [AUR-SUBMISSION-GUIDE.md](AUR-SUBMISSION-GUIDE.md)
2. Test PKGBUILD: `makepkg -si`
3. Submit to AUR (see guide)

### For Translators
1. Read [I18N-GUIDE.md](I18N-GUIDE.md)
2. Copy `locale/en/LC_MESSAGES/gnome-chromecast-player.po`
3. Translate strings
4. Submit pull request

## 🔧 Testing PKGBUILD

Before submitting to AUR:

```bash
# Build package
makepkg -si

# Test package
gnome-chromecast-player

# Clean build
makepkg -c

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO
```

## 🐛 Troubleshooting

### Chromecast Not Found
```bash
./fix-firewall.sh
```

### Debug Information
```bash
./debug-chromecast.sh
```

### Hardware Acceleration Test
```bash
# AMD/Intel
vainfo

# NVIDIA
nvidia-smi
```

## 📚 Documentation Structure

```
.
├── README.md                    # Main documentation (English)
├── INSTALL-ARCH.md             # Arch Linux installation guide
├── AUR-SUBMISSION-GUIDE.md     # AUR packaging guide
├── I18N-GUIDE.md               # Translation guide
├── ARCH-LINUX-README.md        # This file
├── install-arch.sh             # Arch installation script
├── PKGBUILD                    # AUR build script
├── .SRCINFO                    # AUR metadata
├── i18n.py                     # Translation module
└── locale/                     # Translation files
    ├── messages.pot
    ├── de/LC_MESSAGES/
    └── en/LC_MESSAGES/
```

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines:

1. **Code**: Follow PEP 8, test thoroughly
2. **Translations**: See I18N-GUIDE.md
3. **Packaging**: Test PKGBUILD before submitting
4. **Documentation**: Keep guides up-to-date

## 📫 Support

- **Issues**: https://github.com/berlinux2016/gnome-chromecast-player/issues
- **Discussions**: https://github.com/berlinux2016/gnome-chromecast-player/discussions

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

**Made with ❤️ for Simone by DaHool**
