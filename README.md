# Video Chromecast Player

Ein moderner GTK4/Libadwaita-Videoplayer, der für eine nahtlose Wiedergabe sowohl lokal als auch auf Chromecast-Geräten optimiert ist. Inklusive Hardware-Beschleunigung, YouTube-Unterstützung und vielen Komfortfunktionen.

**Mit Liebe für Simone programmiert ❤️**

![Screenshot](https://raw.githubusercontent.com/berlinux2016/gnome-chromecast-player/main/screenshot.png)

## Features

### Wiedergabe & Steuerung
- **Lokale & Chromecast-Wiedergabe**: Nahtloser Wechsel zwischen der Wiedergabe auf dem Computer und einem Chromecast-Gerät.
- **Hardware-Beschleunigung**: Nutzt VA-API (AMD/Intel) und NVDEC (NVIDIA) für eine flüssige Wiedergabe von hochauflösenden Videos.
- **YouTube-Unterstützung**: Öffnen und streamen Sie YouTube-Videos direkt über die URL.
- **Umfassende Formatunterstützung**: Spielt alle gängigen Formate (MP4, WebM, etc.).
- **Automatische Konvertierung**: Konvertiert inkompatible Formate wie MKV und AVI automatisch und schnell im Hintergrund für das Chromecast-Streaming.
- **Wiedergabesteuerung**: Play, Pause, Stop, Spulen über die Timeline.
- **Wiedergabegeschwindigkeit**: Passen Sie die Geschwindigkeit von 0.5x bis 2.0x an.
- **Lautstärkeregelung**: Separate Lautstärkeregelung für lokalen und Chromecast-Modus.

### Komfortfunktionen
- **Playlist-Management**:
    - Erstellen, Speichern und Laden von Playlists.
    - Import von M3U- und PLS-Dateien.
    - Hinzufügen per Drag & Drop.
    - Mischen, Leeren und Entfernen von einzelnen Videos.
- **Lesezeichen (Resume)**: Merkt sich die letzte Wiedergabeposition und fragt beim erneuten Öffnen, ob die Wiedergabe fortgesetzt werden soll.
- **Timeline-Vorschau**: Zeigt Thumbnails an, wenn Sie mit der Maus über die Timeline fahren.
- **Kapitel-Navigation**: Erkennt und zeigt Kapitel aus MP4/MKV-Dateien an.
- **A-B Loop**: Definieren Sie eine Schleife zwischen zwei Zeitpunkten, ideal zum Lernen oder Analysieren von Szenen.
- **Go-To Time**: Springen Sie direkt zu einer bestimmten Zeit im Video.
- **Video-Equalizer**: Passen Sie Helligkeit, Kontrast, Sättigung und Farbton an.
- **Untertitel & Audio-Spuren**: Automatische Erkennung und einfache Auswahl von eingebetteten Untertiteln und mehreren Audio-Spuren.
- **Screenshot-Funktion**: Erstellen Sie mit der 'S'-Taste Screenshots, die automatisch gespeichert werden.
- **Picture-in-Picture (PiP)**: Schauen Sie Videos in einem kleinen, schwebenden Fenster.

### Integration & UI
- **Modernes GTK4/Libadwaita-Design**: Passt sich perfekt in den GNOME-Desktop ein.
- **Drag & Drop**: Ziehen Sie Videodateien einfach ins Fenster, um sie abzuspielen oder zur Playlist hinzuzufügen.
- **Tastatur-Shortcuts**: Vollständige Steuerung über die Tastatur (Leertaste, Pfeiltasten, M, F11 etc.).
- **Info-Overlay**: Zeigt auf Wunsch Informationen zu Codec, Auflösung und Bitrate an.
- **Standby-Verhinderung**: Verhindert den Ruhezustand des Computers während des Streamings.

## Installation

Dieses Programm ist für Linux-Systeme (insbesondere Fedora/GNOME) optimiert.

### 1. Abhängigkeiten installieren

Stellen Sie sicher, dass alle notwendigen Pakete installiert sind.

**Für Fedora:**
```bash
sudo dnf install python3-gobject python3-pip ffmpeg
```

**Zusätzlich für Hardware-Beschleunigung:**
- **AMD**: `sudo dnf install mesa-va-drivers`
- **NVIDIA**: `sudo dnf install nvidia-driver` (aus RPM Fusion)
- **Intel**: `sudo dnf install intel-media-driver`

### 2. Python-Bibliotheken installieren

Installieren Sie die benötigten Python-Pakete mit `pip`:

```bash
pip install pychromecast zeroconf yt-dlp
```

### 3. Anwendung ausführen

Navigieren Sie in das Verzeichnis, in dem sich die `videoplayer.py`-Datei befindet, und führen Sie sie aus:

```bash
python3 videoplayer.py
```

## Bedienung

### Chromecast-Streaming
1.  Klicken Sie auf das WLAN-Symbol in der Kopfleiste, um nach Geräten zu suchen.
2.  Wählen Sie Ihr Chromecast-Gerät aus der Liste in der Seitenleiste aus.
3.  Aktivieren Sie den "Chromecast"-Modus über den Schalter unten rechts.
4.  Öffnen Sie ein Video und drücken Sie auf "Play", um das Streaming zu starten.

### Tastatur-Shortcuts

| Taste(n)        | Aktion                               |
|-----------------|--------------------------------------|
| `Leertaste`     | Wiedergabe / Pause                    |
| `Pfeil Rechts`  | 5 Sekunden vorspulen                 |
| `Pfeil Links`   | 5 Sekunden zurückspulen              |
| `Pfeil Oben`    | Lauter                               |
| `Pfeil Unten`   | Leiser                               |
| `F11` oder `F`  | Vollbildmodus an/aus                 |
| `M`             | Stummschaltung an/aus                |
| `N`             | Nächstes Video in der Playlist       |
| `P`             | Vorheriges Video in der Playlist     |
| `S`             | Screenshot erstellen                 |
| `A`             | A-B Loop: Startpunkt setzen          |
| `B`             | A-B Loop: Endpunkt setzen            |
| `C`             | A-B Loop löschen                     |
| `G`             | Dialog "Zu Zeit springen" öffnen     |
| `I`             | Video-Info-Overlay dauerhaft ein/aus |

## Konfiguration

Die Anwendung speichert ihre Einstellungen automatisch in `~/.config/video-chromecast-player/`. Dazu gehören:
- `settings.json`: Fenstergröße, Lautstärke, letztes Verzeichnis etc.
- `playlist.json`: Die zuletzt geöffnete Playlist.
- `bookmarks.json`: Gespeicherte Wiedergabepositionen.

Der Cache für konvertierte Videos befindet sich in `~/.cache/video-chromecast-player/`.

---