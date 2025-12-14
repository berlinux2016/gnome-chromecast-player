# Build System Overview

GNOME Chromecast Player includes a comprehensive build and packaging system for easy installation and distribution.

## 📦 Available Installation Methods

| Method | Command | Use Case | Root Required |
|--------|---------|----------|---------------|
| **RPM Package** | `./build-rpm.sh` | Production, Distribution | Yes (for install) |
| **Local Install** | `./install-local.sh` | Development, Testing | No |
| **Makefile** | `make install` | Custom Locations | Yes |
| **Direct Run** | `python3 videoplayer.py` | Quick Testing | No |

## 🚀 Quick Start

### For End Users (Recommended)

```bash
# Build RPM package
./build-rpm.sh

# Install the package
sudo dnf install ~/rpmbuild/RPMS/noarch/gnome-chromecast-player-2.0.0-1.*.rpm
```

### For Developers

```bash
# Install locally without root
./install-local.sh install

# Or run directly from source
python3 videoplayer.py
```

## 📁 Build System Files

### Core Files

| File | Purpose |
|------|---------|
| `build-rpm.sh` | Main RPM build script with dependency checking |
| `gnome-chromecast-player.spec` | RPM spec file for package building |
| `Makefile` | Alternative build system with multiple targets |
| `install-local.sh` | User-local installation script |

### Metadata Files

| File | Purpose |
|------|---------|
| `gnome-chromecast-player.desktop` | Desktop entry for application menu |
| `gnome-chromecast-player.appdata.xml` | AppStream metadata for software centers |
| `gnome-chromecast-player.svg` | Application icon (128x128) |
| `LICENSE` | MIT License |
| `README.md` | Main documentation |
| `INSTALL.md` | Detailed installation guide |

## 🔨 Build Scripts Explained

### build-rpm.sh

**Features:**
- Automatic dependency checking
- RPM build environment setup
- Source tarball creation
- Colored output with progress indicators
- Post-build verification
- Runtime dependency checking

**Process:**
1. Checks system compatibility
2. Installs build dependencies if missing
3. Sets up `~/rpmbuild` directory structure
4. Creates source tarball
5. Copies spec file
6. Builds RPM package
7. Shows results and installation instructions

**Usage:**
```bash
./build-rpm.sh
```

### install-local.sh

**Features:**
- No root privileges required
- Installs to `~/.local`
- Desktop integration
- Icon installation
- Clean uninstallation

**Install:**
```bash
./install-local.sh install
```

**Uninstall:**
```bash
./install-local.sh uninstall
```

**Installation Locations:**
- Binary: `~/.local/bin/gnome-chromecast-player`
- Application: `~/.local/share/gnome-chromecast-player/`
- Desktop entry: `~/.local/share/applications/`
- Icon: `~/.local/share/icons/hicolor/scalable/apps/`

### Makefile

**Available Targets:**

| Target | Description |
|--------|-------------|
| `make help` | Show all available targets |
| `make install` | Install system-wide (default: /usr/local) |
| `make uninstall` | Remove from system |
| `make rpm` | Build RPM package |
| `make local-install` | Install to ~/.local |
| `make local-uninstall` | Remove from ~/.local |
| `make check` | Check dependencies |
| `make clean` | Clean build artifacts |

**Custom Installation Prefix:**
```bash
sudo make install PREFIX=/opt/gnome-chromecast-player
```

**Environment Variables:**
- `PREFIX` - Installation prefix (default: `/usr/local`)
- `DESTDIR` - Destination directory for staged installs

## 🎯 RPM Spec File Details

### Package Information
- **Name:** gnome-chromecast-player
- **Version:** 2.0.0
- **License:** MIT
- **Architecture:** noarch (pure Python)

### Dependencies

**Build Requirements:**
- python3-devel
- desktop-file-utils
- libappstream-glib

**Runtime Requirements:**
- Python 3.9+
- GTK4 + Libadwaita
- GStreamer with plugins
- pychromecast
- yt-dlp
- ffmpeg

### Installation Directories

| Type | Directory |
|------|-----------|
| Binary | `/usr/bin/` |
| Application | `/usr/share/gnome-chromecast-player/` |
| Desktop Entry | `/usr/share/applications/` |
| Icon | `/usr/share/icons/hicolor/scalable/apps/` |
| Metadata | `/usr/share/metainfo/` |

## 🧪 Testing the Build

### Verify Desktop Entry

```bash
desktop-file-validate gnome-chromecast-player.desktop
```

### Verify AppStream Metadata

```bash
appstream-util validate-relax --nonet gnome-chromecast-player.appdata.xml
```

### Test RPM Build Without Installing

```bash
./build-rpm.sh
rpm -qlp ~/rpmbuild/RPMS/noarch/gnome-chromecast-player-2.0.0-1.*.rpm
```

### Check Dependencies

```bash
make check
```

## 📊 Build Output Structure

After building the RPM, files are located at:

```
~/rpmbuild/
├── BUILD/              # Build directory (temporary)
├── RPMS/
│   └── noarch/
│       └── gnome-chromecast-player-2.0.0-1.*.rpm  # Binary RPM
├── SOURCES/
│   └── gnome-chromecast-player-2.0.0.tar.gz       # Source tarball
├── SPECS/
│   └── gnome-chromecast-player.spec               # Spec file
└── SRPMS/
    └── gnome-chromecast-player-2.0.0-1.*.src.rpm  # Source RPM
```

## 🔍 Troubleshooting

### Build Dependencies Missing

```bash
sudo dnf install rpm-build rpmdevtools desktop-file-utils libappstream-glib
```

### Runtime Dependencies Missing

```bash
sudo dnf install python3 gtk4 libadwaita python3-gobject \
    gstreamer1 gstreamer1-plugins-{base,good,bad-free,ugly-free} \
    gstreamer1-vaapi python3-pychromecast python3-requests yt-dlp ffmpeg
```

### Desktop Entry Not Showing

```bash
update-desktop-database ~/.local/share/applications
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

### Permission Denied on Scripts

```bash
chmod +x build-rpm.sh install-local.sh
```

## 🚢 Distribution

### For Fedora/RHEL Users

Distribute the built RPM package:

```bash
~/rpmbuild/RPMS/noarch/gnome-chromecast-player-2.0.0-1.*.rpm
```

Users can install with:

```bash
sudo dnf install gnome-chromecast-player-2.0.0-1.*.rpm
```

### For Other Distributions

Provide the source tarball:

```bash
~/rpmbuild/SOURCES/gnome-chromecast-player-2.0.0.tar.gz
```

Or point users to the repository for direct installation.

## 🔄 Updating the Version

When releasing a new version:

1. **Update version in files:**
   - `gnome-chromecast-player.spec` (Version field)
   - `build-rpm.sh` (VERSION variable)
   - `Makefile` (VERSION variable)
   - `gnome-chromecast-player.appdata.xml` (add release entry)

2. **Update changelog:**
   - Add entry in spec file `%changelog` section
   - Update README.md Version History

3. **Rebuild:**
   ```bash
   ./build-rpm.sh
   ```

## 📝 Best Practices

### For Development
- Use `./install-local.sh` or run directly with `python3 videoplayer.py`
- Test frequently without system installation
- Use `make check` to verify dependencies

### For Testing
- Build RPM in clean environment
- Test installation and uninstallation
- Verify desktop integration works
- Check all dependencies are declared

### For Distribution
- Use semantic versioning (major.minor.patch)
- Document all changes in changelog
- Test on clean Fedora installation
- Sign RPM packages if distributing publicly

## 🎓 Learning Resources

### RPM Packaging
- [Fedora RPM Guide](https://docs.fedoraproject.org/en-US/packaging-guidelines/)
- [RPM Packaging Tutorial](https://rpm-packaging-guide.github.io/)

### Desktop Entry
- [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/)
- [Desktop File Keys](https://wiki.archlinux.org/title/desktop_entries)

### AppStream
- [AppStream Documentation](https://www.freedesktop.org/software/appstream/docs/)
- [AppStream Generator](https://github.com/ximion/appstream-generator)

## 💡 Tips

1. **Always test builds in clean environment** - Use containers or VMs
2. **Keep spec file updated** - Maintain accurate dependency list
3. **Version your releases** - Use git tags for version tracking
4. **Document changes** - Keep comprehensive changelog
5. **Test installation paths** - Verify all files are installed correctly

## 📞 Support

For build-related issues:
1. Check `INSTALL.md` for detailed instructions
2. Run `make check` to verify dependencies
3. Review build script output for errors
4. Check file permissions with `ls -la`

For application issues:
- See main `README.md`
- Check issue tracker on GitHub
