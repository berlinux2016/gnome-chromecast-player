#!/usr/bin/env python3
"""
GTK4 Videoplayer mit Chromecast-Unterstützung und AMD Hardware-Beschleunigung (VA-API)
"""

import gi
import sys
import os
import threading
import time
import socket
import re
import subprocess
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gtk, Adw, Gst, GLib, GstVideo, Gdk, Gio
import pychromecast
from zeroconf import Zeroconf
from pychromecast.controllers.youtube import YouTubeController

Gst.init(None)

# GPU-Erkennung und Hardware-Beschleunigung
def detect_gpu():
    """Erkennt die GPU und setzt entsprechende Umgebungsvariablen"""
    try:
        # Prüfe auf NVIDIA GPU
        nvidia_check = subprocess.run(['nvidia-smi', '-L'],
                                     capture_output=True,
                                     text=True,
                                     timeout=2)
        if nvidia_check.returncode == 0 and 'GPU' in nvidia_check.stdout:
            print("✓ NVIDIA GPU erkannt")
            os.environ['VDPAU_DRIVER'] = 'nvidia'
            # NVIDIA nutzt VDPAU und NVDEC
            return 'nvidia'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        # Prüfe auf AMD GPU
        lspci_check = subprocess.run(['lspci'],
                                     capture_output=True,
                                     text=True,
                                     timeout=2)
        if 'AMD' in lspci_check.stdout or 'Radeon' in lspci_check.stdout:
            print("✓ AMD GPU erkannt")
            os.environ['LIBVA_DRIVER_NAME'] = 'radeonsi'
            os.environ['VDPAU_DRIVER'] = 'radeonsi'
            return 'amd'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback zu AMD (Standard)
    print("ℹ Keine spezifische GPU erkannt, nutze AMD-Einstellungen")
    os.environ['LIBVA_DRIVER_NAME'] = 'radeonsi'
    os.environ['VDPAU_DRIVER'] = 'radeonsi'
    return 'unknown'

GPU_TYPE = detect_gpu()


class VideoConverter:
    """Automatische Video-Konvertierung für Chromecast-Kompatibilität"""

    def __init__(self):
        self.conversion_cache_dir = Path.home() / ".cache" / "video-chromecast-player"
        self.conversion_cache_dir.mkdir(parents=True, exist_ok=True)
        self.active_conversions = {}

    def get_cached_mp4_path(self, mkv_path):
        """Generiert Pfad für konvertierte MP4-Datei im Cache"""
        mkv_file = Path(mkv_path)
        # Nutze Hash des Original-Pfads + Dateiname für eindeutigen Cache-Key
        import hashlib
        path_hash = hashlib.md5(str(mkv_file.absolute()).encode()).hexdigest()[:8]
        mp4_name = f"{mkv_file.stem}_{path_hash}.mp4"
        return self.conversion_cache_dir / mp4_name

    def is_ffmpeg_available(self):
        """Prüft ob FFmpeg installiert ist"""
        try:
            subprocess.run(['ffmpeg', '-version'],
                         capture_output=True,
                         check=True,
                         timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def convert_to_mp4(self, input_path, progress_callback=None):
        """
        Konvertiert MKV zu MP4 (schnell, ohne Re-Encoding wenn möglich)
        Returns: Pfad zur MP4-Datei oder None bei Fehler
        """
        input_file = Path(input_path)
        output_path = self.get_cached_mp4_path(input_path)

        # Prüfe ob bereits konvertiert und aktuell
        if output_path.exists():
            # Prüfe ob Cache-Datei neuer ist als Original
            if output_path.stat().st_mtime >= input_file.stat().st_mtime:
                print(f"✓ Nutze bereits konvertierte Datei: {output_path.name}")
                return str(output_path)
            else:
                print(f"Cache veraltet, konvertiere neu...")
                output_path.unlink()

        if not self.is_ffmpeg_available():
            print("✗ FFmpeg ist nicht installiert!")
            print("  Installation: sudo dnf install ffmpeg")
            return None

        print(f"\n=== Automatische Video-Konvertierung ===")
        print(f"Eingabe: {input_file.name}")
        print(f"Ausgabe: {output_path.name}")
        print(f"Methode: Schnelle Konvertierung (ohne Re-Encoding)")
        print(f"Cache-Verzeichnis: {self.conversion_cache_dir}")

        if progress_callback:
            GLib.idle_add(progress_callback, "Konvertiere Video zu MP4...")

        try:
            # Versuche zuerst schnelle Konvertierung ohne Re-Encoding
            cmd = [
                'ffmpeg',
                '-i', str(input_file),
                '-c', 'copy',  # Kopiere Streams ohne Re-Encoding
                '-movflags', '+faststart',  # Optimiere für Streaming
                '-y',  # Überschreibe falls vorhanden
                str(output_path)
            ]

            print(f"Führe aus: {' '.join(cmd)}")
            print("Bitte warten, dies kann einige Sekunden dauern...")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Warte auf Abschluss
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"✓ Konvertierung erfolgreich!")
                print(f"  Dateigröße: {output_path.stat().st_size / (1024*1024):.1f} MB")
                if progress_callback:
                    GLib.idle_add(progress_callback, "Konvertierung abgeschlossen!")
                return str(output_path)
            else:
                print(f"✗ Schnelle Konvertierung fehlgeschlagen, versuche Re-Encoding...")
                print(f"  FFmpeg Fehler: {stderr[:500]}")

                # Fallback: Mit Re-Encoding (langsamer aber sicherer)
                return self.convert_with_reencoding(input_file, output_path, progress_callback)

        except Exception as e:
            print(f"✗ Konvertierungsfehler: {e}")
            import traceback
            traceback.print_exc()
            if output_path.exists():
                output_path.unlink()
            if progress_callback:
                GLib.idle_add(progress_callback, f"Fehler: {e}")
            return None

    def convert_with_reencoding(self, input_file, output_path, progress_callback=None):
        """Konvertiert mit Re-Encoding (garantierte Kompatibilität)"""
        print("\n=== Re-Encoding für garantierte Kompatibilität ===")

        # Wähle Video-Encoder basierend auf GPU (nur Hardware-Encoder!)
        video_codec = None
        video_params = None

        if GPU_TYPE == 'nvidia':
            print("Nutze NVIDIA NVENC Hardware-Encoding...")
            video_codec = 'h264_nvenc'
            video_params = [
                '-c:v', 'h264_nvenc',
                '-preset', 'p4',  # NVENC Preset (p1-p7, p4 = balanced)
                '-profile:v', 'high',
                '-level', '4.1',
                '-b:v', '5M',  # Bitrate 5 Mbps
                '-maxrate', '8M',
                '-bufsize', '10M',
            ]
            print("  ✓ Encoder: NVIDIA NVENC (Hardware-beschleunigt)")

        elif GPU_TYPE == 'amd':
            print("Nutze AMD VAAPI Hardware-Encoding...")
            # Prüfe ob VAAPI Encoding verfügbar ist
            try:
                vaapi_check = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'],
                                            capture_output=True, text=True, timeout=5)
                if 'h264_vaapi' in vaapi_check.stdout:
                    video_codec = 'h264_vaapi'
                    video_params = [
                        '-vaapi_device', '/dev/dri/renderD128',
                        '-c:v', 'h264_vaapi',
                        '-profile:v', 'high',
                        '-level', '4.1',
                        '-qp', '23',
                    ]
                    print("  ✓ Encoder: AMD VAAPI (Hardware-beschleunigt)")
                else:
                    print("  ✗ AMD VAAPI Encoder nicht verfügbar")
                    video_codec = None
            except Exception as e:
                print(f"  ✗ Fehler beim Prüfen von VAAPI: {e}")
                video_codec = None

        # Keine Hardware-Beschleunigung verfügbar
        if video_codec is None:
            error_msg = (
                "❌ Hardware-Beschleunigung nicht verfügbar!\n\n"
                "Dieses Programm benötigt Hardware-Encoding für MKV/AVI Konvertierung.\n\n"
                "Bitte stelle sicher, dass:\n"
                "• Eine kompatible GPU installiert ist (AMD mit VAAPI oder NVIDIA mit NVENC)\n"
                "• Die entsprechenden Treiber installiert sind\n"
                "• FFmpeg mit Hardware-Unterstützung installiert ist\n\n"
                "Für AMD: sudo dnf install mesa-va-drivers ffmpeg\n"
                "Für NVIDIA: sudo dnf install nvidia-driver ffmpeg\n\n"
                "Alternative: Konvertiere die Datei manuell zu MP4 und lade dann die MP4-Datei."
            )
            print("\n" + error_msg)
            if progress_callback:
                GLib.idle_add(progress_callback, "Hardware-Encoding nicht verfügbar")
            return None

        print("Dies kann einige Minuten dauern...")

        if progress_callback:
            GLib.idle_add(progress_callback, f"Re-Encoding läuft ({video_codec})...")

        try:
            cmd = [
                'ffmpeg',
                '-i', str(input_file),
            ]

            # Füge Video-Codec-Parameter hinzu
            cmd.extend(video_params)

            # Audio-Codec (immer gleich)
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '192k',
                '-ar', '48000',
                '-ac', '2',
                # MP4-Optimierungen
                '-movflags', '+faststart',
                '-f', 'mp4',
                '-y',
                str(output_path)
            ])

            print(f"Führe aus: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"✓ Re-Encoding erfolgreich!")
                print(f"  Dateigröße: {output_path.stat().st_size / (1024*1024):.1f} MB")
                if progress_callback:
                    GLib.idle_add(progress_callback, "Re-Encoding abgeschlossen!")
                return str(output_path)
            else:
                print(f"✗ Re-Encoding fehlgeschlagen: {stderr[:500]}")
                if output_path.exists():
                    output_path.unlink()
                return None

        except Exception as e:
            print(f"✗ Re-Encoding Fehler: {e}")
            if output_path.exists():
                output_path.unlink()
            return None


class VideoHTTPServer:
    """Einfacher HTTP-Server für Video-Streaming zu Chromecast"""

    def __init__(self):
        self.server = None
        self.server_thread = None
        self.port = 8765
        self.current_video_path = None

    def get_local_ip(self):
        """Ermittelt die lokale IP-Adresse"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start_server(self, video_path):
        """Startet HTTP-Server für ein Video"""
        if self.server:
            self.stop_server()

        self.current_video_path = video_path
        video_dir = str(Path(video_path).parent)

        class RangeRequestHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                # Zeige HTTP-Logs für Debugging
                print(f"HTTP: {format % args}")

            def handle(self):
                """Überschreibe handle() für besseres Error-Handling"""
                try:
                    super().handle()
                except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError) as e:
                    # Chromecast hat Verbindung getrennt (z.B. Stop gedrückt)
                    print(f"HTTP-Verbindung geschlossen: {e}")
                except Exception as e:
                    print(f"HTTP-Server Fehler: {e}")
                    import traceback
                    traceback.print_exc()
            
            def do_GET(self):
                """Behandelt GET-Anfragen mit Unterstützung für Range-Header."""
                range_header = self.headers.get('Range')
                if not range_header:
                    # Keine Range-Anfrage, verhalte dich wie normal
                    super().do_GET()
                    return

                try:
                    filepath = self.translate_path(self.path)
                    with open(filepath, 'rb') as f:
                        fs = os.fstat(f.fileno())
                        file_len = fs.st_size
                        
                        # Parse Range Header
                        byte1, byte2 = 0, None
                        m = re.match(r'bytes=(\d+)-(\d*)', range_header)
                        if m:
                            byte1 = int(m.group(1))
                            if m.group(2):
                                byte2 = int(m.group(2))

                        if byte2 is None:
                            byte2 = file_len - 1

                        # Ungültige Range
                        if byte1 >= file_len or byte2 >= file_len:
                            self.send_error(416, 'Requested Range Not Satisfiable')
                            return

                        self.send_response(206) # Partial Content
                        self.send_header('Content-type', self.guess_type(self.path))
                        self.send_header('Accept-Ranges', 'bytes')
                        
                        content_range = f'bytes {byte1}-{byte2}/{file_len}'
                        self.send_header('Content-Range', content_range)
                        self.send_header('Content-Length', str(byte2 - byte1 + 1))
                        self.end_headers()

                        f.seek(byte1)
                        chunk_size = 65536 # 64KB
                        bytes_to_send = byte2 - byte1 + 1
                        while bytes_to_send > 0:
                            data = f.read(min(chunk_size, bytes_to_send))
                            if not data:
                                break
                            self.wfile.write(data)
                            bytes_to_send -= len(data)
                except Exception as e:
                    print(f"Fehler bei Range-Request: {e}")
                    # Fallback auf normales Verhalten
                    f = self.send_head()
                    if f:
                        try:
                            self.copyfile(f, self.wfile)
                        finally:
                            f.close()

            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=video_dir, **kwargs)


        try:
            # Versuche mehrere Ports, falls 8765 belegt ist
            ports_to_try = [self.port, 8766, 8767, 8768, 8080, 8888]
            server_started = False


            for port in ports_to_try:
                try:
                    self.port = port
                    self.server = HTTPServer(('0.0.0.0', self.port), RangeRequestHandler)
                    self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                    self.server_thread.start()
                    print(f"✓ HTTP-Server gestartet auf Port {self.port}")

                    # Kurze Wartezeit, um dem Server Zeit zum Binden zu geben
                    time.sleep(0.1)
                    # Überprüfe, ob der Server-Thread noch läuft
                    if not self.server_thread.is_alive():
                        raise OSError("Server-Thread konnte nicht gestartet werden.")

                    print(f"  Lokale IP: {self.get_local_ip()}")
                    print(f"  Video-Verzeichnis: {video_dir}")
                    server_started = True
                    break
                except OSError as e:
                    if "Address already in use" in str(e):
                        print(f"✗ Port {port} bereits belegt, versuche nächsten Port...")
                        continue
                    else:
                        raise

            if not server_started:
                raise Exception("Alle Ports sind belegt")

            return True
        except Exception as e:
            print(f"✗ Fehler beim Starten des HTTP-Servers: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_video_url(self, video_path):
        """Gibt die HTTP-URL für ein Video zurück"""
        if not self.server:
            if not self.start_server(video_path):
                return None

        local_ip = self.get_local_ip()
        video_filename = Path(video_path).name
        url = f"http://{local_ip}:{self.port}/{quote(video_filename)}"
        return url

    def stop_server(self):
        """Stoppt den HTTP-Server"""
        if self.server:
            self.server.shutdown()
            self.server = None
            self.server_thread = None
            print("HTTP-Server gestoppt")


class ChromecastManager:
    """Verwaltet Chromecast-Geräte und Streaming"""

    def __init__(self):
        self.chromecasts = []
        self.selected_cast = None
        self.mc = None
        self._discovery_browser = None
        self._listener = None
        self._zconf_instance = None
        self._found_devices = {} # UUID -> Service

    def discover_chromecasts(self, callback):
        """Sucht nach verfügbaren Chromecast-Geräten"""
        if self._discovery_browser:
            print("ℹ Chromecast-Suche läuft bereits.")
            # Sofort die bereits gefundenen Geräte zurückgeben
            callback(list(self._found_devices.values()))
            return

        print("=== Starte asynchrone Chromecast-Suche ===")
        print("Geräte werden angezeigt, sobald sie gefunden werden...")

        def add_callback(uuid, name):
            """Wird aufgerufen, wenn ein neues Gerät gefunden wird."""
            # pychromecast.get_chromecast_from_service braucht den service
            # Wir holen ihn uns aus dem listener
            service = self._listener.services[uuid]
            print(f"✓ Gerät gefunden: {service.friendly_name} ({service.model_name})")
            self._found_devices[uuid] = service
            self.chromecasts = list(self._found_devices.values())
            GLib.idle_add(callback, self.chromecasts)

        def remove_callback(uuid, name, service):
            """Wird aufgerufen, wenn ein Gerät aus dem Netzwerk verschwindet."""
            print(f"✗ Gerät entfernt: {name}")
            if uuid in self._found_devices:
                del self._found_devices[uuid]
                self.chromecasts = list(self._found_devices.values())
                GLib.idle_add(callback, self.chromecasts)

        # Listener erstellen
        self._listener = pychromecast.CastListener(add_callback, remove_callback)

        # Erstelle eine Zeroconf-Instanz, falls noch keine existiert
        if self._zconf_instance is None:
            self._zconf_instance = Zeroconf()

        # Asynchrone Suche starten
        self._discovery_browser = pychromecast.discovery.start_discovery(self._listener, self._zconf_instance)

        # Nach 3 Sekunden eine Meldung ausgeben, falls nichts gefunden wurde
        def check_if_any_found():
            if not self._found_devices:
                print("\n✗ Nach 3 Sekunden noch keine Geräte gefunden.")
                print("  Mögliche Ursachen:")
                print("  - Chromecast und Computer sind nicht im gleichen WLAN")
                print("  - Firewall blockiert mDNS (Port 5353/udp)")
                print("  - Chromecast ist nicht eingeschaltet")
            return False # Nur einmal ausführen

        GLib.timeout_add_seconds(3, check_if_any_found)

    def connect_to_chromecast(self, service):
        """Verbindet mit einem Chromecast-Gerät"""
        try:
            print(f"\n=== Verbinde mit '{service.friendly_name}' ===")
            print(f"Host: {service.host}:{service.port}")

            # Erstelle das Chromecast-Objekt direkt aus den Host-Informationen des
            # gefundenen Service. Dies ist der zuverlässigste Weg, da er keine neue
            # Suche startet und die bestehende Zeroconf-Instanz korrekt weiterverwendet.
            # Die Funktion get_chromecast_from_host ist für ältere pychromecast-Versionen.
            self.selected_cast = pychromecast.get_chromecast_from_host(
                (service.host, service.port, service.uuid, service.model_name, service.friendly_name),
            )

            if not self.selected_cast:
                print(f"✗ Gerät '{service.friendly_name}' konnte nicht verbunden werden.")
                return False

            print("Warte auf Verbindung...")
            self.selected_cast.wait()  # Warte, bis die Verbindung aktiv ist

            print(f"✓ Erfolgreich verbunden mit '{service.friendly_name}'")
            print(f"  Status: {self.selected_cast.status}")
            print(f"  App: {self.selected_cast.app_display_name}")
            return True

        except Exception as e:
            print(f"✗ Verbindungsfehler zu '{service.friendly_name}': {e}")
            import traceback
            traceback.print_exc()
        return False

    def play_video(self, video_path, video_url):
        """Spielt Video auf Chromecast ab"""
        if not self.selected_cast:
            print("✗ Kein Chromecast-Gerät ausgewählt")
            return False

        try:
            print(f"\n=== Starte Streaming ===")
            print(f"Video: {Path(video_path).name}")
            print(f"URL: {video_url}")

            # Prüfe ob eine andere App aktiv ist (wichtig für Xiaomi TVs)
            if self.selected_cast.app_id and self.selected_cast.app_id != 'CC1AD845':
                print(f"ℹ Aktive App erkannt: {self.selected_cast.app_display_name} ({self.selected_cast.app_id})")
                print("  Beende aktive App für Chromecast-Streaming...")
                try:
                    self.selected_cast.quit_app()
                    # Warte kurz bis App beendet ist
                    time.sleep(2)
                    print("  ✓ App beendet")
                except Exception as e:
                    print(f"  ⚠ Konnte App nicht beenden: {e}")

            self.mc = self.selected_cast.media_controller

            # Video-Typ bestimmen
            mime_type = 'video/mp4'

            if video_path.lower().endswith('.mkv'):
                mime_type = 'video/x-matroska'
                print("ℹ MKV-Format (sollte bereits zu MP4 konvertiert worden sein)")
            elif video_path.lower().endswith('.avi'):
                mime_type = 'video/x-msvideo'
                print("ℹ AVI-Format (sollte bereits zu MP4 konvertiert worden sein)")
            elif video_path.lower().endswith('.webm'):
                mime_type = 'video/webm'
                print("✓ WebM wird unterstützt")
            elif video_path.lower().endswith(('.mp4', '.m4v')):
                mime_type = 'video/mp4'
                print("✓ MP4 - vollständig unterstützt")
            else:
                print(f"ℹ Unbekanntes Video-Format, versuche als MP4...")

            print(f"MIME-Type: {mime_type}")

            # Teste HTTP-Server Erreichbarkeit
            print("\nTeste HTTP-Server Erreichbarkeit...")
            import urllib.request
            try:
                req = urllib.request.Request(video_url, method='HEAD')
                urllib.request.urlopen(req, timeout=5)
                print("✓ HTTP-Server ist erreichbar")
            except Exception as e:
                print(f"✗ HTTP-Server nicht erreichbar: {e}")
                print("  Überprüfe Firewall-Einstellungen!")
                return False

            print("\nStarte Chromecast-Wiedergabe...")

            # Erweiterte Metadaten für bessere Kompatibilität mit Xiaomi TVs
            video_title = Path(video_path).stem
            metadata = {
                'metadataType': 0,  # GenericMediaMetadata
                'title': video_title,
                'contentType': mime_type
            }

            print(f"  Titel: {video_title}")
            print(f"  Content-Type: {mime_type}")

            # Starte Wiedergabe mit Metadaten
            self.mc.play_media(
                video_url,
                mime_type,
                title=video_title,
                autoplay=True,
                current_time=0
            )

            # Warte auf Status-Update
            print("  Warte auf Chromecast-Antwort...")
            self.mc.block_until_active(timeout=10)

            # Robuste Überprüfung, ob die Wiedergabe wirklich startet (wichtig für Xiaomi TV)
            for attempt in range(10):  # Versuche es bis zu 10 Sekunden lang
                time.sleep(1) # Warte eine Sekunde zwischen den Prüfungen
                self.selected_cast.media_controller.update_status()
                status = self.mc.status.player_state

                if status in ("PLAYING", "BUFFERING"):
                    print(f"✓ Streaming erfolgreich gestartet!")
                    print(f"  Status: {status}")
                    if self.mc.status.duration:
                        print(f"  Dauer: {self.mc.status.duration} Sekunden")
                    return True
                elif status == "IDLE":
                    print(f"  Versuch {attempt + 1}/10: Status ist IDLE, warte weiter...")
                    # Manchmal hilft ein erneuter Play-Befehl
                    if attempt == 3:
                        print("  ... sende erneuten Play-Befehl als 'Anstoß'.")
                        self.mc.play()
                else:
                    print(f"  Versuch {attempt + 1}/10: Status ist {status}, warte...")

            print("✗ Wiedergabe konnte nicht gestartet werden. Status bleibt IDLE/UNKNOWN.")
            return False
        except Exception as e:
            print(f"\n✗ Streaming fehlgeschlagen: {e}")
            print("\nMögliche Ursachen:")
            print("  1. Firewall blockiert HTTP-Verbindung")
            print("  2. Video-Format wird nicht unterstützt (verwende MP4)")
            print("  3. Netzwerkprobleme zwischen Computer und Chromecast")
            print("  4. Video-Codec wird nicht unterstützt")
            print("\nFirewall öffnen:")
            print(f"  sudo firewall-cmd --permanent --add-port={self.http_server.port if hasattr(self, 'http_server') else '8765'}/tcp")
            print("  sudo firewall-cmd --reload")
            import traceback
            traceback.print_exc()
            return False

    def pause(self):
        if self.mc:
            self.mc.pause()

    def play(self):
        if self.mc:
            self.mc.play()

    def stop(self):
        if self.mc:
            self.mc.stop()

    def get_position(self):
        """Gibt Chromecast-Position in Sekunden zurück"""
        if self.mc and self.mc.status:
            return self.mc.status.current_time or 0.0
        return 0.0

    def get_duration(self):
        """Gibt Chromecast-Dauer in Sekunden zurück"""
        if self.mc and self.mc.status:
            return self.mc.status.duration or 0.0
        return 0.0

    def seek(self, position_seconds):
        """Springt zu Position auf Chromecast"""
        if self.mc and self.selected_cast:
            try:
                print(f"Chromecast: Seeking to {position_seconds:.1f}s")
                # Warte kurz auf Chromecast-Bereitschaft
                self.selected_cast.wait()
                # Seek-Befehl senden
                self.mc.seek(position_seconds)
                # Status aktualisieren
                time.sleep(0.1)
                self.mc.update_status()
                print(f"✓ Chromecast: Seek erfolgreich zu {position_seconds:.1f}s")
            except Exception as e:
                print(f"✗ Chromecast seek error: {e}")
                import traceback
                traceback.print_exc()

    def update_status(self):
        """Aktualisiert Chromecast-Status (nötig für Position-Abfragen)"""
        if self.selected_cast and self.mc:
            try:
                self.selected_cast.media_controller.update_status()
            except Exception as e:
                print(f"Status update error: {e}")

    def disconnect(self):
        if self.selected_cast:
            self.selected_cast.disconnect()
            self.selected_cast = None
            self.mc = None

        # Stoppe den ursprünglichen Discovery-Browser, der die ganze Zeit lief.
        if self._discovery_browser:
            pychromecast.discovery.stop_discovery(self._discovery_browser)
            self._discovery_browser = None
        
        # Schließe die Zeroconf-Instanz
        if self._zconf_instance:
            self._zconf_instance.close()
            self._zconf_instance = None


class VideoPlayer(Gtk.Box):
    """Video-Player-Widget mit GStreamer und Hardware-Beschleunigung"""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # GStreamer Pipeline mit Hardware-Beschleunigung
        self.playbin = Gst.ElementFactory.make("playbin", "player")

        # Hardware-Beschleunigung aktivieren
        self.setup_hardware_acceleration()

        # Video-Ausgabe
        self.video_widget = Gtk.Picture()
        self.video_widget.set_size_request(800, 450)
        self.video_widget.set_vexpand(True)
        self.video_widget.set_hexpand(True)

        # Video-Sink für GTK
        self.gtksink = Gst.ElementFactory.make("gtk4paintablesink", "sink")
        paintable = self.gtksink.get_property("paintable")
        self.video_widget.set_paintable(paintable)
        self.playbin.set_property("video-sink", self.gtksink)

        self.append(self.video_widget)

        # Bus für Nachrichten
        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_gst_message)

        self.current_file = None
        self.hw_accel_enabled = False

    def setup_hardware_acceleration(self):
        """Konfiguriert Hardware-Beschleunigung (AMD VA-API / NVIDIA NVDEC)"""
        try:
            hw_decoder = None

            if GPU_TYPE == 'nvidia':
                # NVIDIA NVDEC Hardware-Beschleunigung
                nvdec = Gst.ElementFactory.find("nvdec")
                nvh264dec = Gst.ElementFactory.find("nvh264dec")

                if nvdec or nvh264dec:
                    hw_decoder = 'nvdec'
                    print("✓ Hardware-Beschleunigung (NVIDIA NVDEC) aktiviert")
                else:
                    print("⚠ NVDEC nicht verfügbar, prüfe ob gstreamer1-plugins-bad installiert ist")

            elif GPU_TYPE == 'amd':
                # AMD VA-API Hardware-Beschleunigung
                vaapi_dec = Gst.ElementFactory.find("vaapidecodebin")
                if vaapi_dec:
                    hw_decoder = 'vaapi'
                    print("✓ Hardware-Beschleunigung (AMD VA-API) aktiviert")
                else:
                    print("⚠ VA-API nicht verfügbar, prüfe ob gstreamer1-vaapi installiert ist")

            if hw_decoder:
                # Setze Hardware-Decoder-Präferenz
                flags = self.playbin.get_property("flags")
                # Aktiviere Hardware-Dekodierung
                flags |= (1 << 0)  # GST_PLAY_FLAG_VIDEO
                flags |= (1 << 9)  # GST_PLAY_FLAG_NATIVE_VIDEO
                self.playbin.set_property("flags", flags)
                self.hw_accel_enabled = True
            else:
                print("ℹ Nutze Software-Dekodierung")
                self.hw_accel_enabled = False

        except Exception as e:
            print(f"✗ Fehler bei Hardware-Beschleunigung Setup: {e}")
            print("  Falle zurück auf Software-Dekodierung")
            self.hw_accel_enabled = False

    def load_video(self, filepath):
        """Lädt eine Video-Datei"""
        self.current_file = filepath
        uri = f"file://{filepath}"
        print(f"Lade Video lokal: {filepath}")
        self.playbin.set_state(Gst.State.NULL)
        self.playbin.set_property("uri", uri)
        self.playbin.set_state(Gst.State.PAUSED)
        print("Video geladen, Status: PAUSED")

    def play(self):
        self.playbin.set_state(Gst.State.PLAYING)

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)

    def stop(self):
        self.playbin.set_state(Gst.State.NULL)

    def on_gst_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"GStreamer Fehler: {err}, {debug}")
        elif t == Gst.MessageType.EOS:
            self.playbin.set_state(Gst.State.NULL)

    def get_position(self):
        """Gibt aktuelle Position in Sekunden zurück"""
        success, position = self.playbin.query_position(Gst.Format.TIME)
        if success:
            return position / Gst.SECOND
        return 0.0

    def get_duration(self):
        """Gibt Gesamtdauer in Sekunden zurück"""
        success, duration = self.playbin.query_duration(Gst.Format.TIME)
        if success:
            return duration / Gst.SECOND
        return 0.0

    def seek(self, position_seconds):
        """Springt zu einer Position (in Sekunden)"""
        position_ns = position_seconds * Gst.SECOND

        # Nutze ACCURATE für präziseres Seeking, besonders bei MKV-Dateien.
        # KEY_UNIT ist schneller, aber oft unzuverlässig.
        # FLUSH ist wichtig, um alte Daten aus der Pipeline zu entfernen.
        self.playbin.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            position_ns
        )
        print(f"Lokales Seeking zu {position_seconds:.1f}s (präzise)")


class VideoPlayerWindow(Adw.ApplicationWindow):
    """Hauptfenster der Anwendung"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Video Chromecast Player")
        self.set_default_size(1000, 700)

        # Chromecast Manager, HTTP-Server und Video-Converter
        self.cast_manager = ChromecastManager()
        self.http_server = VideoHTTPServer()
        self.video_converter = VideoConverter()
        self.current_video_path = None

        # Standby-Inhibitor (verhindert Standby während Streaming)
        self.inhibit_cookie = None

        # Cleanup beim Schließen
        self.connect("close-request", self.on_close_request)

        # Hauptlayout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header Bar
        self.setup_header_bar()

        # Content Box
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)

        # Video Player
        self.video_player = VideoPlayer()
        content_box.append(self.video_player)

        # Seitenleiste für Chromecast
        self.setup_sidebar()
        content_box.append(self.sidebar)

        self.main_box.append(content_box)

        # Timeline/Seek Bar
        timeline_widget = self.setup_timeline()
        self.main_box.append(timeline_widget)

        # Kontrollleiste
        self.setup_controls()
        self.main_box.append(self.control_box)

        self.set_content(self.main_box)

        # Spiele-Modus (lokal oder chromecast)
        self.play_mode = "local"  # oder "chromecast"
        
        # Timeline state tracking
        self.timeline_update_timeout = None
        self.is_seeking = False

    def setup_header_bar(self):
        """Erstellt die Header Bar"""
        header = Adw.HeaderBar()

        # Datei öffnen Button
        open_button = Gtk.Button()
        open_button.set_icon_name("document-open-symbolic")
        open_button.set_tooltip_text("Video öffnen")
        open_button.connect("clicked", self.on_open_file)
        header.pack_start(open_button)

        # About Button
        about_button = Gtk.Button()
        about_button.set_icon_name("help-about-symbolic")
        about_button.set_tooltip_text("Über")
        about_button.connect("clicked", self.on_show_about)
        header.pack_end(about_button)

        # Chromecast suchen Button
        scan_button = Gtk.Button()
        scan_button.set_icon_name("network-wireless-symbolic")
        scan_button.set_tooltip_text("Chromecast-Geräte suchen")
        scan_button.connect("clicked", self.on_scan_chromecasts)
        header.pack_end(scan_button)

        self.main_box.append(header)

    def setup_sidebar(self):
        """Erstellt die Seitenleiste für Chromecast"""
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.sidebar.set_size_request(250, -1)

        # Überschrift
        label = Gtk.Label(label="Chromecast-Geräte")
        label.add_css_class("title-2")
        self.sidebar.append(label)

        # Scrollbarer Bereich für Geräte
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.device_list = Gtk.ListBox()
        self.device_list.add_css_class("boxed-list")
        self.device_list.connect("row-activated", self.on_device_selected)

        scrolled.set_child(self.device_list)
        self.sidebar.append(scrolled)

        # Status Label
        self.status_label = Gtk.Label(label="Keine Geräte gefunden")
        self.status_label.add_css_class("dim-label")
        self.sidebar.append(self.status_label)

    def setup_timeline(self):
        """Erstellt Timeline mit Zeit-Labels"""
        timeline_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        timeline_box.set_margin_start(12)
        timeline_box.set_margin_end(12)
        timeline_box.set_margin_bottom(6)

        # Zeit-Label links (aktuelle Position)
        self.time_label = Gtk.Label(label="00:00")
        self.time_label.set_width_chars(6)
        self.time_label.add_css_class("monospace")
        timeline_box.append(self.time_label)

        # Timeline-Slider (0-100 = Prozent)
        self.timeline_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self.timeline_scale.set_hexpand(True)
        self.timeline_scale.set_draw_value(False)
        self.timeline_scale.set_sensitive(False)  # Deaktiviert bis Video geladen

        # Korrekte Event-Handler für Seeking
        # 'change-value' wird ausgelöst, wenn der Benutzer den Slider bewegt
        # Das 'format-value' Signal wird entfernt, da es erst ab GTK 4.2 verfügbar ist.
        self.timeline_scale.connect("change-value", self.on_timeline_seek)

        timeline_box.append(self.timeline_scale)

        # Dauer-Label rechts (Gesamtdauer)
        self.duration_label = Gtk.Label(label="00:00")
        self.duration_label.set_width_chars(6)
        self.duration_label.add_css_class("monospace")
        timeline_box.append(self.duration_label)

        return timeline_box

    def start_timeline_updates(self):
        """Startet periodische Timeline-Updates"""
        if self.timeline_update_timeout is None:
            self.timeline_update_timeout = GLib.timeout_add(250, self.update_timeline)
            print("Timeline updates started (250ms interval)")

    def stop_timeline_updates(self):
        """Stoppt Timeline-Updates"""
        if self.timeline_update_timeout is not None:
            GLib.source_remove(self.timeline_update_timeout)
            self.timeline_update_timeout = None
            print("Timeline updates stopped")

    def update_timeline(self):
        """Wird alle 250ms aufgerufen - aktualisiert Timeline"""
        if self.is_seeking:
            return True  # Nicht während Drag updaten

        position = self.get_current_position()
        duration = self.get_current_duration()

        # Labels aktualisieren
        self.time_label.set_text(self.format_time(position))
        self.duration_label.set_text(self.format_time(duration))

        # Slider aktualisieren
        if duration > 0:
            percentage = (position / duration) * 100.0
            self.timeline_scale.set_value(percentage)
            if not self.timeline_scale.get_sensitive():
                self.timeline_scale.set_sensitive(True)
        else:
            if self.timeline_scale.get_sensitive():
                self.timeline_scale.set_sensitive(False)

        return True  # Timeout fortsetzen

    @staticmethod
    def format_time(seconds):
        """Formatiert Sekunden zu MM:SS oder HH:MM:SS"""
        if seconds < 0:
            seconds = 0
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def get_current_position(self):
        """Gibt Position basierend auf Modus zurück"""
        if self.play_mode == "local":
            return self.video_player.get_position()
        else:
            self.cast_manager.update_status()
            return self.cast_manager.get_position()

    def get_current_duration(self):
        """Gibt Dauer basierend auf Modus zurück"""
        if self.play_mode == "local":
            return self.video_player.get_duration()
        else:
            return self.cast_manager.get_duration()

    def on_timeline_seek(self, scale, scroll_type, value):
        """Wird aufgerufen, wenn der Benutzer den Timeline-Slider bewegt."""
        duration = self.get_current_duration()
        if duration > 0:
            position_seconds = (value / 100.0) * duration
            self.perform_seek(position_seconds)
            # Aktualisiere das linke Zeit-Label sofort
            self.time_label.set_text(self.format_time(position_seconds))
        return False # Erlaube dem Signal, weiter zu laufen

    def perform_seek(self, position_seconds):
        """Führt Seek basierend auf Modus aus"""
        print(f"Seeking to {position_seconds:.1f}s (mode: {self.play_mode})")
        if self.play_mode == "local":
            self.video_player.seek(position_seconds)
        else:
            # Chromecast-Seeking in Thread ausführen um UI nicht zu blockieren
            if self.cast_manager.mc:
                def chromecast_seek():
                    self.cast_manager.seek(position_seconds)

                thread = threading.Thread(target=chromecast_seek, daemon=True)
                thread.start()
            else:
                print("Cannot seek: No Chromecast connection")

    def setup_controls(self):
        """Erstellt die Steuerungsleiste"""
        self.control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.control_box.set_halign(Gtk.Align.CENTER)
        self.control_box.set_margin_start(12)
        self.control_box.set_margin_end(12)
        self.control_box.set_margin_bottom(12)

        # Play Button
        self.play_button = Gtk.Button()
        self.play_button.set_icon_name("media-playback-start-symbolic")
        self.play_button.connect("clicked", self.on_play)
        self.control_box.append(self.play_button)

        # Pause Button
        pause_button = Gtk.Button()
        pause_button.set_icon_name("media-playback-pause-symbolic")
        pause_button.connect("clicked", self.on_pause)
        self.control_box.append(pause_button)

        # Stop Button
        stop_button = Gtk.Button()
        stop_button.set_icon_name("media-playback-stop-symbolic")
        stop_button.connect("clicked", self.on_stop)
        self.control_box.append(stop_button)

        # Mode Toggle
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mode_box.set_margin_start(24)

        mode_label = Gtk.Label(label="Modus:")
        mode_box.append(mode_label)

        self.mode_switch = Gtk.Switch()
        self.mode_switch.set_active(False)
        self.mode_switch.connect("notify::active", self.on_mode_changed)
        mode_box.append(self.mode_switch)

        self.mode_label = Gtk.Label(label="Lokal")
        mode_box.append(self.mode_label)

        self.control_box.append(mode_box)

    def on_open_file(self, button):
        """Öffnet Dateiauswahl-Dialog"""
        dialog = Gtk.FileDialog()

        # Filter für Video-Dateien
        filter_video = Gtk.FileFilter()
        filter_video.set_name("Video-Dateien")
        filter_video.add_mime_type("video/*")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_video)
        dialog.set_filters(filters)

        dialog.open(self, None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        """Callback für Dateiauswahl"""
        try:
            file = dialog.open_finish(result)
            if file:
                filepath = file.get_path()
                self.current_video_path = filepath
                self.video_player.load_video(filepath)

                # Timeline aktivieren nach kurzem Delay
                def enable_timeline():
                    duration = self.video_player.get_duration()
                    if duration > 0:
                        self.timeline_scale.set_sensitive(True)
                        self.duration_label.set_text(self.format_time(duration))
                        self.time_label.set_text("00:00")
                        self.timeline_scale.set_value(0)
                    return False

                GLib.timeout_add(500, enable_timeline)

                # Info bei MKV/AVI - wird automatisch konvertiert
                filename = Path(filepath).name
                if filepath.lower().endswith(('.mkv', '.avi')):
                    self.status_label.set_text(f"Geladen: {filename} (wird auto. zu MP4 konvertiert)")
                else:
                    self.status_label.set_text(f"Geladen: {filename}")
        except Exception as e:
            print(f"Fehler beim Öffnen der Datei: {e}")

    def on_scan_chromecasts(self, button):
        """Sucht nach Chromecast-Geräten"""
        self.status_label.set_text("Suche nach Geräten...")
        button.set_sensitive(False)

        def on_devices_found(devices):
            button.set_sensitive(True)
            # Liste leeren
            while True:
                row = self.device_list.get_row_at_index(0)
                if row is None:
                    break
                self.device_list.remove(row)

            if devices:
                for service in devices:
                    row = Gtk.ListBoxRow()
                    label = Gtk.Label(label=service.friendly_name)
                    label.set_margin_start(12)
                    label.set_margin_end(12)
                    label.set_margin_top(6)
                    label.set_margin_bottom(6)
                    row.set_child(label)
                    row.service = service
                    self.device_list.append(row)

                self.status_label.set_text(f"{len(devices)} Gerät(e) gefunden")
            else:
                self.status_label.set_text("Keine Geräte gefunden")

        self.cast_manager.discover_chromecasts(on_devices_found)

    def on_device_selected(self, listbox, row):
        """Wählt ein Chromecast-Gerät aus"""
        service = row.service
        self.status_label.set_text(f"Verbinde mit {service.friendly_name}...")

        def connect():
            success = self.cast_manager.connect_to_chromecast(service)
            GLib.idle_add(self.on_connected, success, service.friendly_name)

        thread = threading.Thread(target=connect, daemon=True)
        thread.start()

    def on_connected(self, success, device_name):
        """Callback nach Verbindung"""
        if success:
            self.status_label.set_text(f"Verbunden: {device_name}")
            self.mode_switch.set_active(True)
        else:
            self.status_label.set_text(f"Verbindung fehlgeschlagen")
        return False

    def on_mode_changed(self, switch, gparam):
        """Wechselt zwischen lokalem und Chromecast-Modus"""
        if switch.get_active():
            # Wechsel zu Chromecast-Modus
            self.play_mode = "chromecast"
            self.mode_label.set_text("Chromecast")

            # Stoppe lokale Wiedergabe falls aktiv
            current_state = self.video_player.playbin.get_state(0).state
            if current_state in (Gst.State.PLAYING, Gst.State.PAUSED):
                print("Stoppe lokale Wiedergabe...")
                self.video_player.stop()

            # Wenn ein Video geladen ist und ein Chromecast verbunden ist,
            # starte automatisch das Streaming
            if self.current_video_path and self.cast_manager.selected_cast:
                self.status_label.set_text("Chromecast-Modus: Bereit")
                print("Chromecast-Modus aktiv. Drücke Play, um das Streaming zu starten.")
                # Das eigentliche Streaming wird jetzt durch on_play() ausgelöst,
                # nicht mehr automatisch beim Moduswechsel.
                # Dies verhindert Race Conditions und Logikfehler.
            elif self.current_video_path and not self.cast_manager.selected_cast:
                self.status_label.set_text("Chromecast-Modus - Kein Gerät verbunden")
            else:
                self.status_label.set_text("Chromecast-Modus")
        else:
            # Wechsel zu Lokal-Modus
            self.play_mode = "local"
            self.mode_label.set_text("Lokal")

            # Stoppe Chromecast-Streaming falls aktiv
            if self.cast_manager.mc and self.cast_manager.selected_cast:
                print("Stoppe Chromecast-Streaming...")
                try:
                    self.cast_manager.stop()
                    self.status_label.set_text("Chromecast gestoppt, Modus: Lokal")
                    # Erlaube wieder Standby
                    self.uninhibit_suspend()
                except Exception as e:
                    print(f"Fehler beim Stoppen von Chromecast: {e}")

            # Lade das Video lokal neu falls eines geladen ist
            if self.current_video_path:
                print(f"\n=== Wechsel zu Lokal-Modus ===")
                print(f"Original-Video: {Path(self.current_video_path).name}")

                # WICHTIG: Lade immer die Original-Datei (nicht die konvertierte MP4)
                # für lokale Wiedergabe
                self.video_player.load_video(self.current_video_path)

                # Gib der Pipeline kurz Zeit, das erste Frame zu laden
                GLib.timeout_add(100, lambda: (
                    self.status_label.set_text(f"Lokal bereit: {Path(self.current_video_path).name}"),
                    False  # Return False to stop the timeout
                ))

                print(f"Video '{Path(self.current_video_path).name}' wurde lokal geladen")
                print("Bereit zur Wiedergabe - drücke Play")

    def inhibit_suspend(self):
        """Verhindert Standby während Chromecast-Streaming"""
        if self.inhibit_cookie is None:
            try:
                # GTK4 Application Inhibit API
                app = self.get_application()
                if app:
                    # Inhibit suspend und idle
                    flags = (
                        Gtk.ApplicationInhibitFlags.SUSPEND |
                        Gtk.ApplicationInhibitFlags.IDLE
                    )
                    self.inhibit_cookie = app.inhibit(
                        self,
                        flags,
                        "Chromecast-Streaming läuft"
                    )
                    print("Standby wurde deaktiviert (Streaming aktiv)")
            except Exception as e:
                print(f"Fehler beim Deaktivieren von Standby: {e}")

    def uninhibit_suspend(self):
        """Erlaubt wieder Standby"""
        if self.inhibit_cookie is not None:
            try:
                app = self.get_application()
                if app:
                    app.uninhibit(self.inhibit_cookie)
                    self.inhibit_cookie = None
                    print("Standby wurde wieder aktiviert")
            except Exception as e:
                print(f"Fehler beim Aktivieren von Standby: {e}")

    def on_play(self, button):
        """Startet die Wiedergabe"""
        if self.play_mode == "local":
            self.video_player.play()
            self.start_timeline_updates()
        else:
            # Chromecast-Modus - Prüfe den Zustand
            mc = self.cast_manager.mc
            # Prüfe, ob eine Media-Session aktiv ist. Das ist der zuverlässigste Weg,
            # um zu wissen, ob ein Video geladen ist (auch wenn es pausiert oder IDLE ist).
            is_media_loaded = mc and mc.status and mc.status.media_session_id is not None


            if is_media_loaded:
                # Video ist bereits geladen, nur fortsetzen
                print("Fortsetze Chromecast-Wiedergabe...")
                self.cast_manager.play()
                self.start_timeline_updates()
                self.inhibit_suspend()
            elif self.current_video_path and self.cast_manager.selected_cast:
                # Verhindere Standby während Streaming
                # Starte HTTP-Server und streame zu Chromecast
                self.status_label.set_text("Starte Streaming...")

                def start_streaming():
                    GLib.idle_add(self.inhibit_suspend)
                    try:
                        video_path = self.current_video_path

                        # Automatische Konvertierung für MKV und AVI
                        if video_path.lower().endswith(('.mkv', '.avi')):
                            print(f"\n⚠ Inkompatibles Format erkannt: {Path(video_path).suffix}")
                            print("Starte automatische Konvertierung zu MP4...")
                            GLib.idle_add(self.status_label.set_text, "Konvertiere Video...")

                            def update_status(msg):
                                self.status_label.set_text(msg)

                            converted_path = self.video_converter.convert_to_mp4(
                                video_path,
                                progress_callback=update_status
                            )

                            if converted_path:
                                print(f"✓ Nutze konvertierte Datei: {converted_path}")
                                video_path = converted_path
                                GLib.idle_add(self.status_label.set_text, "Starte Streaming...")
                            else:
                                print("✗ Konvertierung fehlgeschlagen, versuche Original-Datei...")
                                GLib.idle_add(self.status_label.set_text, "Konvertierung fehlgeschlagen, versuche trotzdem...")
                                # Fahre mit Original-Datei fort (könnte trotzdem funktionieren)

                        # Hole HTTP-URL für Video
                        video_url = self.http_server.get_video_url(video_path)

                        if video_url:
                            print(f"Streaming URL: {video_url}")
                            # Starte Chromecast-Wiedergabe
                            success = self.cast_manager.play_video(video_path, video_url)

                            if success:
                                GLib.idle_add(self.status_label.set_text, "Streaming läuft...")
                                GLib.idle_add(self.start_timeline_updates)
                            else:
                                GLib.idle_add(self.status_label.set_text, "Streaming fehlgeschlagen")
                                GLib.idle_add(self.uninhibit_suspend)
                        else:
                            GLib.idle_add(self.status_label.set_text, "HTTP-Server-Fehler")
                            GLib.idle_add(self.uninhibit_suspend)
                    except Exception as e:
                        print(f"Streaming-Fehler: {e}")
                        import traceback
                        traceback.print_exc()
                        GLib.idle_add(self.status_label.set_text, f"Fehler: {str(e)}")
                        GLib.idle_add(self.uninhibit_suspend)

                thread = threading.Thread(target=start_streaming, daemon=True)
                thread.start()

    def on_pause(self, button):
        """Pausiert die Wiedergabe"""
        if self.play_mode == "local":
            self.video_player.pause()
        else:
            self.cast_manager.pause()
            # Bei Pause Standby wieder erlauben
            self.uninhibit_suspend()

    def on_stop(self, button):
        """Stoppt die Wiedergabe"""
        if self.play_mode == "local":
            self.video_player.stop()
        else:
            self.cast_manager.stop()
            self.status_label.set_text("Gestoppt")
            # Bei Stop Standby wieder erlauben
            self.uninhibit_suspend()

        # Timeline zurücksetzen
        self.stop_timeline_updates()
        self.timeline_scale.set_value(0)
        self.time_label.set_text("00:00")

    def on_show_about(self, button):
        """Zeigt About-Dialog"""
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="Video Chromecast Player",
            application_icon="com.videocast.player", # Stellen Sie sicher, dass dieses Icon existiert
            developer_name="DaHool",
            version="1.2.0",
            developers=["DaHool"],
            copyright="© 2025 DaHool",
            license_type=Gtk.License.MIT_X11,
            website="https://github.com/berlinux2016/gnome-chromecast-player",
            issue_url="https://github.com/berlinux2016/gnome-chromecast-player/issues",
            # Beschreibung des Programms
            comments="Ein moderner GTK4-Videoplayer mit Chromecast-Unterstützung, der für eine nahtlose Wiedergabe sowohl lokal als auch auf Chromecast-Geräten optimiert ist. Inklusive Hardware-Beschleunigung für AMD und NVIDIA GPUs.\n\nMit Liebe für Simone programmiert ❤️",
            # Dieser Text erscheint prominent unter der Versionsnummer
            debug_info=None
        )

        # "Was ist neu?" Sektion (wird im "Credits"-Tab angezeigt)
        about.add_credit_section(
            "Was ist neu in Version 1.2.0?",
            [
                "Timeline/Seek-Funktion für lokale Wiedergabe und Chromecast-Streaming",
                "Hardware-Beschleunigung für NVIDIA (NVDEC/NVENC)",
                "Verbesserte Kompatibilität mit Xiaomi TVs",
                "Optimierte und schnellere Chromecast-Gerätesuche",
                "Stabilerer Modus-Wechsel zwischen Lokal und Chromecast",
            ]
        )

        about.add_credit_section(
            "Features in Version 1.0.0",
            [
                "Grundlegende Chromecast-Unterstützung",
                "Hardware-Beschleunigung für AMD (VA-API)",
                "Automatische Konvertierung von MKV/AVI zu MP4",
                "Moderne Benutzeroberfläche mit GTK4/Libadwaita",
            ]
        )

        about.present()

    def on_close_request(self, window):
        """Cleanup beim Schließen der Anwendung"""
        print("Beende Anwendung, räume auf...")

        # Erlaube wieder Standby
        try:
            self.uninhibit_suspend()
        except Exception as e:
            print(f"Fehler beim Freigeben von Standby-Inhibitor: {e}")

        # Stoppe lokale Wiedergabe
        try:
            self.video_player.stop()
        except Exception as e:
            print(f"Fehler beim Stoppen des Video-Players: {e}")

        # Stoppe Chromecast-Streaming
        try:
            if self.cast_manager.selected_cast:
                print("Stoppe Chromecast-Wiedergabe...")
                self.cast_manager.stop()
                self.cast_manager.disconnect()
        except Exception as e:
            print(f"Fehler beim Trennen von Chromecast: {e}")

        # Stoppe HTTP-Server
        try:
            if self.http_server.server:
                print("Stoppe HTTP-Server...")
                self.http_server.stop_server()
        except Exception as e:
            print(f"Fehler beim Stoppen des HTTP-Servers: {e}")

        print("Cleanup abgeschlossen")
        return False  # Erlaubt Fenster zu schließen


class VideoPlayerApp(Adw.Application):
    """Hauptanwendung"""

    def __init__(self):
        super().__init__(application_id='com.videocast.player')
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = VideoPlayerWindow(application=app)
        self.win.present()


def main():
    app = VideoPlayerApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
