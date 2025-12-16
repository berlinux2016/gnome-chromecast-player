# Maintainer: DaHool <your-email@example.com>
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
    'gtk4'
    'libadwaita'
    'gstreamer'
    'gst-plugins-base'
    'gst-plugins-good'
    'gst-plugins-bad'
    'gst-plugins-ugly'
    'gst-libav'
    'ffmpeg'
    'python-pip'
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
source=("git+https://github.com/berlinux2016/gnome-chromecast-player.git#tag=v${pkgver}")
sha256sums=('SKIP')

pkgver() {
    cd "$pkgname"
    git describe --tags --long | sed 's/^v//;s/\([^-]*-g\)/r\1/;s/-/./g'
}

prepare() {
    cd "$pkgname"
    # Install Python dependencies to a temporary location
    pip install --target="${srcdir}/python-deps" -r requirements.txt --no-deps
}

build() {
    cd "$pkgname"
    # Nothing to build for Python application
}

package() {
    cd "$pkgname"

    # Install main application
    install -Dm755 videoplayer.py "${pkgdir}/usr/bin/${pkgname}"

    # Install Python dependencies
    if [ -d "${srcdir}/python-deps" ]; then
        mkdir -p "${pkgdir}/usr/lib/python$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)/site-packages"
        cp -r "${srcdir}/python-deps/"* "${pkgdir}/usr/lib/python$(python --version | cut -d' ' -f2 | cut -d'.' -f1,2)/site-packages/"
    fi

    # Install icon
    if [ -f icon.svg ]; then
        install -Dm644 icon.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/${pkgname}.svg"
    elif [ -f gnome-chromecast-player.svg ]; then
        install -Dm644 gnome-chromecast-player.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/${pkgname}.svg"
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
