#!/bin/bash
# Löscht den Konvertierungs-Cache

CACHE_DIR="$HOME/.cache/video-chromecast-player"

echo "=== Video Chromecast Player - Cache löschen ==="
echo ""

if [ ! -d "$CACHE_DIR" ]; then
    echo "✓ Cache-Verzeichnis existiert nicht, nichts zu löschen."
    exit 0
fi

echo "Cache-Verzeichnis: $CACHE_DIR"
echo ""

# Zeige Cache-Größe
if command -v du &>/dev/null; then
    SIZE=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
    echo "Aktuelle Cache-Größe: $SIZE"
fi

# Zeige Anzahl Dateien
FILE_COUNT=$(find "$CACHE_DIR" -type f 2>/dev/null | wc -l)
echo "Anzahl gecachte Videos: $FILE_COUNT"
echo ""

if [ $FILE_COUNT -eq 0 ]; then
    echo "✓ Cache ist bereits leer."
    exit 0
fi

# Liste Dateien auf
echo "Gecachte Videos:"
ls -lh "$CACHE_DIR"/*.mp4 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
echo ""

read -p "Möchtest du den Cache wirklich löschen? (j/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Jj]$ ]]; then
    rm -rf "$CACHE_DIR"
    echo "✓ Cache wurde gelöscht!"
    echo ""
    echo "Videos werden beim nächsten Mal neu konvertiert."
else
    echo "Abgebrochen."
fi
