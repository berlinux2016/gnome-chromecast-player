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
import json
import hashlib
import random
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Adw, Gst, GLib, GstVideo, Gdk, Gio, GdkPixbuf
import pychromecast
from zeroconf import Zeroconf
from pychromecast.controllers.youtube import YouTubeController

Gst.init(None)

# GPU-Erkennung und Hardware-Beschleunigung
def detect_gpu():
    """Erweitertes GPU-Erkennung"""
    gpu_info = {
        'type': 'unknown',
        'name': 'Unknown',
        'vram': 0
    }
    
    try:
        # NVIDIA mit nvidia-smi
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total',
                               '--format=csv,noheader,nounits'],
                             capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            gpu_info['type'] = 'nvidia'
            if ',' in result.stdout:
                name, vram = result.stdout.strip().split(',')
                gpu_info['name'] = name.strip()
                gpu_info['vram'] = int(vram.strip())
            print(f"✓ NVIDIA GPU: {gpu_info['name']} ({gpu_info['vram']}MB)")
            return gpu_info
    
    except:
        pass
    
    try:
        # AMD/Intel mit lspci
        result = subprocess.run(['lspci', '-vmm', '-d', '::0300'],
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n\n')
            for device in lines:
                if 'AMD' in device or 'Radeon' in device:
                    gpu_info['type'] = 'amd'
                    for line in device.split('\n'):
                        if line.startswith('Device:'):
                            gpu_info['name'] = line.split(':', 1)[1].strip()
                    print(f"✓ AMD GPU: {gpu_info['name']}")
                    return gpu_info
                elif 'Intel' in device:
                    gpu_info['type'] = 'intel'
                    for line in device.split('\n'):
                        if line.startswith('Device:'):
                            gpu_info['name'] = line.split(':', 1)[1].strip()
                    print(f"✓ Intel GPU: {gpu_info['name']}")
                    return gpu_info
    except:
        pass
    
    print("ℹ Keine spezifische GPU erkannt, nutze AMD-Einstellungen")
    os.environ['LIBVA_DRIVER_NAME'] = 'radeonsi'
    os.environ['VDPAU_DRIVER'] = 'radeonsi'
    return gpu_info

GPU_INFO = detect_gpu()
GPU_TYPE = GPU_INFO['type']


class ConfigManager:
    """Verwaltet Anwendungseinstellungen"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "video-chromecast-player"
        self.config_file = self.config_dir / "settings.json"
        self.config_dir.mkdir(exist_ok=True)
        
        self.default_settings = {
            "last_directory": str(Path.home()),
            "volume": 1.0,
            "window_width": 1000,
            "window_height": 700,
            "chromecast_device": None,
            "play_mode": "local",
            "hardware_acceleration": True,
            "auto_convert_mkv": True,
            "cache_size_gb": 10,
            "keyboard_shortcuts": {
                "play_pause": "space",
                "fullscreen": "F11",
                "volume_up": "Up",
                "volume_down": "Down",
                "seek_forward": "Right",
                "seek_backward": "Left",
                "mute": "m",
                "next_video": "n",
                "previous_video": "p"
            }
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Lädt gespeicherte Einstellungen"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge mit Defaults
                    return {**self.default_settings, **loaded}
            except Exception as e:
                print(f"Fehler beim Laden der Einstellungen: {e}")
        return self.default_settings.copy()
    
    def save_settings(self):
        """Speichert Einstellungen"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Fehler beim Speichern der Einstellungen: {e}")
    
    def get_setting(self, key, default=None):
        """Gibt eine Einstellung zurück"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """Setzt eine Einstellung"""
        self.settings[key] = value
        self.save_settings()


class BookmarkManager:
    """Verwaltet Video-Lesezeichen (gespeicherte Positionen)"""

    def __init__(self):
        self.bookmarks_dir = Path.home() / ".config" / "video-chromecast-player"
        self.bookmarks_file = self.bookmarks_dir / "bookmarks.json"
        self.bookmarks_dir.mkdir(exist_ok=True)
        self.bookmarks = self.load_bookmarks()

    def load_bookmarks(self):
        """Lädt gespeicherte Lesezeichen"""
        if self.bookmarks_file.exists():
            try:
                with open(self.bookmarks_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden der Lesezeichen: {e}")
        return {}

    def save_bookmarks(self):
        """Speichert Lesezeichen"""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            print(f"Fehler beim Speichern der Lesezeichen: {e}")

    def get_bookmark(self, video_path):
        """Gibt die gespeicherte Position für ein Video zurück (in Sekunden)"""
        # Nutze absoluten Pfad als Schlüssel
        abs_path = str(Path(video_path).resolve())
        bookmark = self.bookmarks.get(abs_path)
        if bookmark:
            return bookmark.get('position', 0), bookmark.get('duration', 0)
        return None, None

    def set_bookmark(self, video_path, position, duration):
        """Speichert die aktuelle Position eines Videos"""
        # Speichere nur wenn mehr als 5 Sekunden abgespielt und nicht in den letzten 30 Sekunden
        if position < 5 or (duration > 0 and position > duration - 30):
            # Entferne Lesezeichen wenn am Anfang oder Ende
            self.remove_bookmark(video_path)
            return

        abs_path = str(Path(video_path).resolve())
        self.bookmarks[abs_path] = {
            'position': position,
            'duration': duration,
            'timestamp': time.time(),
            'filename': Path(video_path).name
        }
        self.save_bookmarks()
        print(f"Lesezeichen gespeichert: {Path(video_path).name} @ {self.format_time(position)}")

    def remove_bookmark(self, video_path):
        """Entfernt ein Lesezeichen"""
        abs_path = str(Path(video_path).resolve())
        if abs_path in self.bookmarks:
            del self.bookmarks[abs_path]
            self.save_bookmarks()

    def has_bookmark(self, video_path):
        """Prüft ob ein Lesezeichen existiert"""
        abs_path = str(Path(video_path).resolve())
        return abs_path in self.bookmarks

    @staticmethod
    def format_time(seconds):
        """Formatiert Sekunden zu MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


class VideoConverter:
    """Automatische Video-Konvertierung für Chromecast-Kompatibilität"""

    def __init__(self):
        self.conversion_cache_dir = Path.home() / ".cache" / "video-chromecast-player"
        self.conversion_cache_dir.mkdir(parents=True, exist_ok=True)
        self.active_conversions = {}
        self.cleanup_old_cache_files(max_age_days=7, max_size_gb=10)

    def cleanup_old_cache_files(self, max_age_days=7, max_size_gb=10):
        """Bereinigt alte Cache-Dateien"""
        now = time.time()
        max_size_bytes = max_size_gb * 1024**3
        total_size = 0
        
        cache_files = []
        for file in self.conversion_cache_dir.glob("*.mp4"):
            file_age = now - file.stat().st_mtime
            file_size = file.stat().st_size
            
            if file_age > max_age_days * 86400:
                file.unlink()
                print(f"✗ Alte Cache-Datei gelöscht: {file.name}")
            else:
                cache_files.append((file, file_size))
                total_size += file_size
        
        # Wenn Cache zu groß, älteste Dateien löschen
        cache_files.sort(key=lambda x: x[0].stat().st_mtime)
        while total_size > max_size_bytes and cache_files:
            file_to_delete, file_size = cache_files.pop(0)
            file_to_delete.unlink()
            total_size -= file_size
            print(f"✗ Cache-Datei gelöscht (Größenlimit): {file_to_delete.name}")

    def get_cached_mp4_path(self, mkv_path):
        """Generiert Pfad für konvertierte MP4-Datei im Cache"""
        mkv_file = Path(mkv_path)
        # Nutze Hash des Original-Pfads + Dateiname für eindeutigen Cache-Key
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
                '-progress', 'pipe:1',  # Fortschritt ausgeben
                '-y',  # Überschreibe falls vorhanden
                str(output_path)
            ]

            print(f"Führe aus: {' '.join(cmd)}")
            print("Bitte warten, dies kann einige Sekunden dauern...")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Parse Fortschritt in Echtzeit
            for line in iter(process.stdout.readline, ''):
                if 'time=' in line and progress_callback:
                    time_match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                    if time_match:
                        GLib.idle_add(progress_callback, f"Konvertiere... {time_match.group(1)}")

            process.wait()

            if process.returncode == 0:
                print(f"✓ Konvertierung erfolgreich!")
                print(f"  Dateigröße: {output_path.stat().st_size / (1024*1024):.1f} MB")
                if progress_callback:
                    GLib.idle_add(progress_callback, "Konvertierung abgeschlossen!")
                return str(output_path)
            else:
                print(f"✗ Schnelle Konvertierung fehlgeschlagen, versuche Re-Encoding...")
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

        elif GPU_TYPE == 'intel':
            print("Nutze Intel QSV Hardware-Encoding...")
            try:
                qsv_check = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'],
                                          capture_output=True, text=True, timeout=5)
                if 'h264_qsv' in qsv_check.stdout:
                    video_codec = 'h264_qsv'
                    video_params = [
                        '-c:v', 'h264_qsv',
                        '-profile:v', 'high',
                        '-level', '4.1',
                        '-b:v', '5M',
                    ]
                    print("  ✓ Encoder: Intel QSV (Hardware-beschleunigt)")
                else:
                    print("  ✗ Intel QSV Encoder nicht verfügbar")
                    video_codec = None
            except Exception as e:
                print(f"  ✗ Fehler beim Prüfen von QSV: {e}")
                video_codec = None

        # Keine Hardware-Beschleunigung verfügbar
        if video_codec is None:
            error_msg = (
                "❌ Hardware-Beschleunigung nicht verfügbar!\n\n"
                "Dieses Programm benötigt Hardware-Encoding für MKV/AVI Konvertierung.\n\n"
                "Bitte stelle sicher, dass:\n"
                "• Eine kompatible GPU installiert ist (AMD mit VAAPI oder NVIDIA mit NVENC oder Intel QSV)\n"
                "• Die entsprechenden Treiber installiert sind\n"
                "• FFmpeg mit Hardware-Unterstützung installiert ist\n\n"
                "Für AMD: sudo dnf install mesa-va-drivers ffmpeg\n"
                "Für NVIDIA: sudo dnf install nvidia-driver ffmpeg\n"
                "Für Intel: sudo dnf install intel-media-driver ffmpeg\n\n"
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
                '-progress', 'pipe:1',
                '-f', 'mp4',
                '-y',
                str(output_path)
            ])

            print(f"Führe aus: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Parse Fortschritt in Echtzeit
            for line in iter(process.stdout.readline, ''):
                if 'time=' in line and progress_callback:
                    time_match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                    if time_match:
                        GLib.idle_add(progress_callback, f"Re-Encoding... {time_match.group(1)}")

            process.wait()

            if process.returncode == 0:
                print(f"✓ Re-Encoding erfolgreich!")
                print(f"  Dateigröße: {output_path.stat().st_size / (1024*1024):.1f} MB")
                if progress_callback:
                    GLib.idle_add(progress_callback, "Re-Encoding abgeschlossen!")
                return str(output_path)
            else:
                print(f"✗ Re-Encoding fehlgeschlagen")
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
            print(f"  sudo firewall-cmd --permanent --add-port=8765/tcp")
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

    def set_volume(self, volume):
        """Setzt Chromecast-Lautstärke (0.0 bis 1.0)"""
        if self.selected_cast:
            try:
                if 0.0 <= volume <= 1.0:
                    self.selected_cast.set_volume(volume)
                    print(f"Chromecast Lautstärke: {volume * 100:.0f}%")
                else:
                    print(f"✗ Ungültiger Lautstärke-Wert: {volume} (muss zwischen 0.0 und 1.0 sein)")
            except Exception as e:
                print(f"✗ Fehler beim Setzen der Chromecast-Lautstärke: {e}")

    def get_volume(self):
        """Gibt aktuelle Chromecast-Lautstärke zurück (0.0 bis 1.0)"""
        if self.selected_cast and self.selected_cast.status:
            try:
                return self.selected_cast.status.volume_level
            except Exception as e:
                print(f"✗ Fehler beim Abrufen der Chromecast-Lautstärke: {e}")
                return 0.5  # Standardwert bei Fehler
        return 0.5  # Standardwert wenn nicht verbunden

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


class PlaylistManager:
    """Verwaltet die Video-Playlist"""

    def __init__(self):
        self.playlist = []  # Liste von Video-Pfaden
        self.current_index = -1  # Aktueller Index in der Playlist
        self.play_history = []  # Wiedergabeverlauf
        self.playlist_file = None

    def add_video(self, video_path):
        """Fügt ein Video zur Playlist hinzu"""
        if video_path not in self.playlist:
            self.playlist.append(video_path)
            print(f"✓ Video zur Playlist hinzugefügt: {Path(video_path).name}")
            return True
        else:
            print(f"ℹ Video bereits in Playlist: {Path(video_path).name}")
            return False

    def remove_video(self, index):
        """Entfernt ein Video aus der Playlist"""
        if 0 <= index < len(self.playlist):
            removed = self.playlist.pop(index)
            print(f"✓ Video aus Playlist entfernt: {Path(removed).name}")
            # Aktualisiere current_index wenn nötig
            if index < self.current_index:
                self.current_index -= 1
            elif index == self.current_index:
                self.current_index = -1
            return True
        return False

    def clear_playlist(self):
        """Leert die gesamte Playlist"""
        self.playlist.clear()
        self.current_index = -1
        self.play_history.clear()
        print("✓ Playlist geleert")

    def get_current_video(self):
        """Gibt den Pfad des aktuellen Videos zurück"""
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def next_video(self):
        """Springt zum nächsten Video"""
        if self.current_index < len(self.playlist) - 1:
            if self.current_index >= 0:
                self.play_history.append(self.current_index)
            self.current_index += 1
            return self.get_current_video()
        return None

    def previous_video(self):
        """Springt zum vorherigen Video"""
        if self.play_history:
            self.current_index = self.play_history.pop()
            return self.get_current_video()
        elif self.current_index > 0:
            self.current_index -= 1
            return self.get_current_video()
        return None

    def set_current_index(self, index):
        """Setzt den aktuellen Index"""
        if 0 <= index < len(self.playlist):
            self.current_index = index
            return True
        return False

    def has_next(self):
        """Prüft ob es ein nächstes Video gibt"""
        return self.current_index < len(self.playlist) - 1

    def has_previous(self):
        """Prüft ob es ein vorheriges Video gibt"""
        return self.current_index > 0 or len(self.play_history) > 0

    def get_playlist_length(self):
        """Gibt die Anzahl der Videos in der Playlist zurück"""
        return len(self.playlist)

    def move_video(self, from_index, to_index):
        """Verschiebt ein Video innerhalb der Playlist"""
        if 0 <= from_index < len(self.playlist) and 0 <= to_index < len(self.playlist):
            video = self.playlist.pop(from_index)
            self.playlist.insert(to_index, video)
            # Aktualisiere current_index
            if self.current_index == from_index:
                self.current_index = to_index
            elif from_index < self.current_index <= to_index:
                self.current_index -= 1
            elif to_index <= self.current_index < from_index:
                self.current_index += 1
            return True
        return False

    def save_playlist(self, filepath):
        """Speichert Playlist als M3U-Datei"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for video_path in self.playlist:
                    video_name = Path(video_path).name
                    f.write(f"#EXTINF:-1,{video_name}\n")
                    f.write(f"{video_path}\n")
            self.playlist_file = filepath
            print(f"✓ Playlist gespeichert: {filepath}")
            return True
        except Exception as e:
            print(f"✗ Fehler beim Speichern der Playlist: {e}")
            return False

    def shuffle_playlist(self):
        """Mischt die Playlist zufällig"""
        import random
        current_video = self.get_current_video()
        
        # Speichere aktuelle Position
        if current_video:
            current_pos = self.current_index
        
        random.shuffle(self.playlist)
        
        # Wiederherstellung der aktuellen Position
        if current_video and current_video in self.playlist:
            self.current_index = self.playlist.index(current_video)
        else:
            self.current_index = -1
        
        print("✓ Playlist gemischt")

    def remove_duplicates(self):
        """Entfernt doppelte Einträge aus der Playlist"""
        unique_videos = []
        seen = set()
        
        for video_path in self.playlist:
            if video_path not in seen:
                seen.add(video_path)
                unique_videos.append(video_path)
        
        removed_count = len(self.playlist) - len(unique_videos)
        if removed_count > 0:
            self.playlist = unique_videos
            # Aktuellen Index korrigieren
            if 0 <= self.current_index < len(self.playlist):
                current_video = self.playlist[self.current_index]
            else:
                self.current_index = -1
            
            print(f"✓ {removed_count} doppelte Einträge entfernt")
            return True
        
        return False

    def search_subtitles(self, video_path):
        """Sucht automatisch nach passenden Untertiteln"""
        video_file = Path(video_path)
        video_dir = video_file.parent
        video_stem = video_file.stem
        
        subtitle_formats = ['.srt', '.ass', '.ssa', '.vtt', '.sub']
        found_subtitles = []
        
        # Suche im gleichen Verzeichnis
        for sub_format in subtitle_formats:
            subtitle_file = video_dir / f"{video_stem}{sub_format}"
            if subtitle_file.exists():
                found_subtitles.append(str(subtitle_file))
            
            # Alternative Benennungen
            subtitle_file = video_dir / f"{video_stem}.de{sub_format}"
            if subtitle_file.exists():
                found_subtitles.append(str(subtitle_file))
                
            subtitle_file = video_dir / f"{video_stem}.en{sub_format}"
            if subtitle_file.exists():
                found_subtitles.append(str(subtitle_file))
        
        # Durchsuche auch Untertitel-Unterverzeichnis
        sub_dir = video_dir / "Subs" / video_stem
        if sub_dir.exists():
            for sub_file in sub_dir.glob("*"):
                if sub_file.suffix.lower() in subtitle_formats:
                    found_subtitles.append(str(sub_file))
        
        return found_subtitles


class VideoPlayer(Gtk.Box):
    """Video-Player-Widget mit GStreamer und Hardware-Beschleunigung"""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # GStreamer Pipeline mit Hardware-Beschleunigung
        self.playbin = Gst.ElementFactory.make("playbin", "player")

        # Aktiviere Untertitel-Verarbeitung
        flags = self.playbin.get_property("flags")
        flags |= (1 << 2)  # GST_PLAY_FLAG_TEXT
        self.playbin.set_property("flags", flags)
        # Hardware-Beschleunigung aktivieren
        self.setup_hardware_acceleration()

        # Video-Ausgabe
        self.video_widget = Gtk.Picture()
        self.video_widget.set_size_request(800, 450)
        self.video_widget.set_vexpand(True)
        self.video_widget.set_content_fit(Gtk.ContentFit.COVER)
        self.video_widget.set_hexpand(True)

        # Video-Equalizer (videobalance)
        self.videobalance = Gst.ElementFactory.make("videobalance", "balance")
        self.videoconvert = Gst.ElementFactory.make("videoconvert", "convert")

        # Video-Sink für GTK
        self.gtksink = Gst.ElementFactory.make("gtk4paintablesink", "sink")

        # Erstelle bin mit videobalance -> videoconvert -> gtksink
        video_bin = Gst.Bin.new("video_bin")
        video_bin.add(self.videobalance)
        video_bin.add(self.videoconvert)
        video_bin.add(self.gtksink)

        # Verknüpfe Elemente
        self.videobalance.link(self.videoconvert)
        self.videoconvert.link(self.gtksink)

        # Erstelle Ghost-Pad für Eingang
        sink_pad = self.videobalance.get_static_pad("sink")
        ghost_pad = Gst.GhostPad.new("sink", sink_pad)
        video_bin.add_pad(ghost_pad)

        paintable = self.gtksink.get_property("paintable")
        self.video_widget.set_paintable(paintable)
        self.playbin.set_property("video-sink", video_bin)

        # Standard-Equalizer-Werte
        self.equalizer_settings = {
            'brightness': 0.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'hue': 0.0
        }

        self.append(self.video_widget)

        # Bus für Nachrichten
        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_gst_message)

        self.current_file = None
        self.current_uri = None  # URI für Thumbnail-Extraction
        self.hw_accel_enabled = False
        self.info_callback = None
        # Zustand für Video-Infos, um Flackern zu vermeiden
        self._video_info = {
            "resolution": "N/A",
            "codec": "N/A",
            "bitrate": "N/A"
        }

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

            elif GPU_TYPE == 'intel':
                # Intel VA-API Hardware-Beschleunigung
                vaapi_dec = Gst.ElementFactory.find("vaapidecodebin")
                if vaapi_dec:
                    hw_decoder = 'vaapi'
                    print("✓ Hardware-Beschleunigung (Intel VA-API) aktiviert")
                else:
                    print("⚠ VA-API nicht verfügbar für Intel GPU")

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
        # Setze Video-Infos für neue Datei zurück
        self._video_info = {
            "resolution": "N/A",
            "codec": "N/A",
            "bitrate": "N/A"
        }
        self.current_file = filepath
        # Konvertiere zu absoluten Pfad und erstelle korrekte URI
        abs_path = str(Path(filepath).resolve())
        # Korrekte URI mit drei Slashes für absolute Pfade
        uri = f"file:///{abs_path}" if abs_path.startswith('/') else f"file://{abs_path}"
        self.current_uri = uri  # Speichere URI für Thumbnail-Extraction
        print(f"Lade Video lokal: {abs_path}")
        print(f"URI: {uri}")
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

    def set_playback_rate(self, rate):
        """Setzt die Wiedergabegeschwindigkeit (0.5 = halbe, 2.0 = doppelte Geschwindigkeit)"""
        if rate <= 0:
            print(f"Ungültige Wiedergabegeschwindigkeit: {rate}")
            return False

        position = self.get_position()

        # Führe Seek mit neuer Rate aus
        seek_event = Gst.Event.new_seek(
            rate,
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            Gst.SeekType.SET,
            int(position * Gst.SECOND),
            Gst.SeekType.NONE,
            -1
        )

        success = self.playbin.send_event(seek_event)
        if success:
            print(f"Wiedergabegeschwindigkeit: {rate}x")
        else:
            print(f"Fehler beim Setzen der Wiedergabegeschwindigkeit auf {rate}x")
        return success

    def get_playback_rate(self):
        """Gibt die aktuelle Wiedergabegeschwindigkeit zurück"""
        # GStreamer speichert die Rate nicht direkt, daher müssen wir sie selbst verfolgen
        return getattr(self, '_playback_rate', 1.0)

    def take_screenshot(self, save_path):
        """Nimmt einen Screenshot des aktuellen Frames"""
        try:
            # Hole das aktuelle Sample vom Sink
            # GstGtk4Paintable hat kein get_current_frame, verwende convert-sample stattdessen
            sample = self.playbin.emit("convert-sample", Gst.Caps.from_string("video/x-raw,format=RGB"))
            if not sample:
                print("Kein Frame verfügbar für Screenshot")
                return False

            # Hole die Caps (Format-Info)
            caps = sample.get_caps()
            if not caps:
                print("Keine Caps für Screenshot verfügbar")
                return False

            # Extrahiere das Buffer
            buffer = sample.get_buffer()
            if not buffer:
                print("Kein Buffer für Screenshot")
                return False

            # Map the buffer to access the data
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                print("Konnte Buffer nicht mappen")
                return False

            try:
                # Hole Breite und Höhe aus Caps
                structure = caps.get_structure(0)
                width = structure.get_value('width')
                height = structure.get_value('height')

                # Erstelle PNG mit GdkPixbuf
                from gi.repository import GdkPixbuf

                # Konvertiere buffer data zu bytes
                data = map_info.data

                # Erstelle Pixbuf aus Raw-Daten
                pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                    data,
                    GdkPixbuf.Colorspace.RGB,
                    False,  # has_alpha
                    8,  # bits_per_sample
                    width,
                    height,
                    width * 3  # rowstride
                )

                # Speichere als PNG
                pixbuf.savev(save_path, "png", [], [])
                print(f"Screenshot gespeichert: {save_path}")
                return True

            finally:
                buffer.unmap(map_info)

        except Exception as e:
            print(f"Fehler beim Screenshot: {e}")
            import traceback
            traceback.print_exc()
            return False

    def set_equalizer(self, brightness=None, contrast=None, saturation=None, hue=None):
        """Setzt Video-Equalizer-Werte (brightness: -1 bis 1, contrast: 0 bis 2, saturation: 0 bis 2, hue: -1 bis 1)"""
        if brightness is not None:
            brightness = max(-1.0, min(1.0, brightness))
            self.videobalance.set_property("brightness", brightness)
            self.equalizer_settings['brightness'] = brightness
            print(f"Helligkeit: {brightness}")

        if contrast is not None:
            contrast = max(0.0, min(2.0, contrast))
            self.videobalance.set_property("contrast", contrast)
            self.equalizer_settings['contrast'] = contrast
            print(f"Kontrast: {contrast}")

        if saturation is not None:
            saturation = max(0.0, min(2.0, saturation))
            self.videobalance.set_property("saturation", saturation)
            self.equalizer_settings['saturation'] = saturation
            print(f"Sättigung: {saturation}")

        if hue is not None:
            hue = max(-1.0, min(1.0, hue))
            self.videobalance.set_property("hue", hue)
            self.equalizer_settings['hue'] = hue
            print(f"Farbton: {hue}")

    def get_equalizer(self):
        """Gibt die aktuellen Equalizer-Einstellungen zurück"""
        return self.equalizer_settings.copy()

    def reset_equalizer(self):
        """Setzt Equalizer auf Standard-Werte zurück"""
        self.set_equalizer(brightness=0.0, contrast=1.0, saturation=1.0, hue=0.0)
        print("Equalizer zurückgesetzt")

    def get_frame_at_position(self, position_seconds):
        """Extrahiert ein Frame an einer bestimmten Position als Pixbuf für Thumbnails

        Verwendet eine separate Pipeline für präzises Frame-Extraction ohne
        die Hauptwiedergabe zu stören.
        """
        try:
            # Erstelle eine temporäre Pipeline nur für diesen Frame
            # Dies verhindert, dass wir die Hauptwiedergabe unterbrechen müssen
            pipeline_str = f'uridecodebin uri="{self.current_uri}" ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=160,height=90 ! appsink name=sink sync=false'

            thumbnail_pipeline = Gst.parse_launch(pipeline_str)
            appsink = thumbnail_pipeline.get_by_name('sink')

            # Konfiguriere den appsink
            appsink.set_property('emit-signals', False)
            appsink.set_property('max-buffers', 1)
            appsink.set_property('drop', True)

            # Setze Pipeline in PAUSED state
            thumbnail_pipeline.set_state(Gst.State.PAUSED)

            # Warte bis Pipeline bereit ist
            ret = thumbnail_pipeline.get_state(5 * Gst.SECOND)
            if ret[0] != Gst.StateChangeReturn.SUCCESS:
                thumbnail_pipeline.set_state(Gst.State.NULL)
                return None

            # Seek zur gewünschten Position
            seek_flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE | Gst.SeekFlags.KEY_UNIT
            position_ns = position_seconds * Gst.SECOND

            thumbnail_pipeline.seek_simple(
                Gst.Format.TIME,
                seek_flags,
                position_ns
            )

            # Warte auf Seek-Completion
            bus = thumbnail_pipeline.get_bus()
            msg = bus.timed_pop_filtered(
                2 * Gst.SECOND,
                Gst.MessageType.ASYNC_DONE | Gst.MessageType.ERROR
            )

            if not msg or msg.type == Gst.MessageType.ERROR:
                thumbnail_pipeline.set_state(Gst.State.NULL)
                return None

            # Hole Sample vom appsink
            sample = appsink.emit('pull-preroll')

            if sample:
                buffer = sample.get_buffer()
                caps = sample.get_caps()

                structure = caps.get_structure(0)
                width = structure.get_value("width")
                height = structure.get_value("height")

                success, map_info = buffer.map(Gst.MapFlags.READ)
                if success:
                    try:
                        # Kopiere Daten, da Buffer nach unmap ungültig wird
                        data = bytes(map_info.data)

                        # Erstelle Pixbuf aus Daten
                        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                            GLib.Bytes.new(data),
                            GdkPixbuf.Colorspace.RGB,
                            False,
                            8,
                            width,
                            height,
                            width * 3
                        )

                        # Pipeline aufräumen
                        buffer.unmap(map_info)
                        thumbnail_pipeline.set_state(Gst.State.NULL)

                        return pixbuf

                    except Exception as e:
                        buffer.unmap(map_info)
                        print(f"Fehler beim Pixbuf-Erstellen: {e}")

            # Pipeline aufräumen
            thumbnail_pipeline.set_state(Gst.State.NULL)

        except Exception as e:
            print(f"Fehler beim Thumbnail-Erstellen: {e}")
            import traceback
            traceback.print_exc()

        return None

    def get_chapters(self):
        """Extrahiert Kapitel-Informationen aus dem Video"""
        chapters = []
        try:
            # Versuche TOC (Table of Contents) zu bekommen (get_toc ist die neuere Methode)
            toc = self.playbin.get_toc()
            success = toc is not None
            if success and toc:
                entries = toc.get_entries()
                for entry in entries:
                    # Hole Kapitel-Informationen
                    entry_type = entry.get_entry_type()
                    if entry_type == Gst.TocEntryType.CHAPTER:
                        # Hole Start- und Endzeit
                        success_start, start, stop = entry.get_start_stop_times()
                        if success_start:
                            start_seconds = start / Gst.SECOND

                            # Hole Kapitel-Titel
                            tags = entry.get_tags()
                            title = f"Kapitel {len(chapters) + 1}"
                            if tags:
                                success_title, tag_title = tags.get_string(Gst.TAG_TITLE)
                                if success_title:
                                    title = tag_title

                            chapters.append({
                                'title': title,
                                'start': start_seconds,
                                'index': len(chapters)
                            })
                            print(f"Kapitel gefunden: {title} bei {start_seconds:.1f}s")

                if chapters:
                    print(f"✓ {len(chapters)} Kapitel gefunden")
                else:
                    print("ℹ Keine Kapitel im Video gefunden")
            else:
                print("ℹ Video hat keine TOC (Table of Contents)")

        except Exception as e:
            print(f"Fehler beim Lesen der Kapitel: {e}")

        return chapters

    def on_gst_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"GStreamer Fehler: {err}, {debug}")
        elif t == Gst.MessageType.EOS:
            self.playbin.set_state(Gst.State.NULL)
            # Signal an Parent-Window senden
            if hasattr(self, 'eos_callback') and self.eos_callback:
                GLib.idle_add(self.eos_callback)
        elif t == Gst.MessageType.TAG and self.info_callback:
            taglist = message.parse_tag()
            # Wir rufen die Extraktion auf, die dann die Tags und Caps verarbeitet
            self.extract_video_info(taglist)

        elif t == Gst.MessageType.ASYNC_DONE:
            # Ein guter Zeitpunkt, um nach Untertiteln zu suchen, da die Streams jetzt bekannt sind
            if hasattr(self, 'streams_ready_callback') and self.streams_ready_callback:
                GLib.idle_add(self.streams_ready_callback)

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

    def set_volume(self, volume):
        """Setzt die Lautstärke (0.0 bis 1.0)"""
        if 0.0 <= volume <= 1.0:
            self.playbin.set_property("volume", volume)
            print(f"Lokale Lautstärke: {volume * 100:.0f}%")
        else:
            print(f"✗ Ungültiger Lautstärke-Wert: {volume} (muss zwischen 0.0 und 1.0 sein)")

    def get_volume(self):
        """Gibt aktuelle Lautstärke zurück (0.0 bis 1.0)"""
        return self.playbin.get_property("volume")

    def get_subtitle_tracks(self):
        """Gibt eine Liste der verfügbaren Untertitel-Spuren zurück."""
        tracks = []
        n_text = self.playbin.get_property('n-text')
        for i in range(n_text):
            tags = self.playbin.emit('get-text-tags', i)
            if tags:
                success_lang, lang = tags.get_string(Gst.TAG_LANGUAGE_CODE)
                success_title, title = tags.get_string(Gst.TAG_TITLE)

                description = f"Spur {i+1}"
                if success_title and title:
                    description = title
                elif success_lang and lang:
                    description = f"Spur {i+1} ({lang})"

                tracks.append({"index": i, "description": description})
        return tracks

    def set_subtitle_track(self, index):
        """Setzt die aktive Untertitel-Spur. -1 zum Deaktivieren."""
        self.playbin.set_property("current-text", index)

    def get_audio_tracks(self):
        """Gibt eine Liste der verfügbaren Audio-Spuren zurück."""
        tracks = []
        n_audio = self.playbin.get_property("n-audio")
        for i in range(n_audio):
            tags = self.playbin.emit("get-audio-tags", i)
            if tags:
                lang = tags.get_string(Gst.TAG_LANGUAGE_CODE)
                title = tags.get_string(Gst.TAG_TITLE)
                codec = tags.get_string(Gst.TAG_AUDIO_CODEC)

                description = f"Spur {i+1}"
                if lang and lang[0]:
                    description = f"Spur {i+1} ({lang[1]})"
                if title and title[0]:
                    description = title[1]
                if codec and codec[0]:
                    description += f" [{codec[1]}]"

                tracks.append({"index": i, "description": description})
            else:
                # Fallback wenn keine Tags verfügbar sind
                tracks.append({"index": i, "description": f"Audio-Spur {i+1}"})
        return tracks

    def set_audio_track(self, index):
        """Setzt die aktive Audio-Spur."""
        if index >= 0:
            self.playbin.set_property("current-audio", index)
            print(f"Audio-Spur gewechselt zu Index {index}")

    def get_current_audio_track(self):
        """Gibt den Index der aktuell aktiven Audio-Spur zurück."""
        return self.playbin.get_property("current-audio")

    def extract_video_info(self, taglist):
        """Extrahiert Video-Informationen aus dem GStreamer-Stream."""
        # Diese Funktion wird aufgerufen, wenn eine TAG-Nachricht empfangen wird.
        # Sie extrahiert Codec/Bitrate aus den Tags und die Auflösung aus den Caps.

        def get_and_send_info():
            try:
                # 1. Auflösung aus den Video-Sink-Capabilities extrahieren
                video_sink = self.playbin.get_property("video-sink")
                if video_sink:
                    pad = video_sink.get_static_pad("sink")
                    if pad:
                        peer_pad = pad.get_peer()
                        if peer_pad:
                            caps = peer_pad.get_current_caps()
                            if caps:
                                struct = caps.get_structure(0)
                                if struct and struct.has_field("width") and struct.has_field("height"):
                                    width = struct.get_int("width").value
                                    height = struct.get_int("height").value
                                    # Nur aktualisieren, wenn es ein gültiger Wert ist
                                    self._video_info["resolution"] = f"{width}x{height}"

                # 2. Codec aus den Tags extrahieren
                success, value = taglist.get_string(Gst.TAG_VIDEO_CODEC)
                if success:
                    # Formatieren für bessere Lesbarkeit (z.B. "H.264 (High Profile)")
                    self._video_info["codec"] = value.split(',')[0].replace(" decoder", "")
                else:
                    # Fallback, falls der Tag nicht da ist
                    success, value = taglist.get_string(Gst.TAG_CODEC)
                    if success:
                        # Nur aktualisieren, wenn es ein Video-Codec ist und wir noch keinen haben
                        if "video" in value and self._video_info["codec"] == "N/A":
                           self._video_info["codec"] = value.split(',')[0].replace(" decoder", "")

                # 3. Bitrate aus den Tags extrahieren
                # Nur aktualisieren, wenn ein gültiger Wert > 0 gefunden wird.
                # Dadurch wird ein existierender Wert nicht mit N/A überschrieben.
                success, bitrate = taglist.get_uint(Gst.TAG_BITRATE)
                if success and bitrate > 0:
                    self._video_info["bitrate"] = f"{bitrate / 1000:.0f} kbps"

                # Rufe den UI-Callback immer mit dem aktuellen Zustand des Dictionaries auf
                GLib.idle_add(self.info_callback, self._video_info)

            except Exception as e:
                print(f"Fehler beim Extrahieren der Video-Infos: {e}")

        # Führe die Info-Extraktion nach einer kurzen Verzögerung aus,
        # um sicherzustellen, dass auch die Auflösung verfügbar ist.
        GLib.timeout_add(250, lambda: (get_and_send_info(), False))


class VideoPlayerWindow(Adw.ApplicationWindow):
    """Hauptfenster der Anwendung"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Video Chromecast Player")
        self.set_default_size(1000, 700)

        # Config Manager
        self.config = ConfigManager()

        # Bookmark Manager
        self.bookmark_manager = BookmarkManager()

        # Chromecast Manager, HTTP-Server und Video-Converter
        self.cast_manager = ChromecastManager()
        self.http_server = VideoHTTPServer()
        self.video_converter = VideoConverter()
        self.playlist_manager = PlaylistManager()
        self.current_video_path = None

        # Standby-Inhibitor (verhindert Standby während Streaming)
        self.inhibit_cookie = None

        # Zustand für Stummschaltung
        self.is_muted = False
        self.last_volume = 1.0

        # Wiedergabegeschwindigkeit
        self.current_playback_rate = 1.0

        # A-B Loop
        self.ab_loop_enabled = False
        self.ab_loop_a = None  # Start-Position in Sekunden
        self.ab_loop_b = None  # End-Position in Sekunden

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

        # Video Player und Info-Overlay
        self.video_overlay = Gtk.Overlay()
        content_box.append(self.video_overlay)

        self.video_player = VideoPlayer()
        self.video_overlay.set_child(self.video_player)

        self.info_label = Gtk.Label()
        self.info_label.set_valign(Gtk.Align.START)
        self.info_label.set_halign(Gtk.Align.START)
        self.info_label.set_margin_start(10)
        self.info_label.set_margin_top(10)
        self.info_label.add_css_class("info-overlay")
        self.video_overlay.add_overlay(self.info_label)

        # Seitenleiste für Chromecast
        self.setup_sidebar()
        content_box.append(self.sidebar)

        self.main_box.append(content_box)

        # Timeline/Seek Bar
        self.timeline_widget = self.setup_timeline()
        self.main_box.append(self.timeline_widget)

        # Spiele-Modus (lokal oder chromecast) - muss vor setup_controls() initialisiert werden
        self.play_mode = self.config.get_setting("play_mode", "local")

        # Kontrollleiste
        self.setup_controls()
        self.main_box.append(self.control_box)

        self.set_content(self.main_box)

        # Timeline state tracking
        self.timeline_update_timeout = None
        self.is_seeking = False

        # Initialisiere Lautstärke
        saved_volume = self.config.get_setting("volume", 1.0)
        self.video_player.set_volume(saved_volume)
        self.volume_scale.set_value(saved_volume * 100)

        # Setze EOS-Callback für Auto-Advance
        self.video_player.eos_callback = self.on_video_ended

        # Setze Info-Callback
        self.video_player.info_callback = self.show_video_info

        # Setze Callback für Stream-Erkennung (für Untertitel und Audio)
        self.video_player.streams_ready_callback = self.update_media_menus

        # Drag-and-Drop Setup
        self.setup_drag_and_drop()

        # Tastatur-Events (für F11 Vollbild)
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        # CSS für visuelles Drag-and-Drop Feedback
        self.setup_drop_css()

        # Initialisiere Modus-Switch basierend auf gespeicherten Einstellungen
        if self.play_mode == "chromecast":
            self.mode_switch.set_active(True)
        else:
            self.mode_switch.set_active(False)

        # Window-Größe wiederherstellen
        window_width = self.config.get_setting("window_width", 1000)
        window_height = self.config.get_setting("window_height", 700)
        self.set_default_size(window_width, window_height)

        # Registriere Window-Actions für Menüs
        self.setup_actions()

    def setup_drop_css(self):
        """Fügt CSS für Drag-and-Drop visuelles Feedback hinzu"""
        css_provider = Gtk.CssProvider()
        css = b"""
        .drop-active {
            border: 3px dashed #3584e4;
            border-radius: 12px;
            background-color: alpha(#3584e4, 0.1);
        }
        .info-overlay {
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 10pt;
        }
        .monospace {
            font-family: monospace;
        }
        """
        css_provider.load_from_data(css)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_actions(self):
        """Registriert Window-Actions für Menüs"""
        # Speed Action
        speed_action = Gio.SimpleAction.new_stateful(
            "set_speed",
            GLib.VariantType.new('d'),
            GLib.Variant('d', 1.0)
        )
        speed_action.connect("activate", self.on_set_speed)
        self.add_action(speed_action)

        # Subtitle Action
        subtitle_action = Gio.SimpleAction.new_stateful(
            "set_subtitle",
            GLib.VariantType.new('i'),
            GLib.Variant('i', -1)
        )
        subtitle_action.connect("activate", self.on_set_subtitle)
        self.add_action(subtitle_action)

        # Audio Action
        audio_action = Gio.SimpleAction.new_stateful(
            "set_audio",
            GLib.VariantType.new('i'),
            GLib.Variant('i', 0)
        )
        audio_action.connect("activate", self.on_set_audio)
        self.add_action(audio_action)

        # Chapter Action
        chapter_action = Gio.SimpleAction.new(
            "goto_chapter",
            GLib.VariantType.new('d')
        )
        chapter_action.connect("activate", self.on_goto_chapter)
        self.add_action(chapter_action)

    def setup_drag_and_drop(self):
        """Richtet Drag-and-Drop für Videos ein"""
        # Erstelle DropTarget für Dateien
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)

        # Verbinde Callbacks
        drop_target.connect("drop", self.on_drop)
        drop_target.connect("enter", self.on_drag_enter)
        drop_target.connect("leave", self.on_drag_leave)

        # Füge DropTarget zum Video-Player hinzu
        self.video_player.add_controller(drop_target)

        print("✓ Drag-and-Drop aktiviert")

    def on_drag_enter(self, drop_target, x, y):
        """Wird aufgerufen, wenn eine Datei über das Fenster gezogen wird"""
        # Visuelles Feedback: Markiere den Drop-Bereich
        self.video_player.add_css_class("drop-active")
        return Gdk.DragAction.COPY

    def on_drag_leave(self, drop_target):
        """Wird aufgerufen, wenn die Datei den Drop-Bereich verlässt"""
        # Entferne visuelles Feedback
        self.video_player.remove_css_class("drop-active")

    def on_drop(self, drop_target, value, x, y):
        """Wird aufgerufen, wenn Dateien abgelegt werden"""
        # Entferne visuelles Feedback
        self.video_player.remove_css_class("drop-active")

        if isinstance(value, Gdk.FileList):
            files = value.get_files()
            if files:
                print(f"\n=== Drag-and-Drop: {len(files)} Datei(en) erkannt ===")

                video_files = []
                for file in files:
                    filepath = file.get_path()
                    filename = Path(filepath).name

                    # Prüfe ob es eine Video-Datei ist
                    if filepath.lower().endswith(('.mp4', '.mkv', '.avi', '.webm', '.mov', '.flv', '.ogg', '.mpeg', '.mpg', '.ts', '.wmv', '.m4v')):
                        video_files.append(filepath)
                        print(f"  ✓ {filename}")
                    else:
                        print(f"  ✗ Übersprungen (kein Video): {filename}")

                if video_files:
                    # Füge alle Videos zur Playlist hinzu
                    for video_path in video_files:
                        self.playlist_manager.add_video(video_path)

                    # Aktualisiere UI
                    self.update_playlist_ui()

                    # Wenn die Playlist vorher leer war, lade das erste Video, aber starte es nicht.
                    # Der Benutzer soll explizit auf Play drücken.
                    was_empty = self.playlist_manager.get_playlist_length() == len(video_files)
                    if was_empty:
                        self.playlist_manager.set_current_index(self.playlist_manager.get_playlist_length() - len(video_files))
                        first_video = self.playlist_manager.get_current_video()
                        if first_video:
                            # Lade das Video, aber starte es nicht automatisch
                            self.load_and_play_video(first_video, autoplay=False)

                    self.status_label.set_text(f"{len(video_files)} Video(s) zur Playlist hinzugefügt")
                    return True
                else:
                    self.status_label.set_text("Keine gültigen Video-Dateien gefunden")
                    return False

        return False

    def on_video_ended(self):
        """Wird aufgerufen, wenn ein Video zu Ende ist"""
        print("Video zu Ende - prüfe auf nächstes Video in Playlist")

        # Wenn es ein nächstes Video gibt, spiele es ab
        if self.playlist_manager.has_next():
            next_video = self.playlist_manager.next_video()
            if next_video:
                print(f"Auto-Advance: Spiele nächstes Video ab")
                self.load_and_play_video(next_video)
                self.update_playlist_ui()
        else:
            print("Keine weiteren Videos in Playlist")
            self.stop_timeline_updates()
            self.timeline_scale.set_value(0)
            self.time_label.set_text("00:00")
            # Erlaube wieder Standby, da die Wiedergabe beendet ist
            if self.play_mode == "chromecast":
                self.uninhibit_suspend()

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

        # Untertitel-Button
        self.subtitle_button = Gtk.MenuButton()
        self.subtitle_button.set_icon_name("media-view-subtitles-symbolic")
        self.subtitle_button.set_tooltip_text("Untertitel auswählen")
        self.subtitle_button.set_sensitive(False) # Deaktiviert bis Video geladen

        self.subtitle_popover = Gtk.PopoverMenu()
        self.subtitle_button.set_popover(self.subtitle_popover)
        header.pack_end(self.subtitle_button)

        # Audio-Track-Button
        self.audio_button = Gtk.MenuButton()
        self.audio_button.set_icon_name("audio-speakers-symbolic")
        self.audio_button.set_tooltip_text("Audio-Spur auswählen")
        self.audio_button.set_sensitive(False) # Deaktiviert bis Video geladen

        self.audio_popover = Gtk.PopoverMenu()
        self.audio_button.set_popover(self.audio_popover)
        header.pack_end(self.audio_button)

        # Kapitel-Button
        self.chapters_button = Gtk.MenuButton()
        self.chapters_button.set_icon_name("view-list-symbolic")
        self.chapters_button.set_tooltip_text("Kapitel")
        self.chapters_button.set_sensitive(False) # Deaktiviert bis Video geladen

        self.chapters_popover = Gtk.PopoverMenu()
        self.chapters_button.set_popover(self.chapters_popover)
        header.pack_end(self.chapters_button)

        # Wiedergabegeschwindigkeit-Button
        self.speed_button = Gtk.MenuButton()
        self.speed_button.set_icon_name("media-seek-forward-symbolic")
        self.speed_button.set_tooltip_text("Wiedergabegeschwindigkeit")
        self.speed_button.set_sensitive(False) # Deaktiviert bis Video geladen

        # Erstelle Speed-Menü
        speed_menu = Gio.Menu()
        speeds = [("0.5x", 0.5), ("0.75x", 0.75), ("Normal (1.0x)", 1.0),
                  ("1.25x", 1.25), ("1.5x", 1.5), ("2.0x", 2.0)]
        for label, speed in speeds:
            speed_menu.append(label, f"win.set_speed({speed})")

        self.speed_popover = Gtk.PopoverMenu()
        self.speed_popover.set_menu_model(speed_menu)
        self.speed_button.set_popover(self.speed_popover)
        header.pack_end(self.speed_button)

        # Video-Equalizer-Button
        self.equalizer_button = Gtk.MenuButton()
        self.equalizer_button.set_icon_name("preferences-color-symbolic")
        self.equalizer_button.set_tooltip_text("Video-Equalizer")
        self.equalizer_button.set_sensitive(False) # Deaktiviert bis Video geladen

        # Erstelle Equalizer-Popover
        self.equalizer_popover = self.create_equalizer_popover()
        self.equalizer_button.set_popover(self.equalizer_popover)
        header.pack_end(self.equalizer_button)

        # Vollbild-Button
        self.fullscreen_button = Gtk.Button()
        self.fullscreen_button.set_icon_name("view-fullscreen-symbolic")
        self.fullscreen_button.set_tooltip_text("Vollbild (F11)")
        self.fullscreen_button.connect("clicked", self.on_toggle_fullscreen)
        header.pack_end(self.fullscreen_button)

        # Loading Spinner
        self.loading_spinner = Gtk.Spinner()
        self.loading_spinner.set_size_request(24, 24)
        self.loading_spinner.set_visible(False)
        header.pack_end(self.loading_spinner)

        self.main_box.append(header)

    def setup_sidebar(self):
        """Erstellt die Seitenleiste für Playlist und Chromecast"""
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.sidebar.set_size_request(280, -1)

        # === PLAYLIST SECTION ===
        playlist_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Playlist Überschrift mit Zähler
        playlist_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        playlist_label = Gtk.Label(label="Playlist")
        playlist_label.add_css_class("title-3")
        playlist_header_box.append(playlist_label)

        self.playlist_count_label = Gtk.Label(label="(0)")
        self.playlist_count_label.add_css_class("dim-label")
        playlist_header_box.append(self.playlist_count_label)

        playlist_section.append(playlist_header_box)

        # Playlist Buttons
        playlist_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        add_playlist_button = Gtk.Button()
        add_playlist_button.set_icon_name("list-add-symbolic")
        add_playlist_button.set_tooltip_text("Videos zur Playlist hinzufügen")
        add_playlist_button.connect("clicked", self.on_add_to_playlist)
        playlist_button_box.append(add_playlist_button)

        import_playlist_button = Gtk.Button()
        import_playlist_button.set_icon_name("document-open-symbolic")
        import_playlist_button.set_tooltip_text("Playlist importieren (.m3u, .pls)")
        import_playlist_button.connect("clicked", self.on_import_playlist)
        playlist_button_box.append(import_playlist_button)

        save_playlist_button = Gtk.Button()
        save_playlist_button.set_icon_name("document-save-symbolic")
        save_playlist_button.set_tooltip_text("Playlist speichern")
        save_playlist_button.connect("clicked", self.on_save_playlist)
        playlist_button_box.append(save_playlist_button)

        shuffle_playlist_button = Gtk.Button()
        shuffle_playlist_button.set_icon_name("media-playlist-shuffle-symbolic")
        shuffle_playlist_button.set_tooltip_text("Playlist mischen")
        shuffle_playlist_button.connect("clicked", self.on_shuffle_playlist)
        playlist_button_box.append(shuffle_playlist_button)

        clear_playlist_button = Gtk.Button()
        clear_playlist_button.set_icon_name("user-trash-symbolic")
        clear_playlist_button.set_tooltip_text("Playlist leeren")
        clear_playlist_button.connect("clicked", self.on_clear_playlist)
        playlist_button_box.append(clear_playlist_button)

        playlist_section.append(playlist_button_box)

        # Scrollbarer Bereich für Playlist
        playlist_scrolled = Gtk.ScrolledWindow()
        playlist_scrolled.set_min_content_height(200)
        playlist_scrolled.set_vexpand(True)
        playlist_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.playlist_listbox = Gtk.ListBox()
        self.playlist_listbox.add_css_class("boxed-list")
        self.playlist_listbox.connect("row-activated", self.on_playlist_item_selected)

        playlist_scrolled.set_child(self.playlist_listbox)
        playlist_section.append(playlist_scrolled)

        self.sidebar.append(playlist_section)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.sidebar.append(separator)

        # === CHROMECAST SECTION ===
        chromecast_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Chromecast Überschrift
        label = Gtk.Label(label="Chromecast-Geräte")
        label.add_css_class("title-3")
        chromecast_section.append(label)

        # Scrollbarer Bereich für Geräte
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(150)
        scrolled.set_vexpand(False)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.device_list = Gtk.ListBox()
        self.device_list.add_css_class("boxed-list")
        self.device_list.connect("row-activated", self.on_device_selected)

        scrolled.set_child(self.device_list)
        chromecast_section.append(scrolled)

        # Status Label
        self.status_label = Gtk.Label(label="Keine Geräte gefunden")
        self.status_label.add_css_class("dim-label")
        chromecast_section.append(self.status_label)

        self.sidebar.append(chromecast_section)

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
        # 'value-changed' wird ausgelöst, wenn der Benutzer den Slider bewegt
        self.timeline_scale.connect("value-changed", self.on_timeline_seek)

        # Verwende GestureDrag, um den Start und das Ende des Ziehens zuverlässig zu erkennen
        drag_gesture = Gtk.GestureDrag.new()
        drag_gesture.set_button(1)  # Nur auf linke Maustaste reagieren
        drag_gesture.connect("drag-begin", self.on_timeline_drag_begin)
        drag_gesture.connect("drag-end", self.on_timeline_drag_end)
        self.timeline_scale.add_controller(drag_gesture)

        # Variablen für Thumbnail-Caching
        self.thumbnail_cache = {}
        self.last_thumbnail_position = None

        # Verwende Overlay um Motion-Events zuverlässig zu erfassen
        # während Click/Drag-Events zum Scale durchgereicht werden
        timeline_overlay = Gtk.Overlay()
        timeline_overlay.set_hexpand(True)
        timeline_overlay.set_child(self.timeline_scale)

        # Motion-Controller DIREKT auf dem Overlay-Container
        # Overlay empfängt Motion-Events, aber leitet Click-Events automatisch an Kind weiter
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect("motion", self.on_timeline_hover)
        motion_controller.connect("leave", self.on_timeline_leave)
        motion_controller.connect("enter", self.on_timeline_enter)
        timeline_overlay.add_controller(motion_controller)

        # Timeline-Thumbnail Popover erstellen
        self.thumbnail_popover = Gtk.Popover()
        self.thumbnail_popover.set_parent(timeline_overlay)
        self.thumbnail_popover.set_has_arrow(True)
        self.thumbnail_popover.set_position(Gtk.PositionType.TOP)
        self.thumbnail_popover.set_autohide(False)  # Nicht automatisch verstecken

        # Thumbnail-Box mit Bild und Zeit-Label
        thumb_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        thumb_box.set_margin_start(6)
        thumb_box.set_margin_end(6)
        thumb_box.set_margin_top(6)
        thumb_box.set_margin_bottom(6)

        # Bild für Thumbnail
        self.thumbnail_image = Gtk.Picture()
        self.thumbnail_image.set_size_request(160, 90)
        thumb_box.append(self.thumbnail_image)

        # Zeit-Label unter dem Thumbnail
        self.thumbnail_time_label = Gtk.Label(label="00:00")
        self.thumbnail_time_label.add_css_class("monospace")
        self.thumbnail_time_label.add_css_class("caption")
        thumb_box.append(self.thumbnail_time_label)

        self.thumbnail_popover.set_child(thumb_box)

        timeline_box.append(timeline_overlay)

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

        # Überprüfe A-B Loop
        self.check_ab_loop()

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

    def seek_to_position(self, position):
        """Springt zu einer bestimmten Position im Video"""
        if self.play_mode == "local":
            self.video_player.seek(position)
        else:
            self.cast_manager.seek(position)
        print(f"Gesprungen zu Position: {self.format_time(position)}")

    def save_current_position(self):
        """Speichert die aktuelle Wiedergabeposition als Lesezeichen"""
        if not self.current_video_path:
            return

        position = self.get_current_position()
        duration = self.get_current_duration()

        if position and duration and position > 0:
            self.bookmark_manager.set_bookmark(self.current_video_path, position, duration)

    def on_timeline_drag_begin(self, gesture, start_x, start_y):
        """Wird aufgerufen, wenn der Benutzer beginnt, den Slider zu ziehen."""
        self.is_seeking = True
        print("Timeline seeking started")

    def on_timeline_drag_end(self, gesture, offset_x, offset_y):
        """Wird aufgerufen, wenn der Benutzer das Ziehen des Sliders beendet."""
        self.is_seeking = False
        print("Timeline seeking ended")
        # Setze die Position zurück, um ein sofortiges Thumbnail-Update beim nächsten Hover zu erzwingen
        self.last_thumbnail_position = None
        # Verstecke das Popover, falls es noch offen ist
        self.thumbnail_popover.popdown()

    def on_timeline_seek(self, scale):
        """Wird aufgerufen, wenn der Benutzer den Timeline-Slider bewegt."""
        duration = self.get_current_duration()
        if duration > 0:
            value = scale.get_value()
            position_seconds = (value / 100.0) * duration
            self.perform_seek(position_seconds)
            # Aktualisiere das linke Zeit-Label sofort
            self.time_label.set_text(self.format_time(position_seconds))
        return False  # Erlaube dem Signal, weiter zu laufen

    def on_timeline_enter(self, controller, _x, _y):
        """Wird aufgerufen, wenn die Maus die Timeline betritt."""
        pass

    def on_timeline_hover(self, controller, x, y):
        """Wird aufgerufen, wenn die Maus über die Timeline schwebt."""
        print(f"Timeline hover at ({x:.1f}, {y:.1f})")

        # Nur im lokalen Modus und wenn Video geladen ist
        if self.play_mode != "local" or not self.timeline_scale.get_sensitive():
            print("  -> Skipped: wrong mode or not sensitive")
            return

        # Kein Thumbnail anzeigen während gezogen wird
        if self.is_seeking:
            print("  -> Skipped: seeking")
            return

        duration = self.get_current_duration()
        if not duration or duration <= 0:
            print("  -> Skipped: no duration")
            return

        # Berechne die Position präzise, indem wir das Gtk.Scale-Widget selbst fragen,
        # welchem Wert die Mausposition entspricht. Dies vermeidet Abweichungen durch
        # internes Padding des Widgets.
        # Wir verwenden hierfür ein internes, undokumentiertes Signal.
        hover_position = None # Initialisieren
        try:
            value = self.timeline_scale.emit("get-value-for-pos", x, y)
            hover_position = (value / 100.0) * duration
        except TypeError:
            # Fallback, falls das Signal nicht existiert oder fehlschlägt
            widget_width = self.timeline_scale.get_width()
            progress = max(0.0, min(1.0, x / widget_width)) if widget_width > 0 else 0
            hover_position = progress * duration

        # Stelle sicher, dass hover_position einen Wert hat
        if hover_position is None:
            print("  -> Skipped: hover_position konnte nicht berechnet werden.")
            return

        # Nur aktualisieren, wenn Position sich deutlich geändert hat (mindestens 2 Sekunden)
        if self.last_thumbnail_position is not None:
            if abs(hover_position - self.last_thumbnail_position) < 2.0:
                print(f"  -> Skipped: position change too small ({abs(hover_position - self.last_thumbnail_position):.1f}s)")
                return

        self.last_thumbnail_position = hover_position
        print(f"  -> Showing thumbnail at {hover_position:.1f}s")

        # Zeige Zeit-Label
        self.thumbnail_time_label.set_text(self.format_time(hover_position))

        # Prüfe ob Thumbnail im Cache ist (in 5-Sekunden-Schritten)
        cache_key = int(hover_position / 5) * 5

        if cache_key in self.thumbnail_cache:
            # Verwende gecachtes Thumbnail
            print(f"  -> Using cached thumbnail for {cache_key}s")
            pixbuf = self.thumbnail_cache.get(cache_key)
            if not pixbuf:
                # Sollte nicht passieren, aber zur Sicherheit
                GLib.idle_add(self.load_thumbnail_async, hover_position, cache_key)
                return
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.thumbnail_image.set_paintable(texture)
        else:
            # Lade Thumbnail asynchron
            print(f"  -> Loading new thumbnail for {cache_key}s")
            GLib.idle_add(self.load_thumbnail_async, hover_position, cache_key)

        # Positioniere und zeige Popover
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        self.thumbnail_popover.set_pointing_to(rect)

        self.thumbnail_popover.popup()
        print(f"  -> Popover shown at ({x:.1f}, {y:.1f})")

    def on_timeline_leave(self, controller):
        """Wird aufgerufen, wenn die Maus die Timeline verlässt."""
        self.thumbnail_popover.popdown()
        self.last_thumbnail_position = None
    def load_thumbnail_async(self, position, cache_key):
        """Lädt Thumbnail asynchron und cached es."""
        try:
            pixbuf = self.video_player.get_frame_at_position(position)
            if pixbuf:
                # Cache Thumbnail
                self.thumbnail_cache[cache_key] = pixbuf

                # Zeige Thumbnail
                # Erstelle eine Gdk.Paintable aus dem Pixbuf
                # Gdk.Texture.new_for_pixbuf() ist veraltet.
                # Der empfohlene Weg ist, ein Gtk.Image zu verwenden und dessen Paintable zu bekommen,
                # aber für diesen Fall ist es einfacher, die veraltete Methode vorerst zu behalten.
                texture = Gdk.Texture.new_for_pixbuf(pixbuf) # Veraltet, aber funktioniert
                self.thumbnail_image.set_paintable(texture)
        except Exception as e:
            print(f"Fehler beim Laden des Thumbnails: {e}")

        return False  # Nur einmal ausführen

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

        # Previous Button
        self.previous_button = Gtk.Button()
        self.previous_button.set_icon_name("media-skip-backward-symbolic")
        self.previous_button.set_tooltip_text("Vorheriges Video")
        self.previous_button.connect("clicked", self.on_previous_video)
        self.previous_button.set_sensitive(False)
        self.control_box.append(self.previous_button)

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

        # Next Button
        self.next_button = Gtk.Button()
        self.next_button.set_icon_name("media-skip-forward-symbolic")
        self.next_button.set_tooltip_text("Nächstes Video")
        self.next_button.connect("clicked", self.on_next_video)
        self.next_button.set_sensitive(False)
        self.control_box.append(self.next_button)

        # A-B Loop Buttons
        ab_separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        ab_separator.set_margin_start(12)
        ab_separator.set_margin_end(12)
        self.control_box.append(ab_separator)

        # A-Button (Startpunkt setzen)
        self.ab_button_a = Gtk.Button(label="A")
        self.ab_button_a.set_tooltip_text("A-B Loop: Startpunkt setzen (Taste 'A')")
        self.ab_button_a.connect("clicked", self.on_set_loop_a)
        self.ab_button_a.set_sensitive(False)
        self.control_box.append(self.ab_button_a)

        # B-Button (Endpunkt setzen)
        self.ab_button_b = Gtk.Button(label="B")
        self.ab_button_b.set_tooltip_text("A-B Loop: Endpunkt setzen (Taste 'B')")
        self.ab_button_b.connect("clicked", self.on_set_loop_b)
        self.ab_button_b.set_sensitive(False)
        self.control_box.append(self.ab_button_b)

        # Clear Loop Button
        self.ab_button_clear = Gtk.Button()
        self.ab_button_clear.set_icon_name("edit-clear-symbolic")
        self.ab_button_clear.set_tooltip_text("A-B Loop löschen (Taste 'C')")
        self.ab_button_clear.connect("clicked", self.on_clear_loop)
        self.ab_button_clear.set_sensitive(False)
        self.control_box.append(self.ab_button_clear)

        # Go-To Button (Sprung zu bestimmter Zeit)
        self.goto_button = Gtk.Button()
        self.goto_button.set_icon_name("go-jump-symbolic")
        self.goto_button.set_tooltip_text("Zu Zeit springen (Taste 'G')")
        self.goto_button.connect("clicked", self.on_show_goto_dialog)
        self.goto_button.set_sensitive(False)
        self.control_box.append(self.goto_button)

        # Lautstärke-Kontrolle
        volume_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        volume_box.set_margin_start(24)

        # Lautstärke-Icon
        volume_icon = Gtk.Image.new_from_icon_name("audio-volume-high-symbolic")
        volume_box.append(volume_icon)

        # Lautstärke-Slider (0-100 für bessere UX)
        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self.volume_scale.set_size_request(120, -1)
        self.volume_scale.set_draw_value(False)
        self.volume_scale.set_value(100)  # Standardwert 100%
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        volume_box.append(self.volume_scale)

        self.control_box.append(volume_box)

        # Mode Toggle
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mode_box.set_margin_start(24)

        mode_label = Gtk.Label(label="Modus:")
        mode_box.append(mode_label)

        self.mode_switch = Gtk.Switch()
        self.mode_switch.set_active(self.play_mode == "chromecast")
        self.mode_switch.connect("notify::active", self.on_mode_changed)
        mode_box.append(self.mode_switch)

        self.mode_label = Gtk.Label(label="Lokal" if self.play_mode == "local" else "Chromecast")
        mode_box.append(self.mode_label)

        self.control_box.append(mode_box)

    def create_equalizer_popover(self):
        """Erstellt das Popover für den Video-Equalizer"""
        popover = Gtk.Popover()

        # Hauptcontainer
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        # Titel
        title_label = Gtk.Label(label="Video-Equalizer")
        title_label.add_css_class("title-4")
        box.append(title_label)

        # Helligkeit
        brightness_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        brightness_label = Gtk.Label(label="Helligkeit")
        brightness_label.set_xalign(0)
        brightness_box.append(brightness_label)

        self.brightness_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
        self.brightness_scale.set_value(0.0)
        self.brightness_scale.set_draw_value(True)
        self.brightness_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.brightness_scale.set_hexpand(True)
        self.brightness_scale.connect("value-changed", self.on_brightness_changed)
        brightness_box.append(self.brightness_scale)
        box.append(brightness_box)

        # Kontrast
        contrast_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        contrast_label = Gtk.Label(label="Kontrast")
        contrast_label.set_xalign(0)
        contrast_box.append(contrast_label)

        self.contrast_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 2.0, 0.1)
        self.contrast_scale.set_value(1.0)
        self.contrast_scale.set_draw_value(True)
        self.contrast_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.contrast_scale.set_hexpand(True)
        self.contrast_scale.connect("value-changed", self.on_contrast_changed)
        contrast_box.append(self.contrast_scale)
        box.append(contrast_box)

        # Sättigung
        saturation_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        saturation_label = Gtk.Label(label="Sättigung")
        saturation_label.set_xalign(0)
        saturation_box.append(saturation_label)

        self.saturation_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 2.0, 0.1)
        self.saturation_scale.set_value(1.0)
        self.saturation_scale.set_draw_value(True)
        self.saturation_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.saturation_scale.set_hexpand(True)
        self.saturation_scale.connect("value-changed", self.on_saturation_changed)
        saturation_box.append(self.saturation_scale)
        box.append(saturation_box)

        # Farbton
        hue_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        hue_label = Gtk.Label(label="Farbton")
        hue_label.set_xalign(0)
        hue_box.append(hue_label)

        self.hue_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
        self.hue_scale.set_value(0.0)
        self.hue_scale.set_draw_value(True)
        self.hue_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.hue_scale.set_hexpand(True)
        self.hue_scale.connect("value-changed", self.on_hue_changed)
        hue_box.append(self.hue_scale)
        box.append(hue_box)

        # Reset Button
        reset_button = Gtk.Button(label="Zurücksetzen")
        reset_button.connect("clicked", self.on_equalizer_reset)
        box.append(reset_button)

        popover.set_child(box)
        return popover

    def on_brightness_changed(self, scale):
        """Callback für Helligkeit-Änderung"""
        value = scale.get_value()
        self.video_player.set_equalizer(brightness=value)

    def on_contrast_changed(self, scale):
        """Callback für Kontrast-Änderung"""
        value = scale.get_value()
        self.video_player.set_equalizer(contrast=value)

    def on_saturation_changed(self, scale):
        """Callback für Sättigung-Änderung"""
        value = scale.get_value()
        self.video_player.set_equalizer(saturation=value)

    def on_hue_changed(self, scale):
        """Callback für Farbton-Änderung"""
        value = scale.get_value()
        self.video_player.set_equalizer(hue=value)

    def on_equalizer_reset(self, _button):
        """Reset Equalizer auf Standard-Werte"""
        self.brightness_scale.set_value(0.0)
        self.contrast_scale.set_value(1.0)
        self.saturation_scale.set_value(1.0)
        self.hue_scale.set_value(0.0)
        self.video_player.reset_equalizer()

    def on_set_loop_a(self, _button):
        """Setzt den Startpunkt (A) für A-B Loop"""
        position = self.get_current_position()
        if position is not None:
            self.ab_loop_a = position
            self.ab_button_a.add_css_class("suggested-action")
            self.status_label.set_text(f"Loop Punkt A gesetzt: {self.format_time(position)}")
            print(f"A-B Loop: Punkt A gesetzt bei {position:.1f}s")

            # Aktiviere Clear-Button
            self.ab_button_clear.set_sensitive(True)

            # Wenn B bereits gesetzt ist, aktiviere Loop
            if self.ab_loop_b is not None and self.ab_loop_a < self.ab_loop_b:
                self.ab_loop_enabled = True
                self.ab_button_b.add_css_class("suggested-action")
                self.status_label.set_text(f"Loop aktiv: {self.format_time(self.ab_loop_a)} - {self.format_time(self.ab_loop_b)}")

    def on_set_loop_b(self, _button):
        """Setzt den Endpunkt (B) für A-B Loop"""
        position = self.get_current_position()
        if position is not None:
            # B muss nach A liegen
            if self.ab_loop_a is not None and position <= self.ab_loop_a:
                self.status_label.set_text("Punkt B muss nach Punkt A liegen!")
                return

            self.ab_loop_b = position
            self.ab_button_b.add_css_class("suggested-action")
            self.status_label.set_text(f"Loop Punkt B gesetzt: {self.format_time(position)}")
            print(f"A-B Loop: Punkt B gesetzt bei {position:.1f}s")

            # Aktiviere Clear-Button
            self.ab_button_clear.set_sensitive(True)

            # Wenn A bereits gesetzt ist, aktiviere Loop
            if self.ab_loop_a is not None and self.ab_loop_a < self.ab_loop_b:
                self.ab_loop_enabled = True
                self.ab_button_a.add_css_class("suggested-action")
                self.status_label.set_text(f"Loop aktiv: {self.format_time(self.ab_loop_a)} - {self.format_time(self.ab_loop_b)}")

    def on_clear_loop(self, _button):
        """Löscht den A-B Loop"""
        self.ab_loop_enabled = False
        self.ab_loop_a = None
        self.ab_loop_b = None
        self.ab_button_a.remove_css_class("suggested-action")
        self.ab_button_b.remove_css_class("suggested-action")
        self.ab_button_clear.set_sensitive(False)
        self.status_label.set_text("A-B Loop gelöscht")
        print("A-B Loop: Loop gelöscht")

    def check_ab_loop(self):
        """Überprüft, ob die Position den B-Punkt überschritten hat und springt zu A zurück"""
        if self.ab_loop_enabled and self.ab_loop_a is not None and self.ab_loop_b is not None:
            position = self.get_current_position()
            if position is not None and position >= self.ab_loop_b:
                # Springe zurück zu Punkt A
                self.seek_to_position(self.ab_loop_a)
                print(f"A-B Loop: Zurück zu Punkt A ({self.ab_loop_a:.1f}s)")

    def on_show_goto_dialog(self, _button):
        """Zeigt Dialog zum Springen zu einer bestimmten Zeit"""
        duration = self.get_current_duration()
        if not duration or duration <= 0:
            self.status_label.set_text("Kein Video geladen")
            return

        current_position = self.get_current_position() or 0

        # Erstelle Dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Zu Zeit springen")
        dialog.set_body("Gib die Zielzeit ein (Format: MM:SS oder HH:MM:SS)")

        # Erstelle Entry für Zeit-Eingabe
        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        entry_box.set_margin_top(12)
        entry_box.set_margin_bottom(12)
        entry_box.set_margin_start(12)
        entry_box.set_margin_end(12)

        time_entry = Gtk.Entry()
        time_entry.set_placeholder_text("z.B. 1:23:45 oder 5:30")
        # Setze aktuelle Zeit als Vorgabe
        time_entry.set_text(self.format_time(current_position))
        time_entry.set_max_width_chars(10)
        entry_box.append(time_entry)

        # Info-Label
        info_label = Gtk.Label(label=f"Video-Dauer: {self.format_time(duration)}")
        info_label.add_css_class("dim-label")
        entry_box.append(info_label)

        dialog.set_extra_child(entry_box)

        dialog.add_response("cancel", "Abbrechen")
        dialog.add_response("jump", "Springen")
        dialog.set_response_appearance("jump", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("jump")

        def on_response(dialog, response):
            if response == "jump":
                time_str = time_entry.get_text().strip()
                seconds = self.parse_time_string(time_str)
                if seconds is not None and 0 <= seconds <= duration:
                    self.seek_to_position(seconds)
                    self.status_label.set_text(f"Gesprungen zu {self.format_time(seconds)}")
                else:
                    self.status_label.set_text("Ungültige Zeitangabe")

        dialog.connect("response", on_response)
        dialog.present()

    def parse_time_string(self, time_str):
        """Konvertiert Zeitstring (MM:SS oder HH:MM:SS) zu Sekunden"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            else:
                return None
        except (ValueError, AttributeError):
            return None

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

        # Letztes Verzeichnis aus Config verwenden
        last_dir = self.config.get_setting("last_directory")
        if last_dir and Path(last_dir).exists():
            dialog.set_initial_folder(Gio.File.new_for_path(last_dir))

        dialog.open(self, None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        """Callback für Dateiauswahl"""
        try:
            file = dialog.open_finish(result)
            if file:
                filepath = file.get_path()
                self.current_video_path = filepath

                # Speichere Verzeichnis in Config
                self.config.set_setting("last_directory", str(Path(filepath).parent))

                # Füge zur Playlist hinzu und setze als aktuell
                if filepath not in self.playlist_manager.playlist:
                    self.playlist_manager.add_video(filepath)
                    self.playlist_manager.set_current_index(self.playlist_manager.get_playlist_length() - 1)
                else:
                    # Setze existierendes Video als aktuell
                    index = self.playlist_manager.playlist.index(filepath)
                    self.playlist_manager.set_current_index(index)

                self.update_playlist_ui()

                # Lade Video
                self.video_player.load_video(filepath)

                # Info-Overlay vorbereiten
                self.info_label.set_opacity(0.0)

                # Untertitel-, Audio-, Speed- und Equalizer-Menü zurücksetzen
                self.subtitle_button.set_sensitive(False)
                self.audio_button.set_sensitive(False)
                self.speed_button.set_sensitive(True)  # Speed ist immer für lokale Wiedergabe verfügbar
                self.equalizer_button.set_sensitive(True)  # Equalizer ist immer für lokale Wiedergabe verfügbar

                # A-B Loop Buttons aktivieren
                self.ab_button_a.set_sensitive(True)
                self.ab_button_b.set_sensitive(True)

                # Go-To Button aktivieren
                self.goto_button.set_sensitive(True)

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
            # Speichere Gerät in Config
            self.config.set_setting("chromecast_device", device_name)
        else:
            self.status_label.set_text(f"Verbindung fehlgeschlagen")
        return False

    def on_mode_changed(self, switch, gparam):
        """Wechselt zwischen lokalem und Chromecast-Modus"""
        if switch.get_active():
            # Wechsel zu Chromecast-Modus
            self.play_mode = "chromecast"
            self.config.set_setting("play_mode", "chromecast")
            self.mode_label.set_text("Chromecast")

            # Stoppe lokale Wiedergabe falls aktiv
            current_state = self.video_player.playbin.get_state(0).state
            if current_state in (Gst.State.PLAYING, Gst.State.PAUSED):
                print("Stoppe lokale Wiedergabe...")
                self.video_player.stop()

            # Synchronisiere Lautstärke zum Chromecast
            if self.cast_manager.selected_cast:
                current_volume = self.volume_scale.get_value() / 100.0
                def sync_volume():
                    self.cast_manager.set_volume(current_volume)

                thread = threading.Thread(target=sync_volume, daemon=True)
                thread.start()

            # Wenn ein Video geladen ist und ein Chromecast verbunden ist,
            # starte automatisch das Streaming
            if self.current_video_path and self.cast_manager.selected_cast:
                self.status_label.set_text("Chromecast-Modus: Bereit")
                print("Chromecast-Modus aktiv. Drücke Play, um das Streaming zu starten.")
            elif self.current_video_path and not self.cast_manager.selected_cast:
                self.status_label.set_text("Chromecast-Modus - Kein Gerät verbunden")
            else:
                self.status_label.set_text("Chromecast-Modus")
        else:
            # Wechsel zu Lokal-Modus
            self.play_mode = "local"
            self.config.set_setting("play_mode", "local")
            self.mode_label.set_text("Lokal")

            # Synchronisiere Lautstärke zum lokalen Player
            current_volume = self.volume_scale.get_value() / 100.0
            self.video_player.set_volume(current_volume)

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
            self.play_button.set_icon_name("media-playback-pause-symbolic")
            self.play_button.disconnect_by_func(self.on_play)
            self.play_button.connect("clicked", self.on_pause)
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
                self.play_button.set_icon_name("media-playback-pause-symbolic")
                self.play_button.disconnect_by_func(self.on_play)
                self.play_button.connect("clicked", self.on_pause)
            elif self.current_video_path and self.cast_manager.selected_cast:
                # Verhindere Standby während Streaming
                # Starte HTTP-Server und streame zu Chromecast
                self.status_label.set_text("Starte Streaming...")
                self.loading_spinner.start()
                self.loading_spinner.set_visible(True)
                self.play_button.set_sensitive(False)

                def start_streaming():
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
                                GLib.idle_add(lambda: (
                                    self.status_label.set_text("Streaming läuft..."),
                                    self.start_timeline_updates(),
                                    self.inhibit_suspend(),
                                    self.loading_spinner.stop(),
                                    self.loading_spinner.set_visible(False),
                                    self.play_button.set_sensitive(True),
                                    self.play_button.set_icon_name("media-playback-pause-symbolic"),
                                    self.play_button.disconnect_by_func(self.on_play),
                                    self.play_button.connect("clicked", self.on_pause)
                                ))
                            else:
                                GLib.idle_add(lambda: (
                                    self.status_label.set_text("Streaming fehlgeschlagen"),
                                    self.uninhibit_suspend(),
                                    self.loading_spinner.stop(),
                                    self.loading_spinner.set_visible(False),
                                    self.play_button.set_sensitive(True)
                                ))
                        else:
                            GLib.idle_add(lambda: (
                                self.status_label.set_text("HTTP-Server-Fehler"),
                                self.uninhibit_suspend(),
                                self.loading_spinner.stop(),
                                self.loading_spinner.set_visible(False),
                                self.play_button.set_sensitive(True)
                            ))
                    except Exception as e:
                        print(f"Streaming-Fehler: {e}")
                        import traceback
                        traceback.print_exc()
                        GLib.idle_add(lambda: (
                            self.status_label.set_text(f"Fehler: {str(e)}"),
                            self.uninhibit_suspend(),
                            self.loading_spinner.stop(),
                            self.loading_spinner.set_visible(False),
                            self.play_button.set_sensitive(True)
                        ))

                thread = threading.Thread(target=start_streaming, daemon=True)
                thread.start()

    def on_pause(self, button):
        """Pausiert die Wiedergabe"""
        if self.play_mode == "local":
            self.video_player.pause()
            self.play_button.set_icon_name("media-playback-start-symbolic")
            self.play_button.disconnect_by_func(self.on_pause)
            self.play_button.connect("clicked", self.on_play)
        else:
            self.cast_manager.pause()
            # Bei Pause Standby wieder erlauben
            self.uninhibit_suspend()
            self.play_button.set_icon_name("media-playback-start-symbolic")
            self.play_button.disconnect_by_func(self.on_pause)
            self.play_button.connect("clicked", self.on_play)

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
        
        # Play-Button zurücksetzen
        self.play_button.set_icon_name("media-playback-start-symbolic")
        self.play_button.disconnect_by_func(self.on_pause)
        self.play_button.connect("clicked", self.on_play)

    def on_volume_changed(self, scale):
        """Wird aufgerufen, wenn der Lautstärke-Slider bewegt wird"""
        volume_percent = scale.get_value()
        volume = volume_percent / 100.0  # Konvertiere 0-100 zu 0.0-1.0

        # Speichere Lautstärke in Config
        self.config.set_setting("volume", volume)

        # Wenn manuell lauter gestellt wird, ist es nicht mehr stummgeschaltet
        if volume > 0:
            self.is_muted = False

        self._set_current_volume(volume)

    def _set_current_volume(self, volume):
        """Interne Hilfsfunktion zum Setzen der Lautstärke im aktuellen Modus."""
        if self.play_mode == "local":
            self.video_player.set_volume(volume)
        elif self.cast_manager.selected_cast:
            # Chromecast-Lautstärke in Thread setzen um UI nicht zu blockieren
            def set_chromecast_volume():
                self.cast_manager.set_volume(volume)

            thread = threading.Thread(target=set_chromecast_volume, daemon=True)
            thread.start()

    def on_add_to_playlist(self, button):
        """Öffnet Dialog zum Hinzufügen von Videos zur Playlist"""
        dialog = Gtk.FileDialog()

        # Filter für Video-Dateien
        filter_video = Gtk.FileFilter()
        filter_video.set_name("Video-Dateien")
        filter_video.add_mime_type("video/*")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_video)
        dialog.set_filters(filters)

        # Letztes Verzeichnis aus Config verwenden
        last_dir = self.config.get_setting("last_directory")
        if last_dir and Path(last_dir).exists():
            dialog.set_initial_folder(Gio.File.new_for_path(last_dir))

        dialog.open_multiple(self, None, self.on_playlist_files_selected)

    def on_playlist_files_selected(self, dialog, result):
        """Callback wenn Dateien für Playlist ausgewählt wurden"""
        try:
            files = dialog.open_multiple_finish(result)
            if files:
                for i in range(files.get_n_items()):
                    file = files.get_item(i)
                    filepath = file.get_path()
                    self.playlist_manager.add_video(filepath)

                    # Speichere Verzeichnis in Config
                    self.config.set_setting("last_directory", str(Path(filepath).parent))

                self.update_playlist_ui()
        except Exception as e:
            print(f"Fehler beim Hinzufügen zur Playlist: {e}")

    def on_import_playlist(self, button):
        """Öffnet Dialog zum Importieren einer Playlist-Datei."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Playlist importieren")

        # Filter für Playlist-Dateien
        filter_pls = Gtk.FileFilter()
        filter_pls.set_name("PLS Playlist (*.pls)")
        filter_pls.add_pattern("*.pls")

        filter_m3u = Gtk.FileFilter()
        filter_m3u.set_name("M3U Playlist (*.m3u, *.m3u8)")
        filter_m3u.add_pattern("*.m3u")
        filter_m3u.add_pattern("*.m3u8")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_m3u)
        filters.append(filter_pls)
        dialog.set_filters(filters)

        # Letztes Verzeichnis aus Config verwenden
        last_dir = self.config.get_setting("last_directory")
        if last_dir and Path(last_dir).exists():
            dialog.set_initial_folder(Gio.File.new_for_path(last_dir))

        dialog.open(self, None, self.on_playlist_file_imported)

    def on_playlist_file_imported(self, dialog, result):
        """Callback, wenn eine Playlist-Datei ausgewählt wurde."""
        try:
            file = dialog.open_finish(result)
            if not file:
                return

            playlist_path = file.get_path()
            playlist_dir = Path(playlist_path).parent
            print(f"Importiere Playlist: {playlist_path}")

            # Speichere Verzeichnis in Config
            self.config.set_setting("last_directory", str(playlist_dir))

            video_paths = []
            with open(playlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                if playlist_path.lower().endswith(('.m3u', '.m3u8')):
                    # M3U/M3U8 Parsing
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            video_paths.append(line)
                elif playlist_path.lower().endswith('.pls'):
                    # PLS Parsing (einfach)
                    for line in f:
                        line = line.strip()
                        if line.lower().startswith('file'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                video_paths.append(parts[1])

            # Füge Videos zur Playlist hinzu
            added_count = 0
            for path in video_paths:
                # Mache Pfade absolut, falls sie relativ sind
                video_file = Path(path)
                if not video_file.is_absolute():
                    video_file = playlist_dir / video_file
                
                if video_file.exists() and self.playlist_manager.add_video(str(video_file)):
                    added_count += 1
            
            self.update_playlist_ui()
            self.status_label.set_text(f"{added_count} Video(s) aus Playlist importiert.")
        except Exception as e:
            print(f"Fehler beim Importieren der Playlist: {e}")

    def on_save_playlist(self, button):
        """Speichert die aktuelle Playlist."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Playlist speichern")
        
        # Setze Standard-Dateinamen
        dialog.set_initial_name("meine_playlist.m3u")
        
        # Letztes Verzeichnis aus Config verwenden
        last_dir = self.config.get_setting("last_directory")
        if last_dir and Path(last_dir).exists():
            dialog.set_initial_folder(Gio.File.new_for_path(last_dir))
        
        dialog.save(self, None, self.on_playlist_save_selected)

    def on_playlist_save_selected(self, dialog, result):
        """Callback, wenn ein Speicherort für die Playlist ausgewählt wurde."""
        try:
            file = dialog.save_finish(result)
            if not file:
                return
            
            save_path = file.get_path()
            if self.playlist_manager.save_playlist(save_path):
                self.status_label.set_text(f"Playlist gespeichert: {Path(save_path).name}")
                # Speichere Verzeichnis in Config
                self.config.set_setting("last_directory", str(Path(save_path).parent))
        except Exception as e:
            print(f"Fehler beim Speichern der Playlist: {e}")

    def on_shuffle_playlist(self, button):
        """Mischt die Playlist."""
        self.playlist_manager.shuffle_playlist()
        self.update_playlist_ui()
        self.status_label.set_text("Playlist gemischt")

    def update_playlist_ui(self):
        """Aktualisiert die Playlist-UI"""
        # Leere aktuelle Liste
        while True:
            row = self.playlist_listbox.get_row_at_index(0)
            if row is None:
                break
            self.playlist_listbox.remove(row)

        # Füge alle Playlist-Einträge hinzu
        for index, video_path in enumerate(self.playlist_manager.playlist):
            row = Gtk.ListBoxRow()

            # Box für Eintrag
            entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            entry_box.set_margin_start(6)
            entry_box.set_margin_end(6)
            entry_box.set_margin_top(4)
            entry_box.set_margin_bottom(4)

            # Icon für aktuelles Video
            if index == self.playlist_manager.current_index:
                icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
                entry_box.append(icon)

            # Video-Name
            label = Gtk.Label(label=Path(video_path).name)
            label.set_xalign(0)
            label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
            label.set_hexpand(True)
            entry_box.append(label)

            # Entfernen-Button
            remove_button = Gtk.Button()
            remove_button.set_icon_name("edit-delete-symbolic")
            remove_button.set_has_frame(False)
            remove_button.connect("clicked", self.on_remove_from_playlist, index)
            entry_box.append(remove_button)

            row.set_child(entry_box)
            row.video_index = index
            self.playlist_listbox.append(row)

        # Aktualisiere Zähler
        count = self.playlist_manager.get_playlist_length()
        self.playlist_count_label.set_text(f"({count})")

        # Aktualisiere Button-Status
        self.update_playlist_button_states()

    def update_playlist_button_states(self):
        """Aktualisiert den Zustand der Previous/Next Buttons"""
        self.previous_button.set_sensitive(self.playlist_manager.has_previous())
        self.next_button.set_sensitive(self.playlist_manager.has_next())

    def on_remove_from_playlist(self, button, index):
        """Entfernt ein Video aus der Playlist"""
        self.playlist_manager.remove_video(index)
        self.update_playlist_ui()

    def on_clear_playlist(self, button):
        """Leert die gesamte Playlist"""
        self.playlist_manager.clear_playlist()
        self.update_playlist_ui()

    def on_playlist_item_selected(self, listbox, row):
        """Wird aufgerufen, wenn ein Playlist-Eintrag ausgewählt wird"""
        if row:
            index = row.video_index
            self.playlist_manager.set_current_index(index)
            video_path = self.playlist_manager.get_current_video()
            if video_path:
                self.load_video_with_bookmark_check(video_path)

    def on_next_video(self, button):
        """Springt zum nächsten Video in der Playlist"""
        next_video = self.playlist_manager.next_video()
        if next_video:
            self.load_video_with_bookmark_check(next_video)
            self.update_playlist_ui()

    def on_previous_video(self, button):
        """Springt zum vorherigen Video in der Playlist"""
        previous_video = self.playlist_manager.previous_video()
        if previous_video:
            self.load_video_with_bookmark_check(previous_video)
            self.update_playlist_ui()

    def load_video_with_bookmark_check(self, filepath):
        """Lädt ein Video und prüft ob ein Lesezeichen existiert"""
        # Prüfe ob Lesezeichen existiert
        if self.bookmark_manager.has_bookmark(filepath):
            position, duration = self.bookmark_manager.get_bookmark(filepath)
            if position and duration:
                # Zeige Dialog
                self.show_resume_dialog(filepath, position, duration)
                return

        # Kein Lesezeichen, normal starten
        self.load_and_play_video(filepath)

    def show_resume_dialog(self, filepath, position, duration, autoplay=True):
        """Zeigt Dialog zum Fortsetzen der Wiedergabe"""
        filename = Path(filepath).name
        time_str = self.bookmark_manager.format_time(position)

        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Wiedergabe fortsetzen?")
        dialog.set_body(f"Möchten Sie '{filename}' an der gespeicherten Position ({time_str}) fortsetzen?")

        dialog.add_response("cancel", "Von Anfang an")
        dialog.add_response("resume", "Fortsetzen")
        dialog.set_response_appearance("resume", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("resume")
        dialog.set_close_response("cancel")

        def on_response(dialog, response):
            if response == "resume":
                # Lade Video und springe zur Position
                self.load_and_play_video(filepath, resume_position=position, autoplay=autoplay)
            else:
                # Von vorne beginnen und Lesezeichen entfernen
                self.bookmark_manager.remove_bookmark(filepath)
                self.load_and_play_video(filepath, autoplay=autoplay)

        dialog.connect("response", on_response)
        dialog.present()

    def load_and_play_video(self, filepath, resume_position=None, autoplay=True):
        """Lädt und spielt ein Video ab"""
        # Speichere Position des vorherigen Videos
        if self.current_video_path and self.current_video_path != filepath:
            self.save_current_position()

        # Leere Thumbnail-Cache bei neuem Video
        self.thumbnail_cache.clear()
        self.last_thumbnail_position = None

        self.current_video_path = filepath
        filename = Path(filepath).name

        if self.play_mode == "local":
            self.video_player.load_video(filepath)
            if autoplay:
                self.video_player.play()
                self.start_timeline_updates()
            # Info-Overlay vorbereiten
            self.info_label.set_opacity(0.0)

            # Buttons für lokale Wiedergabe aktivieren/deaktivieren
            self.subtitle_button.set_sensitive(False)
            self.audio_button.set_sensitive(False)
            self.speed_button.set_sensitive(True)  # Speed ist immer für lokale Wiedergabe verfügbar
            self.equalizer_button.set_sensitive(True)  # Equalizer ist immer für lokale Wiedergabe verfügbar
            self.ab_button_a.set_sensitive(True)
            self.ab_button_b.set_sensitive(True)
            self.goto_button.set_sensitive(True)

            if autoplay:
                # Play-Button aktualisieren
                self.play_button.set_icon_name("media-playback-pause-symbolic")
                self.play_button.disconnect_by_func(self.on_play)
                self.play_button.connect("clicked", self.on_pause)
            
            self.status_label.set_text(f"Spielt: {filename}")

            # Timeline aktivieren nach kurzem Delay
            def enable_timeline():
                duration = self.video_player.get_duration()
                if duration > 0:
                    self.timeline_scale.set_sensitive(True)
                    self.duration_label.set_text(self.format_time(duration))
                    self.time_label.set_text("00:00")
                    self.timeline_scale.set_value(0)

                    # Wenn resume_position gesetzt ist, springe dorthin
                    if resume_position:
                        GLib.timeout_add(100, lambda: self.seek_to_position(resume_position))
                return False

            GLib.timeout_add(500, enable_timeline)
        else:
            # Chromecast-Modus
            if self.cast_manager.selected_cast:
                self.status_label.set_text(f"Streame: {filename}")
                self.loading_spinner.start()
                self.loading_spinner.set_visible(True)
                self.play_button.set_sensitive(False)
                
                # Starte Streaming in Thread
                def start_streaming():
                    video_path = filepath

                    # Konvertierung falls nötig
                    if video_path.lower().endswith(('.mkv', '.avi')):
                        GLib.idle_add(self.status_label.set_text, "Konvertiere Video...")
                        converted_path = self.video_converter.convert_to_mp4(video_path)
                        if converted_path:
                            video_path = converted_path

                    video_url = self.http_server.get_video_url(video_path)
                    if video_url:
                        success = self.cast_manager.play_video(video_path, video_url)
                        if success:
                            GLib.idle_add(lambda: (
                                self.status_label.set_text(f"Streamt: {filename}"),
                                self.start_timeline_updates(),
                                self.inhibit_suspend(),
                                self.loading_spinner.stop(),
                                self.loading_spinner.set_visible(False),
                                self.play_button.set_sensitive(True),
                                self.play_button.set_icon_name("media-playback-pause-symbolic"),
                                self.play_button.disconnect_by_func(self.on_play),
                                self.play_button.connect("clicked", self.on_pause)
                            ))
                        else:
                            GLib.idle_add(lambda: (
                                self.status_label.set_text("Streaming fehlgeschlagen"),
                                self.loading_spinner.stop(),
                                self.loading_spinner.set_visible(False),
                                self.play_button.set_sensitive(True)
                            ))
                    else:
                        GLib.idle_add(lambda: (
                            self.status_label.set_text("HTTP-Server-Fehler"),
                            self.loading_spinner.stop(),
                            self.loading_spinner.set_visible(False),
                            self.play_button.set_sensitive(True)
                        ))

                thread = threading.Thread(target=start_streaming, daemon=True)
                thread.start()

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Behandelt Tastendrücke auf dem Hauptfenster."""
        shortcuts = self.config.get_setting("keyboard_shortcuts", {})
        
        # Mapping von Key-Namen zu Gdk.KEY_* Konstanten
        key_map = {
            "space": Gdk.KEY_space,
            "F11": Gdk.KEY_F11,
            "f": Gdk.KEY_f,
            "F": Gdk.KEY_F,
            "Up": Gdk.KEY_Up,
            "Down": Gdk.KEY_Down,
            "Right": Gdk.KEY_Right,
            "Left": Gdk.KEY_Left,
            "m": Gdk.KEY_m,
            "M": Gdk.KEY_M,
            "n": Gdk.KEY_n,
            "N": Gdk.KEY_N,
            "p": Gdk.KEY_p,
            "P": Gdk.KEY_P,
            "s": Gdk.KEY_s,
            "S": Gdk.KEY_S,
            "a": Gdk.KEY_a,
            "A": Gdk.KEY_A,
            "b": Gdk.KEY_b,
            "B": Gdk.KEY_B,
            "c": Gdk.KEY_c,
            "C": Gdk.KEY_C,
            "g": Gdk.KEY_g,
            "G": Gdk.KEY_G
        }

        # Prüfe alle Shortcuts
        if keyval == key_map.get(shortcuts.get("fullscreen", "F11"), Gdk.KEY_F11):
            self.on_toggle_fullscreen(None)
            return True
        elif keyval == key_map.get(shortcuts.get("play_pause", "space"), Gdk.KEY_space):
            self.toggle_play_pause()
            return True
        elif keyval == key_map.get(shortcuts.get("seek_forward", "Right"), Gdk.KEY_Right):
            self.seek_relative(5)  # 5 Sekunden vorspulen
            return True
        elif keyval == key_map.get(shortcuts.get("seek_backward", "Left"), Gdk.KEY_Left):
            self.seek_relative(-5)  # 5 Sekunden zurückspulen
            return True
        elif keyval == key_map.get(shortcuts.get("volume_up", "Up"), Gdk.KEY_Up):
            self.change_volume_relative(0.05)  # Lautstärke +5%
            return True
        elif keyval == key_map.get(shortcuts.get("volume_down", "Down"), Gdk.KEY_Down):
            self.change_volume_relative(-0.05)  # Lautstärke -5%
            return True
        elif keyval == key_map.get(shortcuts.get("mute", "m"), Gdk.KEY_m):
            self.toggle_mute()
            return True
        elif keyval == key_map.get(shortcuts.get("next_video", "n"), Gdk.KEY_n):
            self.on_next_video(None)
            return True
        elif keyval == key_map.get(shortcuts.get("previous_video", "p"), Gdk.KEY_p):
            self.on_previous_video(None)
            return True
        elif keyval == key_map.get(shortcuts.get("screenshot", "s"), Gdk.KEY_s):
            self.take_screenshot()
            return True
        elif keyval == key_map.get(shortcuts.get("ab_loop_a", "a"), Gdk.KEY_a):
            if self.ab_button_a.get_sensitive():
                self.on_set_loop_a(None)
            return True
        elif keyval == key_map.get(shortcuts.get("ab_loop_b", "b"), Gdk.KEY_b):
            if self.ab_button_b.get_sensitive():
                self.on_set_loop_b(None)
            return True
        elif keyval == key_map.get(shortcuts.get("ab_loop_clear", "c"), Gdk.KEY_c):
            if self.ab_button_clear.get_sensitive():
                self.on_clear_loop(None)
            return True
        elif keyval == key_map.get(shortcuts.get("goto_time", "g"), Gdk.KEY_g):
            if self.goto_button.get_sensitive():
                self.on_show_goto_dialog(None)
            return True
        return False

    def take_screenshot(self):
        """Nimmt einen Screenshot und speichert ihn"""
        if self.play_mode != "local":
            self.status_label.set_text("Screenshots nur bei lokaler Wiedergabe möglich")
            return

        # Erstelle Screenshots-Verzeichnis
        screenshots_dir = Path.home() / "Pictures" / "Video-Screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Generiere Dateinamen mit Timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Versuche Video-Namen zu verwenden
        video_name = "screenshot"
        if self.current_video_path:
            video_name = Path(self.current_video_path).stem

        filename = f"{video_name}_{timestamp}.png"
        filepath = screenshots_dir / filename

        # Mache Screenshot
        success = self.video_player.take_screenshot(str(filepath))

        if success:
            self.status_label.set_text(f"Screenshot gespeichert: {filename}")
        else:
            self.status_label.set_text("Screenshot fehlgeschlagen")

    def seek_relative(self, seconds):
        """Spult relativ zur aktuellen Position."""
        current_pos = self.get_current_position()
        duration = self.get_current_duration()
        if duration > 0:
            new_pos = max(0, min(duration, current_pos + seconds))
            self.perform_seek(new_pos)

    def toggle_play_pause(self):
        """Wechselt zwischen Wiedergabe und Pause."""
        is_playing = False
        if self.play_mode == "local":
            state = self.video_player.playbin.get_state(0).state
            is_playing = (state == Gst.State.PLAYING)
        elif self.cast_manager.mc and self.cast_manager.mc.status:
            is_playing = (self.cast_manager.mc.status.player_state == "PLAYING")

        if is_playing:
            self.on_pause(None)
        else:
            self.on_play(None)

    def change_volume_relative(self, delta):
        """Ändert die Lautstärke relativ zum aktuellen Wert."""
        current_volume_percent = self.volume_scale.get_value()
        new_volume_percent = current_volume_percent + (delta * 100)
        new_volume_percent = max(0, min(100, new_volume_percent)) # Begrenze auf 0-100
        self.volume_scale.set_value(new_volume_percent)

    def toggle_mute(self):
        """Schaltet den Ton stumm oder wieder an."""
        if self.is_muted:
            # Ton wieder an
            self.volume_scale.set_value(self.last_volume * 100)
            self.is_muted = False
        else:
            # Stummschalten
            self.last_volume = self.volume_scale.get_value() / 100.0
            if self.last_volume > 0: # Nur stummschalten, wenn nicht schon auf 0
                self.volume_scale.set_value(0)
                self.is_muted = True

    def on_toggle_fullscreen(self, button):
        """Schaltet den Vollbild-Modus um."""
        is_currently_fullscreen = self.is_fullscreen()
        self._toggle_ui_for_fullscreen(not is_currently_fullscreen)

        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()

    def _toggle_ui_for_fullscreen(self, fullscreen_active):
        """Zeigt/versteckt UI-Elemente für den Vollbildmodus."""
        self.main_box.get_first_child().set_visible(not fullscreen_active) # HeaderBar
        self.sidebar.set_visible(not fullscreen_active)
        self.timeline_widget.set_visible(not fullscreen_active)
        self.control_box.set_visible(not fullscreen_active)

    def show_video_info(self, video_info):
        """Zeigt das Info-Overlay für einige Sekunden an."""
        info_text = (
            f"<b>Auflösung:</b> {video_info['resolution']}\n"
            f"<b>Codec:</b> {video_info['codec']}\n"
            f"<b>Bitrate:</b> {video_info['bitrate']}"
        )
        self.info_label.set_markup(info_text)

        # Starte den Timer zum Ausblenden nur, wenn das Overlay noch nicht sichtbar ist.
        # Dies verhindert, dass der Timer bei jeder kleinen Info-Aktualisierung neu startet.
        if self.info_label.get_opacity() < 1.0:
            self.info_label.set_opacity(1.0)
            def hide_overlay():
                self.info_label.set_opacity(0.0)
                return False # Nur einmal ausführen
            GLib.timeout_add_seconds(5, hide_overlay)

        return False # Verhindert, dass der Callback erneut aufgerufen wird

    def update_media_menus(self):
        """Aktualisiert Untertitel-, Audio- und Kapitel-Menüs."""
        self.update_subtitle_menu()
        self.update_audio_menu()
        self.update_chapters_menu()
        return False

    def update_subtitle_menu(self):
        """Aktualisiert das Untertitel-Menü basierend auf verfügbaren Spuren."""
        print("Suche nach Untertitel-Spuren...")
        tracks = self.video_player.get_subtitle_tracks()

        if not tracks:
            print("Keine Untertitel gefunden.")
            self.subtitle_button.set_sensitive(False)
            return False

        print(f"{len(tracks)} Untertitel-Spur(en) gefunden.")

        # Erstelle ein neues Menü-Modell
        menu_model = Gio.Menu()

        # Eintrag zum Deaktivieren
        menu_model.append("Deaktivieren", "win.set_subtitle(-1)")

        # Einträge für jede Spur
        for track in tracks:
            menu_model.append(track["description"], f"win.set_subtitle({track['index']})")

        self.subtitle_popover.set_menu_model(menu_model)
        self.subtitle_button.set_sensitive(True)
        return False # Nur einmal ausführen

    def update_audio_menu(self):
        """Aktualisiert das Audio-Menü basierend auf verfügbaren Spuren."""
        print("Suche nach Audio-Spuren...")
        tracks = self.video_player.get_audio_tracks()

        if not tracks or len(tracks) <= 1:
            print(f"Nur {len(tracks)} Audio-Spur gefunden, kein Menü nötig.")
            self.audio_button.set_sensitive(False)
            return False

        print(f"{len(tracks)} Audio-Spur(en) gefunden.")

        # Erstelle ein neues Menü-Modell
        menu_model = Gio.Menu()

        # Einträge für jede Spur
        for track in tracks:
            menu_model.append(track["description"], f"win.set_audio({track['index']})")

        self.audio_popover.set_menu_model(menu_model)
        self.audio_button.set_sensitive(True)
        return False # Nur einmal ausführen

    def update_chapters_menu(self):
        """Aktualisiert das Kapitel-Menü basierend auf verfügbaren Kapiteln."""
        print("Suche nach Kapiteln...")
        chapters = self.video_player.get_chapters()

        if not chapters:
            print("Keine Kapitel gefunden.")
            self.chapters_button.set_sensitive(False)
            return False

        print(f"{len(chapters)} Kapitel gefunden.")

        # Erstelle ein neues Menü-Modell
        menu_model = Gio.Menu()

        # Einträge für jedes Kapitel
        for chapter in chapters:
            # Format: "Kapitel 1: Titel (0:05:30)"
            time_str = self.format_time(chapter['start'])
            label = f"{chapter['title']} ({time_str})"
            # Verwende die Start-Zeit als Parameter für die Action
            menu_model.append(label, f"win.goto_chapter({chapter['start']})")

        self.chapters_popover.set_menu_model(menu_model)
        self.chapters_button.set_sensitive(True)
        return False # Nur einmal ausführen

    def on_set_subtitle(self, action, param):
        """Wird aufgerufen, wenn ein Untertitel aus dem Menü ausgewählt wird."""
        index = param.get_int32()
        self.video_player.set_subtitle_track(index)
        print(f"Untertitel-Spur auf {index} gesetzt.")

    def on_set_audio(self, action, param):
        """Wird aufgerufen, wenn eine Audio-Spur aus dem Menü ausgewählt wird."""
        index = param.get_int32()
        self.video_player.set_audio_track(index)
        print(f"Audio-Spur auf {index} gesetzt.")

    def on_goto_chapter(self, action, param):
        """Wird aufgerufen, wenn ein Kapitel aus dem Menü ausgewählt wird."""
        start_time = param.get_double()
        self.seek_to_position(start_time)
        self.status_label.set_text(f"Springe zu Kapitel bei {self.format_time(start_time)}")
        print(f"Springe zu Kapitel bei {start_time:.1f}s")

    def on_set_speed(self, action, param):
        """Wird aufgerufen, wenn die Wiedergabegeschwindigkeit geändert wird."""
        speed = param.get_double()
        self.current_playback_rate = speed

        # Nur für lokale Wiedergabe (Chromecast unterstützt keine variable Geschwindigkeit)
        if self.play_mode == "local":
            self.video_player.set_playback_rate(speed)
            self.video_player._playback_rate = speed
            self.status_label.set_text(f"Geschwindigkeit: {speed}x")
        else:
            self.status_label.set_text("Geschwindigkeitsänderung nur für lokale Wiedergabe")

    def on_show_about(self, button):
        """Zeigt About-Dialog"""
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="Video Chromecast Player",
            application_icon="com.videocast.player",
            developer_name="DaHool",
            version="1.8.0",
            developers=["DaHool"],
            copyright="© 2025 DaHool",
            license_type=Gtk.License.MIT_X11,
            website="https://github.com/berlinux2016/gnome-chromecast-player",
            issue_url="https://github.com/berlinux2016/gnome-chromecast-player/issues",
            comments="Ein moderner GTK4-Videoplayer mit Chromecast-Unterstützung, der für eine nahtlose Wiedergabe sowohl lokal als auch auf Chromecast-Geräten optimiert ist. Inklusive Hardware-Beschleunigung für AMD und NVIDIA GPUs.\n\nMit Liebe für Simone programmiert ❤️"
        )

        # Füge Version-Informationen als Credit-Sections hinzu
        about.add_credit_section(
            "Was ist neu in Version 1.8.0?",
            [
                "Go-To-Zeit - Sprung zu bestimmter Zeitposition (G-Taste)",
                "Kapitel-Erkennung - Navigation durch MKV/MP4 Kapitel",
                "Timeline-Thumbnails - Vorschau beim Hovern über Timeline",
                "Go-To-Button in Steuerungsleiste mit Dialog (MM:SS / HH:MM:SS)",
                "Kapitel-Button in Header-Bar zeigt alle verfügbaren Kapitel",
                "Thumbnail-Popover mit 160x90 Vorschau und intelligentem Caching"
            ]
        )

        about.add_credit_section(
            "Features in Version 1.7.0",
            [
                "Video-Equalizer - Helligkeit, Kontrast, Sättigung, Farbton",
                "A-B Loop - Wiederholungsschleife für Lern-Videos",
                "Equalizer-Button mit 4 Slidern und Reset-Funktion",
                "A-B Loop Buttons (A, B, Clear) in Kontrollleiste",
                "Tastaturverknüpfungen: A (Loop Start), B (Loop Ende), C (Clear)"
            ]
        )

        about.add_credit_section(
            "Features in Version 1.6.0",
            [
                "Wiedergabegeschwindigkeit - 0.5x bis 2.0x einstellbar",
                "Screenshot-Funktion - S-Taste für Frame-Capture",
                "Geschwindigkeits-Button in Header-Bar",
                "Auto-Speicherung von Screenshots in ~/Pictures/Video-Screenshots/"
            ]
        )

        about.add_credit_section(
            "Features in Version 1.5.0",
            [
                "Audio-Track-Auswahl - Wechsel zwischen mehreren Audio-Spuren",
                "Lesezeichen/Resume - Automatisches Speichern und Fortsetzen",
                "Intelligentes Lesezeichen-System",
                "Resume-Dialog beim Öffnen gespeicherter Videos"
            ]
        )

        about.add_credit_section(
            "Features in Version 1.4.0",
            [
                "Abspiellisten-Import - M3U und PLS Format",
                "Tastatur-Shortcuts - Leertaste, Pfeiltasten, etc."
            ]
        )

        about.add_credit_section(
            "Features in Version 1.3.0",
            [
                "Vollbild-Modus - F11 für Vollbild",
                "Drag & Drop - Videos ins Fenster ziehen",
                "Video-Info-Overlay - Codec, Auflösung, Bitrate",
                "Untertitel-Support - SRT, ASS, VTT"
            ]
        )

        about.add_credit_section(
            "Features in Version 1.0-1.2",
            [
                "GTK4/Libadwaita UI im GNOME-Stil",
                "Hardware-Beschleunigung (AMD VA-API, NVIDIA NVDEC)",
                "Chromecast-Streaming mit HTTP-Server",
                "Automatische MKV/AVI zu MP4 Konvertierung",
                "Playlist-Unterstützung mit Auto-Advance",
                "Timeline/Seek-Funktion",
                "Lautstärkeregelung"
            ]
        )

        about.present()      

    def on_close_request(self, window):
        """Cleanup beim Schließen der Anwendung"""
        print("Beende Anwendung, räume auf...")

        # Speichere aktuelle Video-Position als Lesezeichen
        self.save_current_position()

        # Speichere Fenstergröße
        width, height = self.get_default_size()
        self.config.set_setting("window_width", width)
        self.config.set_setting("window_height", height)

        # Speichere aktuelle Lautstärke
        self.config.set_setting("volume", self.volume_scale.get_value() / 100.0)

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

        # Aktionen für das Menü (z.B. Untertitel, Audio und Geschwindigkeit)
        subtitle_action = Gio.SimpleAction.new_stateful("set_subtitle", GLib.VariantType.new('i'), GLib.Variant('i', -1))
        subtitle_action.connect("activate", self.on_app_set_subtitle)
        self.add_action(subtitle_action)

        audio_action = Gio.SimpleAction.new_stateful("set_audio", GLib.VariantType.new('i'), GLib.Variant('i', 0))
        audio_action.connect("activate", self.on_app_set_audio)
        self.add_action(audio_action)

        speed_action = Gio.SimpleAction.new_stateful("set_speed", GLib.VariantType.new('d'), GLib.Variant('d', 1.0))
        speed_action.connect("activate", self.on_app_set_speed)
        self.add_action(speed_action)

    def on_activate(self, app):
        self.win = VideoPlayerWindow(application=app)
        self.win.present()

    def on_app_set_subtitle(self, action, param):
        """Leitet die Untertitel-Aktion an das Fenster weiter."""
        if self.win:
            self.win.on_set_subtitle(action, param)

    def on_app_set_audio(self, action, param):
        """Leitet die Audio-Aktion an das Fenster weiter."""
        if self.win:
            self.win.on_set_audio(action, param)

    def on_app_set_speed(self, action, param):
        """Leitet die Geschwindigkeits-Aktion an das Fenster weiter."""
        if self.win:
            self.win.on_set_speed(action, param)


def main():
    app = VideoPlayerApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())