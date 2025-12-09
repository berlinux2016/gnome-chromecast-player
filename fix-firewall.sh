#!/bin/bash
# Firewall-Konfiguration für Chromecast-Streaming

echo "=== Firewall-Konfiguration für Chromecast ==="
echo ""
echo "Dieses Skript öffnet die notwendigen Ports für Chromecast-Streaming."
echo ""

# Prüfe ob firewalld läuft
if ! systemctl is-active --quiet firewalld; then
    echo "Firewalld ist nicht aktiv. Keine Änderungen notwendig."
    exit 0
fi

echo "Aktuelle Firewall-Regeln:"
sudo firewall-cmd --list-all
echo ""

read -p "Möchtest du die Firewall-Regeln für Chromecast hinzufügen? (j/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Jj]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "Füge Firewall-Regeln hinzu..."

# mDNS für Chromecast-Discovery
echo "1. Erlaube mDNS (Chromecast-Suche)..."
sudo firewall-cmd --permanent --add-service=mdns

# Chromecast Kommunikation
echo "2. Erlaube Chromecast-Ports (8008-8009)..."
sudo firewall-cmd --permanent --add-port=8008-8009/tcp

# HTTP-Server Ports für Video-Streaming
echo "3. Erlaube HTTP-Server-Ports (8765-8888)..."
sudo firewall-cmd --permanent --add-port=8765-8888/tcp

# Firewall neu laden
echo "4. Lade Firewall-Regeln neu..."
sudo firewall-cmd --reload

echo ""
echo "✓ Firewall-Konfiguration abgeschlossen!"
echo ""
echo "Aktuelle Regeln:"
sudo firewall-cmd --list-all

echo ""
echo "Du kannst jetzt den Video Chromecast Player neu starten."
echo ""
