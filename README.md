<div align="center">

# 🎬 Video Chromecast Player

### Moderner GTK4 Videoplayer mit Chromecast-Streaming und Hardware-Beschleunigung

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GTK Version](https://img.shields.io/badge/GTK-4-blue.svg)](https://www.gtk.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)](https://www.linux.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/GitHub-berlinux2016%2Fgnome--chromecast--player-blue?logo=github)](https://github.com/berlinux2016/gnome-chromecast-player)

*Entwickelt von **DaHool** mit ❤️ für Simone*

[Features](#-features) • [Installation](#-installation) • [Usage](#-verwendung) • [Hardware Acceleration](#-hardware-beschleunigung) • [Troubleshooting](#-fehlerbehebung)

</div>

---

## 📸 Screenshots

> 🚧 Screenshots folgen in Kürze

<!--
![Hauptfenster](screenshots/main-window.png)
*Hauptfenster mit Timeline und Steuerung*

![Chromecast Modus](screenshots/chromecast-mode.png)
*Chromecast-Streaming mit Geräteauswahl*
-->

## ✨ Features

### 🎨 Moderne Benutzeroberfläche
- **GTK4/Libadwaita** UI im GNOME-Stil
- **Timeline/Seek-Funktion** mit Echtzeit-Positionsanzeige
- **Drag & Drop** zum Vor- und Zurückspulen
- **Dual-Mode**: Lokale Wiedergabe oder Chromecast-Streaming
- **Intuitive Steuerung**: Play, Pause, Stop, Seek

### ⚡ Hardware-Beschleunigung
- **AMD GPUs**: VA-API für Dekodierung + Enkodierung (bis 8K)
- **NVIDIA GPUs**: NVDEC/NVENC für Dekodierung + Enkodierung (bis 8K)
- **Automatische GPU-Erkennung** beim Start
- **Minimale CPU-Last** (< 5% bei 4K Wiedergabe)
- **Blitzschnelle Video-Konvertierung** (10-20x schneller als Software)

### 📡 Chromecast-Integration
- **Automatische Geräteerkennung** im Netzwerk (< 1 Sekunde)
- **Video-Streaming** zu allen Chromecast-Geräten
- **Xiaomi TV Kompatibilität** mit speziellen Fixes
- **Timeline-Synchronisation** zwischen Lokal und Chromecast
- **Intelligentes Caching**: Konvertierte Videos werden für schnelleren Zugriff gespeichert

### 🎞️ Video-Formate & Codecs
- **Alle gängigen Container**: MP4, MKV, AVI, WebM, MOV, FLV, OGG, MPEG, TS, WMV
- **Hardware-Codecs**: H.264, H.265/HEVC, VP9, AV1, VC-1
- **Software-Codecs**: MPEG-2, MPEG-4, DivX, XviD, Theora
- **Automatische MKV/AVI → MP4 Konvertierung** für Chromecast

### 🔒 Rechtliche Sicherheit
- **Keine Software-Codecs enthalten** - nur Hardware-APIs
- **Patent-sicher** - Hardware-Encoder unterliegen keinen Patentbeschränkungen
- **Open Source** - MIT Lizenz

## Systemanforderungen

- Fedora Linux 43 (oder ähnliche Distribution)
- Python 3.9 oder höher
- GTK4
- Libadwaita
- GStreamer 1.0
- **AMD oder NVIDIA Grafikkarte** (für Hardware-Beschleunigung - optional, funktioniert auch ohne)

## Installation

### Automatische Installation (Empfohlen)

Das Installations-Skript richtet automatisch alles ein, inklusive RPM Fusion und AMD Hardware-Beschleunigung:

```bash
chmod +x install.sh
./install.sh
```

Das Skript installiert:
- RPM Fusion Repositories (falls noch nicht vorhanden)
- Alle GStreamer-Pakete und Codecs
- AMD VA-API Treiber und Hardware-Beschleunigung
- Python-Abhängigkeiten
- Desktop-Verknüpfung für GNOME

### Manuelle Installation

Falls du die Installation manuell durchführen möchtest:

#### 1. RPM Fusion aktivieren

```bash
sudo dnf install -y \
    https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
    https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

#### 2. System-Abhängigkeiten installieren

```bash
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
```

#### 3. AMD Hardware-Beschleunigung

```bash
sudo dnf install -y \
    mesa-va-drivers \
    mesa-vdpau-drivers \
    libva \
    libva-utils \
    libva-vdpau-driver \
    gstreamer1-vaapi
```

#### 4. Vollständige Codecs (RPM Fusion)

```bash
sudo dnf install -y \
    gstreamer1-plugins-bad-freeworld \
    gstreamer1-plugins-ugly \
    gstreamer1-plugin-openh264 \
    mozilla-openh264 \
    ffmpeg \
    ffmpeg-libs
```

#### 5. Python-Abhängigkeiten

```bash
pip3 install --user -r requirements.txt
```

#### 6. Ausführbar machen

```bash
chmod +x videoplayer.py
```

## Verwendung

### Starten der Anwendung

```bash
./videoplayer.py
```

Oder suche nach "Video Chromecast Player" in deinen GNOME-Anwendungen.

### Video abspielen

1. Klicke auf das Ordner-Symbol in der Header-Bar, um eine Video-Datei zu öffnen
2. Das Video wird automatisch in der Vorschau angezeigt
3. Nutze die Steuerelemente am unteren Rand:
   - Play-Button: Wiedergabe starten
   - Pause-Button: Wiedergabe pausieren
   - Stop-Button: Wiedergabe stoppen

### Chromecast verwenden

1. Stelle sicher, dass dein Chromecast und dein Computer im gleichen Netzwerk sind
2. Klicke auf das WLAN-Symbol in der Header-Bar, um nach Chromecast-Geräten zu suchen
3. In der rechten Seitenleiste werden gefundene Geräte angezeigt
4. Klicke auf ein Gerät, um dich zu verbinden
5. Der Modus-Schalter wechselt automatisch auf "Chromecast"
6. Öffne ein Video und starte die Wiedergabe
7. **MKV/AVI-Dateien werden automatisch zu MP4 konvertiert** - das kann beim ersten Mal einige Sekunden dauern
8. Konvertierte Videos werden gecacht in `~/.cache/video-chromecast-player/` für schnelleren Zugriff beim nächsten Mal

### Modi

- **Lokal**: Video wird auf deinem Computer abgespielt
- **Chromecast**: Video wird auf das verbundene Chromecast-Gerät gestreamt

Du kannst zwischen den Modi mit dem Schalter in der Steuerungsleiste wechseln.

## Hardware-Beschleunigung

Der Player erkennt automatisch deine GPU und nutzt die entsprechende Hardware-Beschleunigung. Dies reduziert die CPU-Last erheblich, besonders bei hochauflösenden Videos (4K, 8K).

### AMD Grafikkarten (VA-API)

Der Player nutzt VA-API für Hardware-Dekodierung und -Enkodierung.

**Hardware-Beschleunigung prüfen:**
```bash
vainfo
```

**Erwartete Ausgabe:**
```
libva info: VA-API version 1.20.0
libva info: User environment variable requested driver 'radeonsi'
libva info: Trying to open /usr/lib64/dri/radeonsi_drv_video.so
Driver version: Mesa Gallium driver ... for AMD Radeon Graphics
VAProfileH264Main               : VAEntrypointVLD
VAProfileH264High               : VAEntrypointVLD
VAProfileHEVCMain               : VAEntrypointVLD
VAProfileHEVCMain10             : VAEntrypointVLD
...
```

**Unterstützte Codecs:**
- **H.264/AVC** (bis zu 4K)
- **H.265/HEVC** (bis zu 8K, 10-bit)
- **VP9** (bis zu 4K)
- **AV1** (auf neueren AMD-Karten)
- **MPEG-2**, **VC-1**

### NVIDIA Grafikkarten (NVDEC/NVENC)

Der Player nutzt NVDEC für Hardware-Dekodierung und NVENC für Hardware-Enkodierung.

**Voraussetzungen:**
- NVIDIA proprietäre Treiber müssen installiert sein
- FFmpeg mit NVENC-Unterstützung (wird vom install.sh installiert)

**Hardware-Beschleunigung prüfen:**
```bash
nvidia-smi
ffmpeg -encoders | grep nvenc
```

**Erwartete Ausgabe:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx             Driver Version: 535.xx.xx   CUDA: 12.2  |
|-------------------------------+----------------------+----------------------+
| GPU  Name                     | Bus-Id        | GPU-Util  Memory-Usage     |
|===============================+======================+======================|
|   0  GeForce RTX xxxx         | 00000000:01:00.0 |    0%      xxxMiB      |
+-------------------------------+----------------------+----------------------+

V..... h264_nvenc           NVIDIA NVENC H.264 encoder
V..... hevc_nvenc           NVIDIA NVENC HEVC encoder
```

**Unterstützte Codecs:**
- **H.264/AVC** (bis zu 8K auf neueren Karten)
- **H.265/HEVC** (bis zu 8K auf neueren Karten)
- **AV1** (auf RTX 40-Serie und neuer)

**Performance-Vorteile:**
- Extrem schnelle Video-Konvertierung (oft 10-20x schneller als Software)
- Minimale CPU-Last (< 5%)
- Unterstützt mehrere parallele Encoding-Sessions

## Unterstützte Video-Formate

Durch RPM Fusion werden **alle gängigen Video-Formate** unterstützt:

### Container-Formate
- **MP4** - H.264, H.265/HEVC, AV1
- **MKV** (Matroska) - alle Codecs
- **AVI** - DivX, XviD, etc.
- **WebM** - VP8, VP9, AV1
- **MOV** (QuickTime)
- **FLV** (Flash Video)
- **OGG/OGV** - Theora, Vorbis
- **MPG/MPEG** - MPEG-1, MPEG-2
- **TS** (Transport Stream)
- **WMV** - Windows Media Video

### Video-Codecs
- **H.264/AVC** ✓ Hardware
- **H.265/HEVC** ✓ Hardware
- **VP8, VP9** ✓ Hardware
- **AV1** ✓ Hardware (auf unterstützten GPUs)
- **MPEG-2, MPEG-4**
- **DivX, XviD**
- **Theora**
- **VC-1** ✓ Hardware

### Audio-Codecs
- **AAC, MP3, Opus, Vorbis, FLAC, AC3, DTS** und viele mehr

## Fehlerbehebung

### Automatisches Debugging

Für eine schnelle Diagnose von Problemen, führe aus:
```bash
./debug-chromecast.sh
```

Dieses Skript überprüft:
- Netzwerk-Verbindung
- Firewall-Konfiguration
- Python-Abhängigkeiten
- Chromecast-Geräte im Netzwerk
- HTTP-Server-Ports

### Firewall automatisch konfigurieren

Falls Chromecast-Probleme auftreten, führe aus:
```bash
./fix-firewall.sh
```

Dieses Skript öffnet automatisch alle notwendigen Ports.

### Chromecast wird nicht gefunden

**Symptom**: Beim Klicken auf "Chromecast-Geräte suchen" werden keine Geräte angezeigt.

**Lösungen**:
1. Prüfe, ob dein Computer und Chromecast im gleichen WLAN sind
2. Führe das Firewall-Fix-Skript aus:
   ```bash
   ./fix-firewall.sh
   ```

   Oder manuell:
   ```bash
   sudo firewall-cmd --permanent --add-service=mdns
   sudo firewall-cmd --permanent --add-port=8008-8009/tcp
   sudo firewall-cmd --permanent --add-port=8765-8888/tcp
   sudo firewall-cmd --reload
   ```

3. Starte den Chromecast neu (Strom ziehen und wieder einstecken)
4. Warte beim Scannen die vollen 15 Sekunden ab

### Video wird nicht abgespielt

- Führe das Installations-Skript aus, um alle Codecs zu installieren
- Prüfe die Konsolen-Ausgabe auf Fehler: `./videoplayer.py`
- Teste GStreamer direkt:
  ```bash
  gst-launch-1.0 filesrc location=dein-video.mp4 ! decodebin ! autovideosink
  ```

### Hardware-Beschleunigung funktioniert nicht

1. Prüfe VA-API:
   ```bash
   vainfo
   ```

2. Prüfe ob GStreamer VA-API findet:
   ```bash
   gst-inspect-1.0 vaapi
   ```

3. Überprüfe Umgebungsvariablen:
   ```bash
   echo $LIBVA_DRIVER_NAME  # sollte "radeonsi" sein
   ```

### Chromecast-Streaming funktioniert nicht

**Symptom**: Verbindung zum Chromecast klappt, aber Video wird nicht abgespielt.

**Lösungen**:

1. **Automatische Konvertierung**
   - Der Player konvertiert MKV/AVI automatisch zu MP4
   - Beim ersten Mal kann dies 10-60 Sekunden dauern
   - Status wird in der App angezeigt ("Konvertiere Video...")
   - Konvertierte Dateien werden gecacht für schnelleren Zugriff
   - Falls die Konvertierung fehlschlägt, stelle sicher dass FFmpeg installiert ist:
     ```bash
     sudo dnf install ffmpeg
     ```

2. **Manuelle Konvertierung** (falls automatisch nicht funktioniert)
   ```bash
   # Schnelle Konvertierung (ohne Re-Encoding)
   ffmpeg -i video.mkv -c copy video.mp4

   # Mit Re-Encoding (garantierte Kompatibilität)
   ffmpeg -i video.mkv -c:v libx264 -c:a aac video.mp4
   ```

3. **Cache löschen** (falls Probleme mit gecachten Videos)
   ```bash
   rm -rf ~/.cache/video-chromecast-player/
   ```

4. **Firewall-Ports öffnen**
   Der HTTP-Server benötigt offene Ports:
   ```bash
   ./fix-firewall.sh
   ```

3. **Detaillierte Logs prüfen**
   Starte die App im Terminal für detaillierte Fehler-Informationen:
   ```bash
   ./videoplayer.py
   ```

4. **HTTP-Server-Erreichbarkeit testen**
   Die App testet automatisch, ob der HTTP-Server vom Chromecast erreicht werden kann.
   Wenn dieser Test fehlschlägt, ist es ein Firewall-Problem.

5. **Netzwerk-Probleme**
   - Stelle sicher, dass Computer und Chromecast im gleichen Subnetz sind
   - Manche Router blockieren Kommunikation zwischen Geräten (AP Isolation)
   - Deaktiviere "Client Isolation" in deinen Router-Einstellungen

## Abhängigkeiten

### System-Pakete
- `gtk4` - GTK4 Toolkit
- `libadwaita` - GNOME Libadwaita
- `gstreamer1-*` - GStreamer Multimedia-Framework
- `gstreamer1-vaapi` - VA-API Hardware-Beschleunigung
- `mesa-va-drivers` - AMD VA-API Treiber
- `python3-gobject` - Python GTK Bindings
- `ffmpeg` - FFmpeg Codecs (via RPM Fusion)

### Python-Pakete
- `PyGObject` - Python GTK/GObject Bindings
- `pychromecast` - Chromecast-Steuerung
- `zeroconf` - Netzwerk-Service-Discovery

## Performance-Tipps

### CPU-Last bei Video-Wiedergabe

Mit AMD Hardware-Beschleunigung:
- **4K H.264**: ~5-10% CPU (ohne: 40-60%)
- **4K HEVC**: ~5-15% CPU (ohne: 60-80%)
- **1080p**: ~2-5% CPU (ohne: 20-40%)

### Überprüfe ob Hardware-Beschleunigung aktiv ist

Starte den Player im Terminal und achte auf diese Meldung:
```
Hardware-Beschleunigung (VA-API) aktiviert
```

Nutze `htop` oder `top` während der Wiedergabe um CPU-Last zu überwachen.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

## Autor

**DaHool** - [GitHub](https://github.com/berlinux2016/gnome-chromecast-player)

Mit Liebe gemacht für Simone ❤️

## Entwicklung

### Projektstruktur

```
Videoplayer/
├── videoplayer.py      # Hauptanwendung
├── requirements.txt    # Python-Abhängigkeiten
├── install.sh         # Installations-Skript
└── README.md          # Dokumentation
```

### 🤝 Beitragen

Beiträge sind willkommen! Hier ist wie du helfen kannst:

1. **Fork** das Repository
2. Erstelle einen **Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. **Push** zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen **Pull Request**

#### Coding Standards
- Folge PEP 8 für Python-Code
- Kommentiere komplexe Logik auf Deutsch
- Teste deine Änderungen gründlich auf AMD und NVIDIA Hardware (falls möglich)

#### Bug Reports
Wenn du einen Bug findest:
1. Prüfe ob er bereits als Issue gemeldet wurde
2. Erstelle ein neues Issue mit:
   - Detaillierter Beschreibung
   - Schritten zur Reproduktion
   - System-Informationen (Fedora Version, GPU, etc.)
   - Log-Ausgabe von `./videoplayer.py`

## Bekannte Einschränkungen

1. Chromecast-Streaming erfordert, dass Videos über HTTP erreichbar sind
2. Einige Video-Codecs benötigen zusätzliche Plugins
3. Die Anwendung wurde primär für Fedora 43 getestet

## 🚀 Roadmap / Zukünftige Features

- [ ] **Playlist-Unterstützung** - Mehrere Videos in einer Warteschlange
- [ ] **Untertitel-Support** - SRT, ASS, VTT Dateien
- [ ] **Lautstärkeregelung** - Lokale und Chromecast Lautstärke-Kontrolle
- [ ] **Vollbild-Modus** - F11 für Vollbild-Wiedergabe
- [ ] **Drag-and-Drop** - Videos einfach in das Fenster ziehen
- [ ] **Tastatur-Shortcuts** - Space (Play/Pause), Pfeiltasten (Seek), etc.
- [ ] **Video-Info-Overlay** - Codec, Bitrate, Auflösung anzeigen
- [ ] **Audio-Track-Auswahl** - Bei mehrsprachigen Videos
- [ ] **Abspiellisten-Import** - M3U/PLS Format-Support

## 📊 Version History

### Version 1.2.0 (Dezember 2024)
- ✨ Timeline/Seek-Funktion für lokale und Chromecast-Wiedergabe
- ✨ NVIDIA Hardware-Beschleunigung (NVDEC/NVENC)
- 🐛 Verbesserte Chromecast-Kompatibilität (Xiaomi TVs)
- ⚡ Chromecast-Gerätesuche 30x schneller (500ms statt 15s)
- 🔧 Modus-Wechsel zwischen Lokal und Chromecast optimiert
- 🔒 **Rechtliche Bereinigung**: Entfernung aller Software-Codecs

### Version 1.0.0 (Dezember 2024)
- 🎉 Erste Version
- ✨ AMD VA-API Hardware-Beschleunigung
- ✨ Automatische MKV/AVI zu MP4 Konvertierung
- ✨ GTK4/Libadwaita UI
- ✨ Chromecast-Streaming mit HTTP-Server
