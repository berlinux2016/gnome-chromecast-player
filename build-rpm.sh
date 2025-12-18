#!/bin/bash
#
# RPM Build Script for GNOME Chromecast Player
# This script creates an RPM package from the current source code
#

set -e  # Exit on error

# Configuration
APP_NAME="gnome-chromecast-player"
VERSION="2.0.1"
RELEASE="1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Fedora/RHEL
check_system() {
    print_info "Checking system..."
    if [ ! -f /etc/fedora-release ] && [ ! -f /etc/redhat-release ]; then
        print_warning "This script is designed for Fedora/RHEL-based systems"
    fi
}

# Install build dependencies
install_build_deps() {
    print_info "Checking build dependencies..."

    local packages=(
        "rpm-build"
        "rpmdevtools"
        "desktop-file-utils"
        "libappstream-glib"
    )

    local missing=()
    for pkg in "${packages[@]}"; do
        if ! rpm -q "$pkg" &>/dev/null; then
            missing+=("$pkg")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        print_info "Installing missing build dependencies: ${missing[*]}"
        sudo dnf install -y "${missing[@]}" || {
            print_error "Failed to install dependencies"
            exit 1
        }
    else
        print_success "All build dependencies are installed"
    fi
}

# Setup RPM build environment
setup_rpm_env() {
    print_info "Setting up RPM build environment..."

    # Create rpmbuild directory structure
    rpmdev-setuptree

    print_success "RPM build environment ready at ~/rpmbuild"
}

# Create source tarball
create_tarball() {
    print_info "Creating source tarball..."

    local TARBALL_NAME="${APP_NAME}-${VERSION}"
    local TEMP_DIR="/tmp/${TARBALL_NAME}"
    local ORIGINAL_DIR="$(pwd)"

    # Clean up old temp directory
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"

    # Copy files to temp directory
    cp videoplayer.py "$TEMP_DIR/"
    cp README.md "$TEMP_DIR/"
    cp LICENSE "$TEMP_DIR/"
    cp ${APP_NAME}.desktop "$TEMP_DIR/"
    cp ${APP_NAME}.appdata.xml "$TEMP_DIR/"

    # Copy icon if exists
    if [ -f "${APP_NAME}.svg" ]; then
        cp ${APP_NAME}.svg "$TEMP_DIR/"
    else
        print_warning "Icon file ${APP_NAME}.svg not found - creating placeholder"
        # Create a simple placeholder SVG
        cat > "$TEMP_DIR/${APP_NAME}.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" version="1.1" xmlns="http://www.w3.org/2000/svg">
  <rect width="128" height="128" fill="#3584e4" rx="16"/>
  <path d="m64 32-32 32h24v32h16v-32h24z" fill="#fff"/>
  <circle cx="64" cy="96" r="8" fill="#fff"/>
</svg>
EOF
    fi

    # Create tarball
    cd /tmp
    tar -czf "${TARBALL_NAME}.tar.gz" "${TARBALL_NAME}/"

    # Copy to rpmbuild SOURCES
    cp "${TARBALL_NAME}.tar.gz" ~/rpmbuild/SOURCES/

    # Cleanup
    rm -rf "$TEMP_DIR"

    # Return to original directory
    cd "$ORIGINAL_DIR"

    print_success "Source tarball created: ~/rpmbuild/SOURCES/${TARBALL_NAME}.tar.gz"
}

# Copy spec file
copy_spec() {
    print_info "Copying spec file..."

    cp ${APP_NAME}.spec ~/rpmbuild/SPECS/

    print_success "Spec file copied to ~/rpmbuild/SPECS/"
}

# Build RPM
build_rpm() {
    print_info "Building RPM package..."

    cd ~/rpmbuild/SPECS
    rpmbuild -ba ${APP_NAME}.spec

    if [ $? -eq 0 ]; then
        print_success "RPM package built successfully!"
    else
        print_error "RPM build failed"
        exit 1
    fi
}

# Show results
show_results() {
    print_info "Build complete! Packages location:"
    echo ""
    echo -e "${GREEN}SRPM:${NC}"
    ls -lh ~/rpmbuild/SRPMS/${APP_NAME}-${VERSION}-${RELEASE}*.src.rpm 2>/dev/null || echo "  Not found"
    echo ""
    echo -e "${GREEN}RPM:${NC}"
    ls -lh ~/rpmbuild/RPMS/noarch/${APP_NAME}-${VERSION}-${RELEASE}*.rpm 2>/dev/null || echo "  Not found"
    echo ""
    print_info "To install the package, run:"
    echo -e "${BLUE}  sudo dnf install ~/rpmbuild/RPMS/noarch/${APP_NAME}-${VERSION}-${RELEASE}*.rpm${NC}"
    echo ""
}

# Check runtime dependencies (optional)
check_runtime_deps() {
    print_info "Checking runtime dependencies..."

    local runtime_deps=(
        "python3"
        "gtk4"
        "libadwaita"
        "python3-gobject"
        "gstreamer1"
        "gstreamer1-plugins-base"
        "gstreamer1-plugins-good"
        "gstreamer1-plugins-bad-free"
        "gstreamer1-vaapi"
        "python3-pychromecast"
        "python3-requests"
        "yt-dlp"
        "ffmpeg"
    )

    local missing_runtime=()
    for pkg in "${runtime_deps[@]}"; do
        if ! rpm -q "$pkg" &>/dev/null; then
            missing_runtime+=("$pkg")
        fi
    done

    if [ ${#missing_runtime[@]} -gt 0 ]; then
        print_warning "Missing runtime dependencies (will be installed with RPM):"
        for pkg in "${missing_runtime[@]}"; do
            echo "  - $pkg"
        done
    else
        print_success "All runtime dependencies are already installed"
    fi
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   GNOME Chromecast Player - RPM Build Script      ║${NC}"
    echo -e "${BLUE}║              Version ${VERSION}                          ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Change to script directory
    cd "$(dirname "$0")"

    # Execute build steps
    check_system
    install_build_deps
    setup_rpm_env
    create_tarball
    copy_spec
    build_rpm
    echo ""
    show_results
    echo ""
    check_runtime_deps

    echo ""
    print_success "All done! 🎉"
    echo ""
}

# Run main function
main "$@"
