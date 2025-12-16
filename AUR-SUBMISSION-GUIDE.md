# AUR Submission Guide for gnome-chromecast-player

This guide explains how to submit this package to the Arch User Repository (AUR).

## Prerequisites

1. **AUR Account**: Create an account at https://aur.archlinux.org/register
2. **SSH Key**: Add your SSH public key to your AUR account settings
3. **Git**: Ensure git is installed on your system
4. **Base-devel**: Install the base-devel package group

```bash
sudo pacman -S base-devel git
```

## Step 1: Initial Setup

Clone the AUR repository (first time only):

```bash
git clone ssh://aur@aur.archlinux.org/gnome-chromecast-player.git aur-gnome-chromecast-player
cd aur-gnome-chromecast-player
```

## Step 2: Prepare Files

Copy the PKGBUILD and .SRCINFO files to the AUR directory:

```bash
cp ../PKGBUILD .
cp ../.SRCINFO .
```

## Step 3: Test the Package

Before submitting, test the package locally:

```bash
# Build the package
makepkg -si

# Test if it installs correctly
makepkg -f

# Test if it works
gnome-chromecast-player

# Clean up test files
makepkg -c
```

## Step 4: Generate .SRCINFO

Update the .SRCINFO file (required for AUR):

```bash
makepkg --printsrcinfo > .SRCINFO
```

## Step 5: Commit and Push to AUR

```bash
# Add files
git add PKGBUILD .SRCINFO

# Commit with a meaningful message
git commit -m "Initial commit: gnome-chromecast-player 2.0.0"

# Push to AUR
git push origin master
```

## Updating the Package

When releasing a new version:

1. Update `pkgver` in PKGBUILD
2. Update `pkgrel` to 1 (reset for new version)
3. Update the source URL if needed
4. Regenerate .SRCINFO:
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```
5. Test the package:
   ```bash
   makepkg -si
   ```
6. Commit and push:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to version X.Y.Z"
   git push origin master
   ```

## PKGBUILD Best Practices

- **pkgver**: Use semantic versioning (MAJOR.MINOR.PATCH)
- **pkgrel**: Increment for packaging fixes (not version bumps)
- **depends**: List all runtime dependencies
- **makedepends**: List build-time dependencies
- **optdepends**: List optional features with descriptions
- **source**: Use HTTPS URLs, prefer tags over branches
- **checksums**: Use `updpkgsums` to update checksums automatically

## Useful Commands

```bash
# Update checksums automatically
updpkgsums

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Test build in clean chroot (recommended)
extra-x86_64-build

# Check for common errors
namcap PKGBUILD
namcap *.pkg.tar.zst
```

## AUR Package Guidelines

Follow the Arch packaging guidelines:
- https://wiki.archlinux.org/title/PKGBUILD
- https://wiki.archlinux.org/title/AUR_submission_guidelines
- https://wiki.archlinux.org/title/Arch_package_guidelines

## Maintenance

As the package maintainer, you should:

1. **Monitor comments**: Check AUR package page for user feedback
2. **Update regularly**: Keep the package in sync with upstream releases
3. **Flag out-of-date**: Users will flag when a new version is available
4. **Respond to issues**: Help users with installation problems
5. **Test updates**: Always test before pushing updates

## Disowning the Package

If you can no longer maintain the package:

1. Go to the AUR package page
2. Click "Disown Package" under "Package Actions"
3. Another user can then adopt it

## Orphaning vs Deletion

- **Orphan**: Package remains, someone else can adopt
- **Delete**: Package is removed from AUR (requires TU approval)

## Getting Help

- **AUR Mailing List**: https://lists.archlinux.org/listinfo/aur-general
- **Arch Forums**: https://bbs.archlinux.org/
- **#archlinux-aur** on Libera.Chat IRC

## Example Workflow

```bash
# Initial submission
git clone ssh://aur@aur.archlinux.org/gnome-chromecast-player.git
cd gnome-chromecast-player
cp /path/to/PKGBUILD .
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "Initial commit"
git push

# Update to new version
vim PKGBUILD  # Update pkgver
updpkgsums    # Update checksums
makepkg --printsrcinfo > .SRCINFO
makepkg -si   # Test build
git add PKGBUILD .SRCINFO
git commit -m "Update to version X.Y.Z"
git push
```

## Notes

- **First submission**: Can take a few minutes to appear on AUR
- **Package naming**: Must match the `pkgname` in PKGBUILD
- **Git history**: Keep a clean commit history
- **Tags**: Consider using git tags for versions

## Contact

For questions about this package, open an issue on GitHub:
https://github.com/berlinux2016/gnome-chromecast-player/issues
