#!/bin/bash
# Debugging-Skript für Chromecast-Probleme

echo "=== Chromecast Debugging ==="
echo ""

# 1. Netzwerk-Verbindung prüfen
echo "1. Netzwerk-Verbindung:"
echo "   Lokale IP-Adresse:"
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1
echo ""

# 2. Firewall-Status
echo "2. Firewall-Status:"
if systemctl is-active --quiet firewalld; then
    echo "   Firewalld ist aktiv"
    echo ""
    echo "   Offene Ports und Services:"
    sudo firewall-cmd --list-all | grep -E "(services|ports)"
    echo ""

    # Prüfe ob mDNS erlaubt ist
    if sudo firewall-cmd --list-services | grep -q mdns; then
        echo "   ✓ mDNS ist erlaubt (Chromecast-Suche funktioniert)"
    else
        echo "   ✗ mDNS ist NICHT erlaubt (Chromecast-Suche funktioniert NICHT)"
        echo "      Fix: sudo firewall-cmd --permanent --add-service=mdns && sudo firewall-cmd --reload"
    fi
    echo ""
else
    echo "   Firewalld ist nicht aktiv"
fi

# 3. Python-Abhängigkeiten prüfen
echo "3. Python-Abhängigkeiten:"
if python3 -c "import pychromecast" 2>/dev/null; then
    echo "   ✓ pychromecast ist installiert"
    python3 -c "import pychromecast; print(f'      Version: {pychromecast.__version__}')"
else
    echo "   ✗ pychromecast ist NICHT installiert"
    echo "      Fix: pip3 install --user pychromecast"
fi

if python3 -c "import zeroconf" 2>/dev/null; then
    echo "   ✓ zeroconf ist installiert"
else
    echo "   ✗ zeroconf ist NICHT installiert"
    echo "      Fix: pip3 install --user zeroconf"
fi
echo ""

# 4. Suche nach Chromecast-Geräten im Netzwerk
echo "4. Suche nach Chromecast-Geräten (mDNS):"
echo "   Suche läuft (10 Sekunden)..."
timeout 10 avahi-browse -t _googlecast._tcp 2>/dev/null | grep -E "^\+|hostname" || \
    echo "   ✗ Keine Geräte gefunden oder avahi-browse nicht installiert"
echo ""

# 5. Test: Einfacher HTTP-Server
echo "5. Test: HTTP-Server"
echo "   Versuche Port 8765..."
if nc -z 127.0.0.1 8765 2>/dev/null; then
    echo "   ✗ Port 8765 ist bereits belegt"
else
    echo "   ✓ Port 8765 ist verfügbar"
fi
echo ""

# 6. Empfohlene Schritte
echo "=== Empfohlene Schritte bei Problemen ==="
echo ""
echo "Problem: Chromecast wird nicht gefunden"
echo "  1. Stelle sicher, dass Computer und Chromecast im gleichen WLAN sind"
echo "  2. Führe fix-firewall.sh aus: ./fix-firewall.sh"
echo "  3. Starte den Chromecast neu (Strom ziehen)"
echo ""
echo "Problem: Streaming startet nicht"
echo "  1. Prüfe das Video-Format (MP4 wird am besten unterstützt)"
echo "  2. Konvertiere Videos: ffmpeg -i input.mkv -c:v libx264 -c:a aac output.mp4"
echo "  3. Stelle sicher, dass die Firewall HTTP-Ports erlaubt (8765-8888)"
echo "  4. Starte die App im Terminal für detaillierte Logs: ./videoplayer.py"
echo ""
echo "Problem: Verbindung zu 'Wohnzimmer 2' schlägt fehl"
echo "  1. Prüfe ob der Name korrekt ist (Leerzeichen, Sonderzeichen)"
echo "  2. Suche erneut nach Geräten (15 Sekunden warten)"
echo "  3. Prüfe in der Chromecast-App, ob das Gerät online ist"
echo ""
