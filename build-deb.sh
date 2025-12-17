#!/bin/bash
#
# Build Debian package for gnome-chromecast-player
# This script creates a .deb package for Debian and Ubuntu systems
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Building Debian Package${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "videoplayer.py" ]; then
    echo -e "${RED}Error: videoplayer.py not found!${NC}"
    echo "Please run this script from the gnome-chromecast-player directory."
    exit 1
fi

# Check if debian directory exists
if [ ! -d "debian" ]; then
    echo -e "${RED}Error: debian directory not found!${NC}"
    exit 1
fi

# Check for required build tools
echo -e "${YELLOW}Checking for required build tools...${NC}"
MISSING_TOOLS=()

if ! command -v dpkg-buildpackage &> /dev/null; then
    MISSING_TOOLS+=("dpkg-dev")
fi

if ! command -v debuild &> /dev/null; then
    MISSING_TOOLS+=("devscripts")
fi

if ! command -v dh &> /dev/null; then
    MISSING_TOOLS+=("debhelper")
fi

if ! command -v msgfmt &> /dev/null; then
    MISSING_TOOLS+=("gettext")
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo -e "${RED}Missing required tools!${NC}"
    echo "Please install them with:"
    echo "  sudo apt install ${MISSING_TOOLS[*]}"
    exit 1
fi

echo -e "${GREEN}All build tools found!${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf debian/gnome-chromecast-player
rm -f ../gnome-chromecast-player_*.deb
rm -f ../gnome-chromecast-player_*.build
rm -f ../gnome-chromecast-player_*.buildinfo
rm -f ../gnome-chromecast-player_*.changes
rm -f ../gnome-chromecast-player_*.tar.xz

# Compile locale files
echo -e "${YELLOW}Compiling locale files...${NC}"
if [ -f "locale/de/LC_MESSAGES/gnome-chromecast-player.po" ]; then
    msgfmt locale/de/LC_MESSAGES/gnome-chromecast-player.po -o locale/de/LC_MESSAGES/gnome-chromecast-player.mo
    echo -e "${GREEN}✓ German locale compiled${NC}"
fi
if [ -f "locale/en/LC_MESSAGES/gnome-chromecast-player.po" ]; then
    msgfmt locale/en/LC_MESSAGES/gnome-chromecast-player.po -o locale/en/LC_MESSAGES/gnome-chromecast-player.mo
    echo -e "${GREEN}✓ English locale compiled${NC}"
fi
echo ""

# Build the package
echo -e "${YELLOW}Building Debian package...${NC}"
dpkg-buildpackage -us -uc -b

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}Build Successful!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "Package created:"
    ls -lh ../gnome-chromecast-player_*.deb
    echo ""
    echo "To install the package, run:"
    echo -e "${YELLOW}  sudo dpkg -i ../gnome-chromecast-player_*.deb${NC}"
    echo -e "${YELLOW}  sudo apt-get install -f  # Install missing dependencies${NC}"
else
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}Build Failed!${NC}"
    echo -e "${RED}================================${NC}"
    exit 1
fi
