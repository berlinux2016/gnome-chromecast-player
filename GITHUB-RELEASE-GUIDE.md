# GitHub Release Guide - v2.0.0

This guide explains how to create the GitHub Release for version 2.0.0.

## 📦 Release Files Created

All release files are located in `/run/media/dahool/Platte2/Videoplayer/`:

```
gnome-chromecast-player-2.0.0.tar.gz      (84 KB)  - Gzip compressed
gnome-chromecast-player-2.0.0.tar.bz2     (68 KB)  - Bzip2 compressed (smaller)
gnome-chromecast-player-2.0.0.sha256      (207 B)  - SHA256 checksums
```

## 🚀 Creating the GitHub Release

### Step 1: Navigate to GitHub Releases

1. Go to: https://github.com/berlinux2016/gnome-chromecast-player
2. Click on **"Releases"** in the right sidebar
3. Click **"Draft a new release"** button

### Step 2: Tag Information

- **Tag version:** `v2.0.0`
- **Target:** `main` branch
- **Release title:** `GNOME Chromecast Player v2.0.0`

### Step 3: Release Description

Copy the content from **RELEASE-NOTES-SHORT.md** into the description box.

**Or use this text:**

```markdown
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
```

### Step 4: Upload Release Files

Click **"Attach binaries by dropping them here or selecting them"** and upload:

1. ✅ `gnome-chromecast-player-2.0.0.tar.gz`
2. ✅ `gnome-chromecast-player-2.0.0.tar.bz2`
3. ✅ `gnome-chromecast-player-2.0.0.sha256`

### Step 5: Additional Settings

- ☑️ **Set as the latest release** - Check this box
- ☐ **Set as a pre-release** - Leave unchecked (this is a stable release)
- ☐ **Create a discussion for this release** - Optional (recommended for major releases)

### Step 6: Publish

Click **"Publish release"** button.

## ✅ Post-Release Checklist

After publishing the release:

### 1. Verify Release Page

Visit: https://github.com/berlinux2016/gnome-chromecast-player/releases/tag/v2.0.0

Check:
- ✅ Release title is correct
- ✅ All 3 files are attached
- ✅ Description displays correctly
- ✅ Tagged as "Latest"

### 2. Test Download Links

Download and verify one of the archives:

```bash
wget https://github.com/berlinux2016/gnome-chromecast-player/releases/download/v2.0.0/gnome-chromecast-player-2.0.0.tar.gz
sha256sum gnome-chromecast-player-2.0.0.tar.gz
# Should match: 0971be7b3d16d790a6b38001a2ec35f2321776b3aee9b89ccd06cf08fa65c2b2
```

### 3. Update README.md (Optional)

Add a badge to your README.md:

```markdown
[![Release](https://img.shields.io/github/v/release/berlinux2016/gnome-chromecast-player)](https://github.com/berlinux2016/gnome-chromecast-player/releases/latest)
```

### 4. Announce the Release (Optional)

Consider announcing on:
- GNOME Discourse
- Reddit (r/gnome, r/linux)
- Social media
- Project mailing lists

## 📝 Release Archive Contents

Each archive contains:

```
gnome-chromecast-player-2.0.0/
├── videoplayer.py              # Main application (172 KB)
├── README.md                   # Full documentation
├── LICENSE                     # MIT License
├── gnome-chromecast-player.spec
├── gnome-chromecast-player.desktop
├── gnome-chromecast-player.appdata.xml
├── gnome-chromecast-player.svg
├── build-rpm.sh               # RPM build script
├── install-local.sh           # Local install script
├── Makefile                   # Build system
├── INSTALL.md                 # Installation guide
└── BUILD-SYSTEM.md            # Build documentation
```

## 🔐 Security

### File Integrity

Users can verify downloads using SHA256:

```bash
sha256sum -c gnome-chromecast-player-2.0.0.sha256
```

### GPG Signing (Future Enhancement)

For future releases, consider GPG-signing the release:

```bash
gpg --detach-sign --armor gnome-chromecast-player-2.0.0.tar.gz
```

This creates a `.asc` signature file that can be uploaded with the release.

## 📊 Release Statistics

After a few days, check release statistics:

1. Go to: https://github.com/berlinux2016/gnome-chromecast-player/releases
2. Click on the release
3. Scroll to **"Assets"** section
4. View download counts for each file

## 🎯 Next Steps

After successful release:

1. **Monitor Issues** - Check for bug reports related to new features
2. **Update Documentation** - Ensure wiki/docs reflect v2.0.0 changes
3. **Plan v2.0.1** - Start collecting bugs for next patch release
4. **Plan v2.1.0** - Begin roadmap for next feature release

## 📞 Support

If you encounter issues during the release process:

- Check GitHub documentation: https://docs.github.com/en/repositories/releasing-projects-on-github
- Verify file permissions and sizes
- Ensure all files are properly named

---

**Happy releasing!** 🚀
