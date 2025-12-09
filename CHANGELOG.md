# Changelog

Entwickelt von **DaHool** mit ❤️ für Simone

## Version 1.1.0 - 2025-12-08

### Neue Features

#### Automatische Video-Konvertierung
- **MKV/AVI zu MP4**: Der Player konvertiert automatisch inkompatible Video-Formate zu MP4 beim Chromecast-Streaming
- **Intelligentes Caching**: Konvertierte Videos werden in `~/.cache/video-chromecast-player/` gespeichert
- **Schnelle Konvertierung**: Nutzt FFmpeg mit Stream-Copy (ohne Re-Encoding) für maximale Geschwindigkeit
- **Fallback Re-Encoding**: Falls Stream-Copy nicht funktioniert, wird automatisch mit Re-Encoding konvertiert
- **Status-Anzeige**: Live-Updates in der UI während der Konvertierung

#### Verbessertes Debugging
- Detaillierte Logging-Ausgaben für alle Chromecast-Operationen
- HTTP-Server-Erreichbarkeitstests vor dem Streaming
- Automatische Port-Auswahl (8765-8888) falls Ports belegt sind
- Erweiterte Fehlerdiagnose mit Lösungsvorschlägen

#### Neue Hilfsskripte
- `fix-firewall.sh`: Automatische Firewall-Konfiguration für Chromecast
- `debug-chromecast.sh`: Umfassendes Diagnose-Tool für Chromecast-Probleme

#### UI-Verbesserungen
- Modernes App-Icon mit Video- und Cast-Symbol
- Desktop-Integration mit `.desktop` Datei
- Status-Updates während der Video-Konvertierung
- Informative Meldungen bei MKV/AVI-Dateien
- About-Dialog mit Entwickler-Informationen und GitHub-Link

### Behobene Probleme
- ✓ Chromecast-Discovery-Timeout erhöht (15 Sekunden)
- ✓ Verbesserte Fehlerbehandlung bei HTTP-Server-Start
- ✓ Standby-Inhibitor während Streaming
- ✓ Bessere Unterstützung für verschiedene Chromecast-Modelle
- ✓ Xiaomi TV Kompatibilität (automatisches Beenden aktiver Apps)
- ✓ Erweiterte Metadaten für besseres Streaming

### Technische Änderungen
- Neue `VideoConverter` Klasse für automatische Format-Konvertierung
- Cache-System mit MD5-basierter Identifikation
- Parallele Threads für Konvertierung ohne UI-Blockierung
- Erweiterte FFmpeg-Integration mit Fortschritts-Callbacks

## Version 1.0.0 - 2025-12-08

### Initiale Features
- GTK4/Libadwaita UI
- AMD Hardware-Beschleunigung (VA-API)
- Lokale Video-Wiedergabe mit GStreamer
- Chromecast-Discovery und Streaming
- HTTP-Server für Video-Streaming
- Vollständige Codec-Unterstützung via RPM Fusion
