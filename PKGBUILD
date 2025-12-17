# Maintainer: DaHool <torsten.mobi@gmail.com>
pkgname=gnome-chromecast-player
pkgver=2.0.1
pkgrel=1
pkgdesc="Modern GTK4 video player with Chromecast streaming and hardware acceleration"
arch=('any')
url="https://github.com/berlinux2016/gnome-chromecast-player"
license=('MIT')
depends=(
    'python>=3.9'
    'python-gobject'
    'python-pychromecast'
    'python-zeroconf'
    'python-requests'
    'gtk4'
    'libadwaita'
    'gstreamer'
    'gst-plugins-base'
    'gst-plugins-good'
    'gst-plugins-bad'
    'gst-plugins-ugly'
    'gst-libav'
    'ffmpeg'
    'gettext'
)
makedepends=('git')
optdepends=(
    'libva-mesa-driver: Hardware acceleration for AMD GPUs'
    'libva-intel-driver: Hardware acceleration for Intel GPUs'
    'intel-media-driver: Hardware acceleration for newer Intel GPUs'
    'libva-nvidia-driver: Hardware acceleration for NVIDIA GPUs'
    'nvidia-utils: NVIDIA GPU support'
    'gstreamer-vaapi: VA-API support for GStreamer'
    'yt-dlp: YouTube video support'
    'x264: H.264 encoding support'
    'x265: H.265/HEVC encoding support'
    'libvpx: VP8/VP9 encoding support'
    'aom: AV1 encoding support'
)
source=("${pkgname}::git+file://$(pwd)")
sha256sums=('SKIP')

pkgver() {
    cd "$srcdir/$pkgname"
    # Get version from git tag and format it properly for pacman
    # Converts v2.0.1-0-g1384d17 to 2.0.1.r0.g1384d17
    git describe --tags --long 2>/dev/null | sed 's/^v//;s/\([^-]*-g\)/r\1/;s/-/./g' || echo "2.0.1"
}

build() {
    cd "$pkgname"
    # Compile locale files
    for lang in locale/*/LC_MESSAGES/*.po; do
        if [ -f "$lang" ]; then
            lang_code=$(echo "$lang" | cut -d'/' -f2)
            msgfmt "$lang" -o "locale/${lang_code}/LC_MESSAGES/gnome-chromecast-player.mo"
        fi
    done
}

package() {
    cd "$pkgname"

    # Install main application
    install -Dm755 videoplayer.py "${pkgdir}/usr/bin/${pkgname}"

    # Install i18n module
    install -Dm644 i18n.py "${pkgdir}/usr/share/${pkgname}/i18n.py"

    # Install compiled locale files
    for lang in locale/*/LC_MESSAGES/*.mo; do
        if [ -f "$lang" ]; then
            lang_code=$(echo "$lang" | cut -d'/' -f2)
            install -Dm644 "$lang" "${pkgdir}/usr/share/locale/${lang_code}/LC_MESSAGES/${pkgname}.mo"
        fi
    done

    # Install icon (with both names for compatibility)
    if [ -f icon.svg ]; then
        install -Dm644 icon.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/${pkgname}.svg"
        install -Dm644 icon.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/com.videocast.player.svg"
    elif [ -f gnome-chromecast-player.svg ]; then
        install -Dm644 gnome-chromecast-player.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/${pkgname}.svg"
        install -Dm644 gnome-chromecast-player.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/com.videocast.player.svg"
    fi

    # Install desktop file
    install -Dm644 gnome-chromecast-player.desktop "${pkgdir}/usr/share/applications/${pkgname}.desktop"

    # Fix Exec path in desktop file
    sed -i "s|Exec=.*|Exec=/usr/bin/${pkgname}|" "${pkgdir}/usr/share/applications/${pkgname}.desktop"

    # Install AppData/MetaInfo
    if [ -f gnome-chromecast-player.appdata.xml ]; then
        install -Dm644 gnome-chromecast-player.appdata.xml "${pkgdir}/usr/share/metainfo/${pkgname}.appdata.xml"
    fi

    # Install license
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"

    # Install documentation
    install -Dm644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"

    # Install utility scripts
    install -Dm755 debug-chromecast.sh "${pkgdir}/usr/share/${pkgname}/debug-chromecast.sh"
    install -Dm755 fix-firewall.sh "${pkgdir}/usr/share/${pkgname}/fix-firewall.sh"
    install -Dm755 clear-cache.sh "${pkgdir}/usr/share/${pkgname}/clear-cache.sh"
}
