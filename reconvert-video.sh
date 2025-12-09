#!/bin/bash
# Re-konvertiert ein Video mit optimierten Einstellungen für Xiaomi TV/Chromecast

if [ $# -eq 0 ]; then
    echo "Verwendung: $0 <video.mkv>"
    echo ""
    echo "Dieses Skript konvertiert ein Video mit optimierten Einstellungen"
    echo "für maximale Kompatibilität mit Xiaomi TVs und Chromecast."
    exit 1
fi

INPUT="$1"
if [ ! -f "$INPUT" ]; then
    echo "✗ Datei nicht gefunden: $INPUT"
    exit 1
fi

# Generiere Output-Dateinamen
BASENAME=$(basename "$INPUT" | sed 's/\.[^.]*$//')
OUTPUT="${BASENAME}_chromecast.mp4"

echo "=== Video-Konvertierung für Chromecast/Xiaomi TV ==="
echo "Eingabe: $INPUT"
echo "Ausgabe: $OUTPUT"
echo ""
echo "Diese Konvertierung kann mehrere Minuten dauern..."
echo ""

ffmpeg -i "$INPUT" \
    -c:v libx264 \
    -profile:v high \
    -level 4.1 \
    -preset faster \
    -crf 23 \
    -c:a aac \
    -b:a 192k \
    -ar 48000 \
    -ac 2 \
    -movflags +faststart \
    -f mp4 \
    -y \
    "$OUTPUT"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Konvertierung erfolgreich!"
    echo "  Ausgabe: $OUTPUT"
    SIZE=$(du -h "$OUTPUT" | cut -f1)
    echo "  Größe: $SIZE"
    echo ""
    echo "Du kannst jetzt diese Datei im Player öffnen und zu Chromecast streamen."
else
    echo ""
    echo "✗ Konvertierung fehlgeschlagen!"
    exit 1
fi
