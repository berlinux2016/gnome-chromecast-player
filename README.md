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
- **YouTube Video Streaming** - Direkte Wiedergabe von YouTube-Videos über URL-Eingabe
- **Playlist-Unterstützung** - Mehrere Videos in Warteschlange mit Auto-Advance
- **Playlist-Thumbnails** - Automatische Video-Vorschaubilder in der Playlist
- **Recent Files** - Verlauf der zuletzt geöffneten Videos (max. 10)
- **Vollbild-Modus** - F11 für Vollbild-Wiedergabe
- **Drag & Drop** - Videos direkt ins Fenster ziehen
- **Timeline/Seek-Funktion** mit Echtzeit-Positionsanzeige
- **Lautstärkeregelung** mit Slider für lokale und Chromecast-Wiedergabe
- **Video-Info-Overlay** - Zeigt Codec, Auflösung und Bitrate an
- **Video-Effekte** - Rotation, Spiegelung, Zoom, Crop, Gamma-Korrektur
- **Filter-Presets** - 10 vordefinierte Filter (Sepia, Vintage, Schwarz-Weiß, etc.)
- **Untertitel-Support** - Automatische Erkennung von SRT, ASS, VTT Dateien
- **Audio-Track-Auswahl** - Wechsel zwischen mehreren Audio-Spuren
- **Lesezeichen/Resume** - Automatisches Speichern und Fortsetzen der Wiedergabe
- **Wiedergabegeschwindigkeit** - 0.25x bis 3.0x mit Dropdown-Menü und Tastaturkürzeln
- **Frame-by-Frame Navigation** - Präzise Einzelbild-Navigation mit , und . Tasten
- **Screenshot-Funktion** - Frame-Capture mit S-Taste
- **Video-Equalizer** - Helligkeit, Kontrast, Sättigung und Farbton anpassen
- **A-B Loop** - Wiederholungsschleife zwischen zwei Punkten für Lern-Videos
- **Go-To-Zeit** - Sprung zu bestimmter Zeitposition (MM:SS oder HH:MM:SS)
- **Kapitel-Erkennung** - Automatische Erkennung und Navigation von MKV/MP4 Kapiteln
- **Timeline-Thumbnails** - Vorschau-Bilder beim Hovern über Timeline
- **Tastatur-Shortcuts** - Umfangreiche Tastatursteuerung mit Hilfe-Dialog (H-Taste)
- **Abspiellisten-Import** - M3U und PLS Format-Support
- **Intuitive Steuerung**: Previous, Next, Play, Pause, Stop, Seek, Volume

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
- **Untertitel-Unterstützung** - Untertitel auf Chromecast-Gerät anzeigen
- **Audio-Track-Auswahl** - Wähle Audio-Spuren für Chromecast-Wiedergabe
- **Multi-Room-Audio** - Synchronisierte Wiedergabe auf mehreren Geräten
- **Gruppen-Support** - Verbindung mit Chromecast-Gruppen
- **Erweiterte Status-Anzeige** - Detaillierte Chromecast-Informationen in Echtzeit

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
2. Das Video wird automatisch zur Playlist hinzugefügt und in der Vorschau angezeigt
3. Nutze die Steuerelemente am unteren Rand:
   - **Previous-Button**: Vorheriges Video in Playlist
   - **Play-Button**: Wiedergabe starten
   - **Pause-Button**: Wiedergabe pausieren
   - **Stop-Button**: Wiedergabe stoppen
   - **Next-Button**: Nächstes Video in Playlist
   - **Lautstärke-Slider**: Lautstärke anpassen (0-100%)
   - **Timeline-Slider**: Zu beliebiger Position springen

### Playlist verwenden

1. **Videos hinzufügen**:
   - Klicke auf **+** in der Playlist-Sektion, um mehrere Videos auszuwählen
   - **ODER** ziehe einfach Video-Dateien per Drag & Drop ins Fenster
2. Die Videos werden in der Reihenfolge abgespielt
3. Nach Ende eines Videos startet automatisch das nächste (Auto-Advance)
4. Klicke auf ein Video in der Playlist, um direkt dorthin zu springen
5. Nutze **Previous** und **Next** Buttons zum Navigieren
6. Entferne einzelne Videos mit dem **X**-Button
7. **Playlist importieren**:
   - Klicke auf den **Import-Button** (Ordner-Symbol) in der Playlist-Sektion.
   - Wähle eine `.m3u`- oder `.pls`-Datei aus.
   - Die enthaltenen Videos werden automatisch zur Playlist hinzugefügt.
8. Leere die gesamte Playlist mit dem **Papierkorb**-Button

**Playlist-Thumbnails:**
- Jedes Video in der Playlist zeigt automatisch ein **Vorschaubild** (Thumbnail) aus dem Video
- Thumbnails werden beim ersten Mal automatisch extrahiert und gecacht
- Die Vorschaubilder werden aus der Mitte des Videos (ca. 5 Sekunden) generiert
- Thumbnails sind **60x60 Pixel** groß für optimale Performance
- Gecachte Thumbnails werden in `~/.cache/gnome-chromecast-player/thumbnails/` gespeichert
- Bei YouTube-Videos oder URLs wird ein Standard-Video-Icon angezeigt

### Drag & Drop verwenden

1. Öffne deinen Dateimanager und navigiere zu deinen Videos
2. Wähle ein oder mehrere Video-Dateien aus
3. Ziehe sie ins Video-Player-Fenster
4. Die Videos werden automatisch zur Playlist hinzugefügt
5. Das erste Video startet automatisch die Wiedergabe (falls noch kein Video läuft)
6. **Visuelles Feedback**: Der Bereich wird blau umrandet beim Darüberziehen

### YouTube Videos abspielen

1. Klicke auf den **YouTube-Button** (▶-Symbol) in der Header-Bar
2. Ein Dialog öffnet sich mit einem Eingabefeld für die YouTube-URL
3. Füge die URL eines YouTube-Videos ein (z.B. `https://www.youtube.com/watch?v=...`)
4. Klicke auf **Video laden**
5. Das Video wird automatisch extrahiert und zur Playlist hinzugefügt
6. **Hinweis**: Benötigt `yt-dlp` für die Video-Extraktion
7. Funktioniert sowohl für lokale Wiedergabe als auch für Chromecast-Streaming

### Vollbild-Modus

1. Drücke die **F11**-Taste, um in den Vollbild-Modus zu wechseln und ihn wieder zu verlassen
2. Alternativ kannst du den Vollbild-Button in der Kopfleiste verwenden

### Tastatur-Shortcuts

**Drücke H für eine vollständige Übersicht aller Tastenkürzel im Player!**

#### Wiedergabe
- **Leertaste**: Wiedergabe / Pause
- **←/→**: 5 Sekunden zurück/vor
- **,/.**: Frame rückwärts/vorwärts (Frame-by-Frame)
- **[/]**: Geschwindigkeit verringern/erhöhen
- **N**: Nächstes Video in Playlist
- **P**: Vorheriges Video in Playlist

#### Lautstärke & Audio
- **↑/↓**: Lautstärke erhöhen/verringern (5%)
- **M**: Stummschalten / Ton an

#### Ansicht
- **F11 oder F**: Vollbildmodus umschalten
- **I**: Info-Overlay ein/aus

#### A-B Loop & Export
- **A**: Loop-Punkt A setzen
- **B**: Loop-Punkt B setzen
- **C**: Loop löschen
- **E**: Clip exportieren (A-B)

#### Navigation
- **G**: Zu Zeit springen
- **S**: Screenshot erstellen (nur lokal)

#### Hilfe
- **H**: Tastaturkürzel-Übersicht anzeigen

### Untertitel verwenden

1. **Automatische Erkennung**: Lege eine Untertitel-Datei (`.srt`, `.ass`, `.vtt`) in denselben Ordner wie dein Video. Die Datei muss denselben Namen haben (z.B. `MeinFilm.mp4` und `MeinFilm.srt`).
2. **Auswählen**: Wenn ein Video mit Untertiteln geladen wird, wird der Untertitel-Button (Sprechblase) in der Kopfleiste aktiv.
3. Klicke auf den Button, um eine Untertitel-Spur auszuwählen oder die Untertitel zu deaktivieren.

### Audio-Spur auswählen

1. Bei Videos mit mehreren Audio-Spuren (z.B. mehrsprachige Filme) wird der Audio-Button (Lautsprecher) in der Kopfleiste aktiv.
2. Klicke auf den Button, um zwischen verfügbaren Audio-Spuren zu wechseln.
3. Die Audio-Spuren zeigen Sprache, Titel und Codec an (z.B. "Spur 1 (deu) [AC-3]").

### Lesezeichen / Wiedergabe fortsetzen

1. **Automatisches Speichern**: Der Player speichert automatisch deine Position beim Schließen oder Wechseln des Videos.
2. **Fortsetzen**: Beim erneuten Öffnen eines Videos wird ein Dialog angezeigt, um die Wiedergabe fortzusetzen oder von vorne zu beginnen.
3. **Intelligentes Speichern**: Positionen werden nur gespeichert, wenn mehr als 5 Sekunden abgespielt wurden und das Video nicht in den letzten 30 Sekunden ist.
4. **Lesezeichen-Verwaltung**: Lesezeichen werden automatisch entfernt, wenn du ein Video bis zum Ende schaust oder von vorne beginnst.

### Wiedergabegeschwindigkeit anpassen

1. Klicke auf den Geschwindigkeits-Button (Vorspul-Symbol) in der Kopfleiste.
2. Wähle eine Geschwindigkeit: **0.5x**, **0.75x**, **Normal (1.0x)**, **1.25x**, **1.5x** oder **2.0x**.
3. Die Geschwindigkeit wird sofort angewendet (nur für lokale Wiedergabe).
4. Perfekt zum Lernen (langsam) oder schnellen Durchsehen (schnell).

### Screenshot aufnehmen

1. Drücke die **S-Taste** während der Wiedergabe (nur lokale Wiedergabe).
2. Der Screenshot wird automatisch gespeichert in: `~/Pictures/Video-Screenshots/`
3. Dateiname-Format: `VideoName_20251209_153045.png` (mit Timestamp).
4. Eine Bestätigung erscheint in der Statusleiste.

### Video-Equalizer verwenden

1. Klicke auf den Equalizer-Button (Farb-Symbol) in der Kopfleiste.
2. Passe die folgenden Werte mit den Slidern an:
   - **Helligkeit**: -1.0 bis +1.0 (0 = Standard)
   - **Kontrast**: 0.0 bis 2.0 (1.0 = Standard)
   - **Sättigung**: 0.0 bis 2.0 (1.0 = Standard)
   - **Farbton**: -1.0 bis +1.0 (0 = Standard)
3. Änderungen werden sofort angewendet.
4. Klicke auf **Zurücksetzen**, um alle Werte auf Standard zurückzusetzen.
5. Perfekt für Videos mit schlechter Farbqualität oder zu dunklen Szenen.

### Video-Effekte verwenden

1. Klicke auf den **Video-Effekte-Button** (Bild-Symbol) in der Kopfleiste
2. Ein Fenster mit 3 Tabs öffnet sich:

**Tab 1 - Rotation & Spiegelung:**
   - **Normal**: Keine Rotation
   - **90° ↻**: 90° im Uhrzeigersinn drehen
   - **180°**: Um 180° drehen
   - **90° ↺**: 90° gegen Uhrzeigersinn drehen
   - **↔ Horizontal**: Horizontal spiegeln
   - **↕ Vertikal**: Vertikal spiegeln

**Tab 2 - Zoom & Crop:**
   - **Zoom**: 0.5x bis 3.0x Vergrößerung (Standard: 1.0x)
   - **Zuschneiden**: Schneide Pixel von jeder Seite ab
     - Oben: 0-500 Pixel
     - Unten: 0-500 Pixel
     - Links: 0-500 Pixel
     - Rechts: 0-500 Pixel

**Tab 3 - Gamma & Filter:**
   - **Gamma-Korrektur**: 0.1 bis 3.0 (Standard: 1.0)
     - Höhere Werte = heller
     - Niedrigere Werte = dunkler
   - **Filter-Presets**: 10 vordefinierte Effekte
     - **Normal**: Standard-Einstellungen
     - **Sepia**: Vintage Sepia-Ton
     - **Graustufen**: Schwarz-Weiß ohne Kontrast
     - **Schwarz-Weiß**: Hoher Kontrast Schwarz-Weiß
     - **Vintage**: Retro-Look mit reduzierten Farben
     - **Lebhaft**: Kräftige, gesättigte Farben
     - **Dunkel**: Dunkler Film-Look
     - **Hell**: Aufgehelltes Video
     - **Kalt**: Kühlerer Blau-Ton
     - **Warm**: Wärmerer Orange-Ton

3. Klicke auf **Alle Effekte zurücksetzen**, um alle Einstellungen auf Standard zurückzusetzen
4. Perfekt für Videos mit falscher Ausrichtung, ungewünschten Rändern oder für kreative Effekte

### A-B Loop verwenden (Wiederholungsschleife)

1. Spiele ein Video ab und navigiere zum gewünschten **Startpunkt**.
2. Drücke die **A-Taste** oder klicke auf den **A-Button**, um Punkt A zu setzen.
3. Navigiere zum gewünschten **Endpunkt**.
4. Drücke die **B-Taste** oder klicke auf den **B-Button**, um Punkt B zu setzen.
5. Die Schleife ist nun aktiv - das Video springt automatisch zu Punkt A zurück, wenn Punkt B erreicht wird.
6. Um die Schleife zu löschen, drücke die **C-Taste** oder klicke auf den **Clear-Button** (X).
7. Perfekt für Lern-Videos, Sprach-Training oder Musik-Loops.

### Go-To-Zeit verwenden (Zu bestimmter Zeit springen)

1. Drücke die **G-Taste** oder klicke auf den **Go-To-Button** (Sprung-Symbol) in der Steuerungsleiste.
2. Ein Dialog öffnet sich mit einem Eingabefeld für die Zielzeit.
3. Gib die Zeit ein im Format **MM:SS** (z.B. `5:30`) oder **HH:MM:SS** (z.B. `1:23:45`).
4. Das Eingabefeld ist bereits mit der aktuellen Position vorausgefüllt.
5. Klicke auf **Springen**, um zur eingegebenen Zeit zu springen.
6. Perfekt zum schnellen Navigieren zu bekannten Zeitstempeln.

### Kapitel verwenden (Chapter Navigation)

1. Bei Videos mit Kapiteln (MKV/MP4 mit Chapter-Metadata) wird der **Kapitel-Button** (Listen-Symbol) in der Kopfleiste aktiv.
2. Klicke auf den Button, um eine Liste aller Kapitel zu sehen.
3. Jeder Eintrag zeigt den Kapitel-Titel und die Startzeit (z.B. "Kapitel 1: Intro (00:05:30)").
4. Klicke auf ein Kapitel, um direkt dorthin zu springen.
5. Perfekt für strukturierte Videos wie Tutorials, Filme oder Vorlesungen.

### Timeline-Thumbnails verwenden (Vorschau beim Hovern)

1. Wenn ein Video im **lokalen Modus** geladen ist, bewege die Maus über die Timeline.
2. Ein **Vorschau-Popover** erscheint automatisch mit einem Thumbnail des aktuellen Frames.
3. Unter dem Thumbnail wird die Zeitposition angezeigt.
4. Bewege die Maus entlang der Timeline, um verschiedene Positionen zu sehen.
5. Thumbnails werden gecacht für schnellere Anzeige.
6. **Hinweis**: Feature ist nur im lokalen Modus verfügbar, nicht bei Chromecast-Wiedergabe.

### Chromecast verwenden

1. Stelle sicher, dass dein Chromecast und dein Computer im gleichen Netzwerk sind
2. Klicke auf das WLAN-Symbol in der Header-Bar, um nach Chromecast-Geräten zu suchen
3. In der rechten Seitenleiste werden gefundene Geräte angezeigt
4. Klicke auf ein Gerät, um dich zu verbinden
5. Der Modus-Schalter wechselt automatisch auf "Chromecast"
6. Öffne ein Video und starte die Wiedergabe
7. **MKV/AVI-Dateien werden automatisch zu MP4 konvertiert** - das kann beim ersten Mal einige Sekunden dauern
8. Konvertierte Videos werden gecacht in `~/.cache/video-chromecast-player/` für schnelleren Zugriff beim nächsten Mal

### Erweiterte Chromecast-Features

**Erweiterte Status-Anzeige:**
1. Nach der Verbindung mit einem Chromecast erscheint ein **"Erweiterte Informationen"** Expander in der Seitenleiste
2. Klappe ihn auf, um detaillierte Informationen zu sehen:
   - Gerätename und Modell
   - Aktive App
   - Wiedergabe-Status (PLAYING 🟢, PAUSED 🟡, BUFFERING 🔵, IDLE ⚪)
   - Aktuell abgespielte Media
   - Wiedergabe-Fortschritt in Prozent
   - Gruppen-Mitglieder (falls in einer Gruppe)

**Chromecast-Gruppen (Multi-Room-Audio):**
1. Erstelle Gruppen in der **Google Home App** auf deinem Smartphone
2. Füge mehrere Chromecast-Geräte zu einer Gruppe hinzu
3. Im Video Player werden Gruppen automatisch bei der Geräte-Suche angezeigt
4. Verbinde dich mit einer Gruppe wie mit einem normalen Gerät
5. Audio wird synchronisiert auf allen Geräten in der Gruppe abgespielt
6. Die Status-Anzeige zeigt alle Gruppenmitglieder an

**Untertitel für Chromecast:**
- Untertitel werden automatisch mit dem Video übertragen (experimentell)
- Funktioniert mit VTT-Format (besser unterstützt als SRT)
- HTTP-Server stellt Untertitel-Dateien bereit

**Audio-Track-Auswahl:**
- Mehrere Audio-Spuren werden auf Chromecast unterstützt
- Wechsel zwischen verfügbaren Audio-Tracks möglich

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

## 🚀 Roadmap / Geplante Features

### 🎨 Video-Effekte & Verarbeitung
- [x] **Video-Rotation & Spiegelung** - Drehen (90°, 180°, 270°) und spiegeln (horizontal/vertikal) ✓
- [x] **Crop & Zoom** - Dynamisches Zuschneiden und Zoomen während der Wiedergabe ✓
- [x] **Filter-Presets** - Vordefinierte Effekte (Sepia, Schwarz-Weiß, Vintage) ✓
- [x] **Gamma-Korrektur** - Erweiterte Gamma-Anpassung für bessere Darstellung ✓
- [ ] **RGB-Kanal-Kontrolle** - Individuelle Einstellung von Rot-, Grün- und Blau-Kanälen

### 📋 Playlist-Management
- [x] **Playlist-Thumbnails** - Automatische Video-Vorschaubilder in der Playlist ✓
- [ ] **Playlist-Suche** - Schnelles Filtern und Suchen in der Playlist
- [ ] **Smart Playlists** - Automatische Playlists (Zuletzt gespielt, Meistgeschaut)
- [ ] **Playlist-Kategorien** - Organisation mit Tags und Kategorien
- [ ] **Sortier-Optionen** - Nach Name, Größe, Datum, Dauer sortieren
- [ ] **Playlist-Statistiken** - Gesamtdauer, Anzahl Videos, durchschnittliche Länge
- [ ] **Netzwerk-Playlisten** - HTTP-URLs für M3U-Playlists unterstützen

### 📡 Erweiterte Streaming-Features
- [ ] **Twitch Integration** - Live-Streams und VODs direkt abspielen
- [ ] **Vimeo Support** - Native Vimeo-Video-Unterstützung
- [ ] **Dailymotion Support** - Dailymotion-Videos streamen
- [ ] **HLS Adaptive Streaming** - Automatische Qualitätsanpassung bei Bandbreitenwechsel
- [ ] **Batch-URL-Download** - Mehrere URLs gleichzeitig laden
- [ ] **Stream-Recorder** - Live-Streams aufzeichnen

### 🎯 Benutzerfreundlichkeit
- [ ] **Kontextmenü** - Rechtsklick-Menü mit häufigen Aktionen
- [x] **Tastatur-Shortcuts-Hilfe** - Visuelle Übersicht aller Shortcuts (H-Taste) ✓
- [x] **Recent Files** - Verlauf der zuletzt geöffneten Videos ✓
- [ ] **Schnell-Einstellungen-Panel** - Dashboard mit häufig genutzten Einstellungen
- [ ] **Fenster-Position speichern** - Automatisches Merken der Fensterposition
- [ ] **Gesten-Steuerung** - Touch-Gesten für Tablets und Touchscreens
- [ ] **Dunkelmodus-Umschalter** - Manueller Toggle zwischen Hell/Dunkel-Theme

### ⚡ Power-User Features
- [ ] **Segment-Export** - Video-Segmente von A nach B exportieren
- [ ] **Batch-Konvertierung** - Mehrere Videos gleichzeitig konvertieren
- [x] **Frame-Stepping** - Einzelne Frames vor/zurück (,/. Tasten) ✓
- [ ] **Metadaten-Editor** - Bearbeitung von Video-Tags, Titel, Beschreibung
- [ ] **Codec-Analyse** - Detaillierte Codec-Informationen und Bitrate-Graphen
- [ ] **Markierungs-System** - Custom Marker für wichtige Zeitpunkte
- [ ] **GIF-Export** - Video-Segmente als animierte GIFs exportieren
- [ ] **Vergleichsmodus** - Zwei Videos nebeneinander vergleichen

### 📊 Visualisierung & Statistiken
- [ ] **Bitrate-Graph** - Visueller Verlauf der Video-Bitrate
- [ ] **FPS-Anzeige** - Aktuelle Framerate in Echtzeit
- [ ] **CPU/GPU-Monitoring** - Systemressourcen-Auslastung anzeigen
- [ ] **Puffer-Status** - Detaillierte Anzeige des Puffer-Prozentsatzes
- [ ] **Kapitel-Minimap** - Visuelle Kapitel-Marker auf Timeline
- [ ] **Audio-Waveform** - Audio-Wellenform-Visualisierung
- [ ] **Thumbnail-Grid** - Storyboard-Ansicht aller Video-Thumbnails

### 🔧 Chromecast-Erweiterungen
- [x] **Chromecast-Untertitel** - Untertitel-Steuerung auf Remote-Gerät ✓
- [x] **Chromecast-Audio-Tracks** - Audio-Spur-Auswahl für Chromecast ✓
- [x] **Multi-Room-Audio** - Synchronisierte Wiedergabe auf mehreren Geräten ✓
- [x] **Chromecast-Gruppen** - Unterstützung für Audio-Gruppen ✓
- [x] **Erweiterte Status-Anzeige** - Detaillierte Chromecast-Informationen ✓

### 🌐 Netzwerk & Integration
- [ ] **DLNA/UPnP Support** - Netzwerk-Medienserver-Integration
- [ ] **SMB/NFS Support** - Direkte Wiedergabe von Netzwerk-Shares
- [ ] **Cloud-Speicher** - OneDrive, Google Drive, Dropbox Integration
- [ ] **Auto-Subtitle-Download** - Automatischer Download von OpenSubtitles.org

### 🎵 Audio-Features
- [ ] **Audio-Equalizer** - Bass, Treble, und Multi-Band EQ
- [ ] **Audio-Normalisierung** - Automatische Lautstärke-Anpassung
- [ ] **Surround-Sound** - 5.1/7.1 Audio-Spatialisierung
- [ ] **Audio-Track-Export** - Audio-Spuren als separate Dateien exportieren

### ⌨️ Zusätzliche Tastatur-Shortcuts
- [ ] **J/L Tasten** - -10/+10 Sekunden Seek (VLC-Style)
- [ ] **0-9 Tasten** - Sprung zu 0%-90% der Video-Länge
- [x] **[/] Tasten** - Wiedergabegeschwindigkeit verringern/erhöhen ✓
- [x] **,/. Tasten** - Frame rückwärts/vorwärts ✓
- [ ] **T Taste** - Untertitel Ein/Aus Toggle
- [x] **H Taste** - Shortcuts-Hilfe anzeigen ✓
- [ ] **Ctrl+O** - Datei öffnen Dialog
- [ ] **Ctrl+U** - URL-Dialog öffnen
- [ ] **Ctrl+Q** - Anwendung beenden

### 🔄 Import/Export
- [ ] **Einstellungs-Backup** - Export/Import von Konfigurationen
- [ ] **Lesezeichen-Export** - Backup aller Wiedergabepositionen
- [ ] **Untertitel-Extraktion** - Untertitel aus Videos extrahieren
- [ ] **Kapitel-Export** - Kapitel-Informationen exportieren (JSON/XML)
- [ ] **Metadaten-Export** - Video-Informationen als CSV/JSON

## 📊 Version History

### Version 2.0.0 (Dezember 2025)
- ✨ **Recent Files** - Verlauf der zuletzt geöffneten Videos (max. 10 Einträge)
- 🕐 Recent Files Button in Header-Bar mit Uhr-Symbol
- 📋 Automatisches Tracking lokaler Video-Dateien
- 🗑️ "Verlauf löschen" Option im Menü
- 💾 Speicherung in `~/.config/video-chromecast-player/recent_files.json`
- ✨ **Playback Speed Shortcuts** - Tastaturkürzel für Geschwindigkeitsänderung
- ⌨️ **[** Taste: Geschwindigkeit verringern (0.25x bis 3.0x)
- ⌨️ **]** Taste: Geschwindigkeit erhöhen (0.25x bis 3.0x)
- 🎯 10 Geschwindigkeitsstufen mit Status-Feedback
- ✨ **Frame-by-Frame Navigation** - Präzise Einzelbild-Navigation
- ⌨️ **,** Taste: Frame rückwärts (25 FPS / 0.04s)
- ⌨️ **.** Taste: Frame vorwärts (25 FPS / 0.04s)
- 🎬 Automatisches Pausieren für Frame-Analyse
- 🎯 Perfekt für Screenshots und Video-Analyse
- ✨ **Shortcuts Help Dialog** - Tastaturkürzel-Übersicht
- ⌨️ **H** Taste: Shortcuts-Dialog anzeigen
- 📖 Übersichtlich in 6 Kategorien organisiert (Wiedergabe, Lautstärke, Ansicht, A-B Loop, Navigation, Hilfe)
- 📜 Scrollbare Liste aller Tastenkombinationen
- 🎨 Professionelles Design mit Monospace-Schrift für Tastennamen

### Version 1.3.0 (Dezember 2025)
- ✨ **Playlist-Thumbnails** - Automatische Video-Vorschaubilder in der Playlist
- 🖼️ Jedes Video zeigt ein 60x60 Pixel Thumbnail aus der Video-Mitte
- ⚡ Asynchrone Thumbnail-Extraktion ohne UI-Blockierung
- 💾 Intelligentes Caching-System in `~/.cache/gnome-chromecast-player/thumbnails/`
- 🎨 Platzhalter-Icon für YouTube-Videos und URLs
- 🔧 `extract_video_thumbnail()` Methode für GStreamer-basierte Extraktion
- 🔧 `get_thumbnail_path()` Methode mit MD5-Hash für eindeutige Cache-Dateinamen
- 📊 Automatische Cache-Verwaltung und Wiederverwendung bestehender Thumbnails

### Version 1.2.0 (Dezember 2025)
- ✨ **Chromecast-Untertitel** - Untertitel-Unterstützung für Chromecast-Wiedergabe (VTT-Format)
- ✨ **Chromecast-Audio-Tracks** - Auswahl von Audio-Spuren auf Remote-Gerät
- ✨ **Multi-Room-Audio** - Synchronisierte Wiedergabe auf mehreren Chromecast-Geräten
- ✨ **Chromecast-Gruppen** - Automatische Erkennung und Verbindung mit Gruppen
- ✨ **Erweiterte Status-Anzeige** - Ausklappbare Detailanzeige in Seitenleiste
- 📊 Echtzeit-Status: Gerätename, Modell, App, Wiedergabe-Status mit Icons
- 📊 Fortschritts-Anzeige in Prozent für Chromecast-Wiedergabe
- 🎵 Gruppen-Mitglieder-Anzeige bei Multi-Room-Wiedergabe
- 🔧 `enable_subtitles()` und `disable_subtitles()` Methoden
- 🔧 `set_audio_track()` für Audio-Spur-Wechsel
- 🔧 `get_extended_status()` mit 15+ Status-Informationen
- 🔧 `discover_cast_groups()` und `connect_to_group()` für Gruppen
- 🔧 `get_group_members()` zeigt alle Geräte in der Gruppe
- 🎨 Status-Icons: 🟢 PLAYING, 🟡 PAUSED, 🔵 BUFFERING, ⚪ IDLE
- 🎨 Automatische UI-Updates alle 250ms im Chromecast-Modus

### Version 1.1.0 (Dezember 2025)
- ✨ **Video-Rotation & Spiegelung** - Drehen (90°, 180°, 270°) und spiegeln (horizontal/vertikal)
- ✨ **Zoom & Crop** - Dynamisches Zoomen (0.5x-3.0x) und Zuschneiden des Videos
- ✨ **Gamma-Korrektur** - Erweiterte Helligkeitsanpassung (0.1-3.0)
- ✨ **Filter-Presets** - 10 vordefinierte Effekte (Sepia, Vintage, Schwarz-Weiß, Graustufen, Lebhaft, Hell, Dunkel, Kalt, Warm)
- 🎨 Neuer Video-Effekte-Button in Header-Bar mit Tab-Interface
- 🎯 Tab 1: Rotation & Spiegelung mit 6 Optionen
- 🎯 Tab 2: Zoom (0.5x-3.0x) und Crop (0-500px pro Seite)
- 🎯 Tab 3: Gamma-Korrektur und 10 Filter-Presets
- 🔄 Alle Effekte zurücksetzen-Button für schnellen Reset
- ⚡ GStreamer-Pipeline erweitert: videobalance → gamma → videoflip → videocrop → videoscale
- 💾 Echtzeit-Anwendung aller Effekte ohne Performance-Verlust
- 🎨 Preset-Synchronisation mit Equalizer-Einstellungen

### Version 1.0.9 (Dezember 2025)
- ✨ **YouTube Video Streaming** - Direkte Wiedergabe von YouTube-Videos über URL-Eingabe
- 🎬 YouTube-Button in Header-Bar für einfachen Zugriff
- 🔗 URL-Dialog zum Einfügen von YouTube-Links
- 📺 Unterstützung für lokale und Chromecast-Wiedergabe von YouTube-Inhalten
- ⚡ Automatische Video-Extraktion mit yt-dlp Integration
- 🎯 Nahtlose Integration in bestehende Playlist-Funktionalität

### Version 1.8.0 (Dezember 2025)
- ✨ **Go-To-Zeit** - Sprung zu bestimmter Zeitposition mit Dialog (MM:SS oder HH:MM:SS)
- ✨ **Kapitel-Erkennung** - Automatische Erkennung und Navigation von MKV/MP4 Kapiteln
- ✨ **Timeline-Thumbnails** - Vorschau-Bilder beim Hovern über Timeline mit intelligentem Caching
- 🎯 Go-To-Button in der Steuerungsleiste mit Sprung-Symbol
- 📑 Kapitel-Button in Header-Bar zeigt alle verfügbaren Kapitel
- 🖼️ Hover-Popover über Timeline mit 160x90 Thumbnail-Vorschau
- 🎮 Neue Tastaturverknüpfung: G für Go-To-Zeit Dialog
- ⚡ GStreamer TOC API für Kapitel-Extraktion
- 💾 Thumbnail-Cache für performante Vorschau-Anzeige

### Version 1.7.0 (Dezember 2025)
- ✨ **Video-Equalizer** - Echtzeit-Anpassung von Helligkeit, Kontrast, Sättigung und Farbton
- ✨ **A-B Loop** - Wiederholungsschleife zwischen zwei Punkten für Lern-Videos
- 🎨 Equalizer-Button in Header-Bar mit 4 Slidern und Reset-Funktion
- 🔄 A-B Loop Buttons (A, B, Clear) in der Kontrollleiste
- 🎮 Neue Tastaturverknüpfungen: A (Loop Start), B (Loop Ende), C (Loop löschen)
- 🎞️ Visuelle Markierung aktiver Loop-Punkte durch farbige Buttons
- ⚡ GStreamer videobalance Element für Hardware-beschleunigte Video-Anpassungen

### Version 1.6.0 (Dezember 2025)
- ✨ **Wiedergabegeschwindigkeit** - Einstellbare Geschwindigkeit von 0.5x bis 2.0x
- ✨ **Screenshot-Funktion** - Frame-Capture mit S-Taste, speichert in ~/Pictures/Video-Screenshots/
- 🎚️ Geschwindigkeits-Button in Header-Bar mit 6 vordefinierten Geschwindigkeiten
- 📸 Automatische Benennung von Screenshots mit Video-Name und Timestamp
- 🎮 Neue Tastaturverknüpfung: S für Screenshot

### Version 1.5.0 (Dezember 2025)
- ✨ **Audio-Track-Auswahl** - Wechsel zwischen mehreren Audio-Spuren bei mehrsprachigen Videos
- ✨ **Lesezeichen/Resume-Funktion** - Automatisches Speichern und Fortsetzen der Wiedergabe
- 🔧 Intelligentes Lesezeichen-System - Nur bei sinnvollen Positionen (nicht Anfang/Ende)
- 💬 Resume-Dialog beim Öffnen von Videos mit gespeicherter Position

### Version 1.4.0 (Dezember 2025)
- ✨ **Abspiellisten-Import** - M3U und PLS Format-Support

### Version 1.3.0 (Dezember 2025)
- ✨ **Tastatur-Shortcuts** - Steuerung per Leertaste, Pfeiltasten, etc.
- ✨ **Vollbild-Modus** - F11 für Vollbild-Wiedergabe
- ✨ **Drag & Drop** - Videos direkt ins Fenster ziehen
- ✨ **Video-Info-Overlay** - Zeigt Codec, Auflösung und Bitrate an
- ✨ **Untertitel-Support** - Automatische Erkennung von SRT, ASS, VTT Dateien

- ### Version 1.2.0 (Dezember 2025)
- ✨ **Playlist-Unterstützung** - Mehrere Videos in Warteschlange mit Auto-Advance
- ✨ **Drag & Drop** - Videos direkt ins Fenster ziehen (einzeln oder mehrere)
- ✨ Timeline/Seek-Funktion für lokale und Chromecast-Wiedergabe
- ✨ Lautstärkeregelung mit Slider für lokale und Chromecast-Wiedergabe
- ✨ NVIDIA Hardware-Beschleunigung (NVDEC/NVENC)
- 🐛 Verbesserte Chromecast-Kompatibilität (Xiaomi TVs)
- ⚡ Chromecast-Gerätesuche 30x schneller (500ms statt 15s)
- 🔧 Modus-Wechsel zwischen Lokal und Chromecast optimiert
- 🎚️ Automatische Lautstärke-Synchronisation beim Moduswechsel
- ⏭️ Previous/Next Video Buttons für Playlist-Navigation
- 🎵 Playlist-Verwaltung: Hinzufügen, Entfernen, Auswählen
- 🎨 Visuelles Feedback beim Drag-and-Drop (blaue Umrandung)


### Version 1.0.0 (Dezember 2025)
- 🎉 Erste Version
- ✨ AMD VA-API Hardware-Beschleunigung
- ✨ Automatische MKV/AVI zu MP4 Konvertierung
- ✨ GTK4/Libadwaita UI
- ✨ Chromecast-Streaming mit HTTP-Server

