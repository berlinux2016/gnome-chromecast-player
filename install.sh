#!/bin/bash
# Installations-Skript für Video Chromecast Player mit AMD Hardware-Beschleunigung

echo "=== Video Chromecast Player Installation (AMD-optimiert) ==="
echo ""

# Prüfe ob auf Fedora
if [ ! -f /etc/fedora-release ]; then
    echo "Warnung: Dieses Skript ist für Fedora Linux optimiert."
    read -p "Trotzdem fortfahren? (j/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Jj]$ ]]; then
        exit 1
    fi
fi

# RPM Fusion Repositories aktivieren
echo "Aktiviere RPM Fusion Repositories..."
if ! rpm -q rpmfusion-free-release &>/dev/null; then
    sudo dnf install -y \
        https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
        https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
    echo "RPM Fusion wurde aktiviert."
else
    echo "RPM Fusion ist bereits aktiviert."
fi

# System-Abhängigkeiten installieren
echo ""
echo "Installiere System-Abhängigkeiten..."
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-gobject \
    gtk4 \
    libadwaita \
    gstreamer1 \
    gstreamer1-plugins-base \
    gstreamer1-plugins-good \
    gstreamer1-plugins-bad-free \
    gstreamer1-plugins-ugly-free \
    gstreamer1-libav

# Hardware-Beschleunigung (AMD VA-API / NVIDIA NVDEC)
echo ""
echo "Installiere Hardware-Beschleunigung..."

# Prüfe GPU-Typ
if command -v nvidia-smi &>/dev/null && nvidia-smi -L | grep -q "GPU"; then
    echo "NVIDIA GPU erkannt - installiere NVDEC/NVENC Unterstützung..."
    sudo dnf install -y \
        nvidia-vaapi-driver \
        libva-vdpau-driver \
        libvdpau-va-gl \
        gstreamer1-plugins-bad-free \
        ffmpeg
    echo "Hinweis: Stelle sicher, dass die NVIDIA-Treiber installiert sind!"
elif lspci | grep -i 'vga\|3d' | grep -qi 'amd\|radeon'; then
    echo "AMD GPU erkannt - installiere VA-API Unterstützung..."
    sudo dnf install -y \
        mesa-va-drivers \
        mesa-vdpau-drivers \
        libva \
        libva-utils \
        libva-vdpau-driver \
        gstreamer1-vaapi
else
    echo "Keine spezifische GPU erkannt - installiere Standard-Treiber..."
    sudo dnf install -y \
        libva \
        libva-utils \
        gstreamer1-vaapi \
        gstreamer1-plugins-bad-free
fi

# Vollständige Codec-Unterstützung mit RPM Fusion
echo ""
echo "Installiere vollständige Codec-Unterstützung (RPM Fusion)..."
sudo dnf install -y \
    gstreamer1-plugins-bad-freeworld \
    gstreamer1-plugins-ugly \
    gstreamer1-plugin-openh264 \
    mozilla-openh264 \
    ffmpeg \
    ffmpeg-libs

# Zusätzliche Hardware-Codecs für Intel (falls vorhanden)
sudo dnf install -y \
    libva-intel-driver \
    intel-media-driver 2>/dev/null || echo "Intel-Treiber übersprungen"

# Python-Abhängigkeiten installieren
echo ""
echo "Installiere Python-Abhängigkeiten..."
pip3 install --user -r requirements.txt

# Ausführbar machen
chmod +x videoplayer.py

# Icon installieren
echo ""
echo "Installiere App-Icon..."
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR"
cp icon.svg "$ICON_DIR/video-chromecast-player.svg"

# Desktop-Datei erstellen
echo "Erstelle Desktop-Verknüpfung..."
DESKTOP_FILE="$HOME/.local/share/applications/video-chromecast-player.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Video Chromecast Player
Name[de]=Video Chromecast Player
Comment=Video player with Chromecast support and AMD hardware acceleration
Comment[de]=Videoplayer mit Chromecast-Unterstützung und AMD Hardware-Beschleunigung
Exec=$(pwd)/videoplayer.py
Icon=video-chromecast-player
Terminal=false
Categories=AudioVideo;Video;Player;GTK;GNOME;
Keywords=video;player;chromecast;cast;streaming;
StartupNotify=true
StartupWMClass=video-chromecast-player
EOL

# Desktop-Datenbank und Icon-Cache aktualisieren
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# Hardware-Beschleunigung testen
echo ""
echo "Teste Hardware-Beschleunigung..."

if command -v nvidia-smi &>/dev/null && nvidia-smi -L | grep -q "GPU"; then
    echo ""
    echo "NVIDIA GPU Status:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null
    echo ""
    echo "NVDEC Status:"
    ffmpeg -hide_banner -encoders 2>&1 | grep -i nvenc | head -n 3 || echo "NVENC nicht verfügbar"
    echo ""
elif command -v vainfo &>/dev/null; then
    echo ""
    echo "VA-API Status:"
    vainfo 2>/dev/null | grep -E "Driver|VAProfile" | head -n 10
    echo ""
else
    echo "Hardware-Beschleunigung Tools nicht gefunden."
fi

echo ""
echo "=== Installation abgeschlossen! ==="
echo ""

# GPU-spezifische Hinweise
if command -v nvidia-smi &>/dev/null && nvidia-smi -L | grep -q "GPU"; then
    echo "Deine NVIDIA-Grafikkarte ist jetzt für Hardware-Beschleunigung konfiguriert."
    echo "Hardware-Beschleunigung: NVDEC (Dekodierung) + NVENC (Enkodierung)"
    echo ""
    echo "Um Hardware-Beschleunigung zu überprüfen:"
    echo "  nvidia-smi"
    echo "  ffmpeg -encoders | grep nvenc"
elif lspci | grep -i 'vga\|3d' | grep -qi 'amd\|radeon'; then
    echo "Deine AMD-Grafikkarte ist jetzt für Hardware-Beschleunigung konfiguriert."
    echo "Hardware-Beschleunigung: VA-API (Dekodierung + Enkodierung)"
    echo ""
    echo "Um Hardware-Beschleunigung zu überprüfen:"
    echo "  vainfo"
else
    echo "Generische Hardware-Beschleunigung wurde eingerichtet."
fi

echo ""
echo "Du kannst den Player jetzt starten mit:"
echo "  ./videoplayer.py"
echo ""
echo "Oder suche nach 'Video Chromecast Player' in deinen Anwendungen."
echo ""
echo "Hinweise:"
echo "- Hardware-Beschleunigung ist aktiviert (automatische GPU-Erkennung)"
echo "- Alle gängigen Video-Codecs sind installiert (H.264, H.265, VP9, AV1, etc.)"
echo "- Stelle sicher, dass Chromecast und Computer im gleichen Netzwerk sind"
echo ""
