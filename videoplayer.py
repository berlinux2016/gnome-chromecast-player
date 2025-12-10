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
from enum import Enum
import hashlib
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote
from queue import Queue

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Adw, Gst, GLib, GstVideo, Gdk, Gio, GdkPixbuf
import pychromecast
from zeroconf import Zeroconf
from pychromecast.controllers.youtube import YouTubeController

class LoopMode(Enum):
    """Enum für die Wiederholungsmodi der Playlist."""
    NONE = 0
    ONE = 1
    ALL = 2

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
            "loop_mode": "NONE",
            "equalizer": None,
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
                "previous_video": "p",
                "screenshot": "s",
                "ab_loop_a": "a",
                "ab_loop_b": "b",
                "ab_loop_clear": "c",
                "goto_time": "g",
                "toggle_info": "i"
            }
        }
        self.playlist_file = self.config_dir / "playlist.json"
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

    def load_playlist(self):
        """Lädt die letzte Playlist aus einer Datei."""
        if self.playlist_file.exists():
            try:
                with open(self.playlist_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden der Playlist: {e}")
        return []

    def save_playlist(self, playlist):
        """Speichert die aktuelle Playlist in einer Datei."""
        try:
            with open(self.playlist_file, 'w') as f:
                json.dump(playlist, f)
        except Exception as e:
            print(f"Fehler beim Speichern der Playlist: {e}")


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

    def enable_subtitles(self, subtitle_url, subtitle_lang='en-US', subtitle_name='Subtitles'):
        """Aktiviert Untertitel für Chromecast-Wiedergabe

        Args:
            subtitle_url (str): URL zur Untertitel-Datei (SRT, VTT)
            subtitle_lang (str): Sprach-Code (z.B. 'de-DE', 'en-US')
            subtitle_name (str): Anzeige-Name für Untertitel
        """
        if not self.mc or not self.mc.status:
            print("✗ Kein aktiver Chromecast-Stream")
            return False

        try:
            print(f"\n=== Aktiviere Chromecast-Untertitel ===")
            print(f"URL: {subtitle_url}")
            print(f"Sprache: {subtitle_lang}")

            # Erstelle Track-Metadaten
            tracks = [{
                'trackId': 1,
                'type': 'TEXT',
                'trackContentId': subtitle_url,
                'trackContentType': 'text/vtt',  # VTT wird besser unterstützt als SRT
                'name': subtitle_name,
                'language': subtitle_lang,
                'subtype': 'SUBTITLES'
            }]

            # Update Media mit Untertiteln
            current_time = self.mc.status.current_time or 0
            self.mc.play_media(
                self.mc.status.content_id,
                self.mc.status.content_type,
                current_time=current_time,
                autoplay=True,
                subtitles=tracks
            )

            # Aktiviere erste Untertitel-Spur
            self.mc.update_status()
            time.sleep(0.5)
            self.mc.enable_subtitle(1)

            print("✓ Untertitel aktiviert")
            return True

        except Exception as e:
            print(f"✗ Fehler beim Aktivieren der Untertitel: {e}")
            import traceback
            traceback.print_exc()
            return False

    def disable_subtitles(self):
        """Deaktiviert Untertitel für Chromecast"""
        if self.mc:
            try:
                self.mc.disable_subtitle()
                print("✓ Untertitel deaktiviert")
                return True
            except Exception as e:
                print(f"✗ Fehler beim Deaktivieren der Untertitel: {e}")
                return False
        return False

    def set_audio_track(self, track_id):
        """Wählt eine Audio-Spur für Chromecast aus

        Args:
            track_id (int): Track-ID der gewünschten Audio-Spur
        """
        if not self.mc:
            print("✗ Kein aktiver Chromecast-Stream")
            return False

        try:
            print(f"Wähle Chromecast Audio-Track {track_id}")
            # Nutze die native Chromecast-Funktion zum Wechseln der Audio-Spur
            self.mc.enable_subtitle(track_id)  # Trotz des Namens funktioniert es auch für Audio
            print(f"✓ Audio-Track {track_id} ausgewählt")
            return True
        except Exception as e:
            print(f"✗ Fehler beim Wechseln der Audio-Spur: {e}")
            return False

    def get_extended_status(self):
        """Gibt erweiterte Chromecast-Status-Informationen zurück

        Returns:
            dict: Status-Dictionary mit allen verfügbaren Informationen
        """
        if not self.selected_cast:
            return {
                'connected': False,
                'device_name': 'Nicht verbunden',
                'app_name': 'N/A',
                'player_state': 'IDLE',
                'volume': 0.0,
                'is_muted': False,
                'current_time': 0.0,
                'duration': 0.0,
                'buffer_percent': 0,
                'media_title': 'N/A',
                'content_type': 'N/A'
            }

        status = {
            'connected': True,
            'device_name': self.selected_cast.name,
            'device_model': self.selected_cast.model_name,
            'device_uuid': self.selected_cast.uuid,
            'cast_type': self.selected_cast.cast_type,
            'app_name': self.selected_cast.app_display_name or 'Keine App',
            'app_id': self.selected_cast.app_id,
            'volume': self.selected_cast.status.volume_level if self.selected_cast.status else 0.0,
            'is_muted': self.selected_cast.status.volume_muted if self.selected_cast.status else False,
        }

        if self.mc and self.mc.status:
            media_status = self.mc.status
            status.update({
                'player_state': media_status.player_state,
                'current_time': media_status.current_time or 0.0,
                'duration': media_status.duration or 0.0,
                'media_title': media_status.title or 'Unbekannt',
                'content_type': media_status.content_type or 'N/A',
                'content_id': media_status.content_id or 'N/A',
                'stream_type': media_status.stream_type,
                'idle_reason': getattr(media_status, 'idle_reason', None),
                'supports_pause': media_status.supports_pause,
                'supports_seek': media_status.supports_seek,
            })

            # Berechne Buffer-Prozentsatz
            if media_status.duration and media_status.duration > 0:
                status['buffer_percent'] = int((media_status.current_time / media_status.duration) * 100)
            else:
                status['buffer_percent'] = 0
        else:
            status.update({
                'player_state': 'IDLE',
                'current_time': 0.0,
                'duration': 0.0,
                'buffer_percent': 0,
                'media_title': 'N/A',
                'content_type': 'N/A'
            })

        return status

    def discover_cast_groups(self):
        """Entdeckt Chromecast-Gruppen für Multi-Room-Audio

        Returns:
            list: Liste von gefundenen Gruppen
        """
        groups = []

        if not self._zconf_instance:
            print("✗ Zeroconf nicht initialisiert")
            return groups

        try:
            print("\n=== Suche nach Chromecast-Gruppen ===")

            # Durchsuche alle gefundenen Geräte nach Gruppen
            for uuid, service in self._found_devices.items():
                # Gruppen haben meist "Google Cast Group" im Namen oder sind vom Typ "group"
                if hasattr(service, 'cast_type') and service.cast_type == 'group':
                    groups.append({
                        'uuid': uuid,
                        'name': service.friendly_name,
                        'service': service
                    })
                    print(f"✓ Gruppe gefunden: {service.friendly_name}")

            if not groups:
                print("ℹ Keine Chromecast-Gruppen gefunden")
                print("  Hinweis: Erstelle Gruppen in der Google Home App")
            else:
                print(f"✓ {len(groups)} Gruppe(n) gefunden")

            return groups

        except Exception as e:
            print(f"✗ Fehler bei der Gruppen-Suche: {e}")
            import traceback
            traceback.print_exc()
            return groups

    def connect_to_group(self, group_service):
        """Verbindet mit einer Chromecast-Gruppe für Multi-Room-Audio

        Args:
            group_service: Service-Objekt der Gruppe

        Returns:
            bool: True bei erfolgreicher Verbindung
        """
        try:
            print(f"\n=== Verbinde mit Gruppe '{group_service.friendly_name}' ===")

            # Verbinde wie mit einem normalen Gerät
            success = self.connect_to_chromecast(group_service)

            if success:
                print("✓ Erfolgreich mit Gruppe verbunden")
                print("  Audio wird auf allen Geräten der Gruppe synchronisiert abgespielt")
                return True
            else:
                print("✗ Verbindung zur Gruppe fehlgeschlagen")
                return False

        except Exception as e:
            print(f"✗ Fehler bei Gruppen-Verbindung: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_group_members(self):
        """Gibt Mitglieder der aktuell verbundenen Gruppe zurück

        Returns:
            list: Liste von Geräte-Namen in der Gruppe
        """
        if not self.selected_cast:
            return []

        try:
            # Prüfe ob es eine Gruppe ist
            if hasattr(self.selected_cast, 'cast_type') and self.selected_cast.cast_type == 'group':
                # Versuche Gruppen-Informationen zu erhalten
                if hasattr(self.selected_cast, 'status') and hasattr(self.selected_cast.status, 'group_uuid'):
                    # Finde alle Geräte mit der gleichen Gruppen-UUID
                    members = []
                    group_uuid = self.selected_cast.status.group_uuid

                    for uuid, service in self._found_devices.items():
                        if hasattr(service, 'group_uuid') and service.group_uuid == group_uuid:
                            members.append(service.friendly_name)

                    return members

            return [self.selected_cast.name]  # Kein Gruppe, nur einzelnes Gerät

        except Exception as e:
            print(f"✗ Fehler beim Abrufen der Gruppen-Mitglieder: {e}")
            return []

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
        # Liste von Dictionaries: [{'path': '/path/to/file', 'display': 'filename'}, ...]
        self.playlist = []
        self.current_index = -1  # Aktueller Index in der Playlist
        self.play_history = []  # Wiedergabeverlauf
        self.playlist_file = None

    def add_video(self, video_path):
        """Fügt ein Video zur Playlist hinzu"""
        # Prüfe, ob der Pfad bereits existiert
        if not any(item['path'] == video_path for item in self.playlist):
            display_name = Path(video_path).name
            # Bei URLs einen lesbareren Namen generieren
            if video_path.startswith("http"):
                try:
                    parsed = urlparse(video_path)
                    display_name = parse_qs(parsed.query).get('v', [Path(parsed.path).name])[0]
                except Exception:
                    pass # Fallback auf den Dateinamen des Pfades
            self.playlist.append({'path': video_path, 'display': display_name})
            print(f"✓ Video zur Playlist hinzugefügt: {Path(video_path).name}")
            return True
        else:
            print(f"ℹ Video bereits in Playlist: {Path(video_path).name}")
            return False

    def remove_video(self, index):
        """Entfernt ein Video aus der Playlist"""
        if 0 <= index < len(self.playlist):
            removed = self.playlist.pop(index)
            print(f"✓ Video aus Playlist entfernt: {removed['display']}")
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
            return self.playlist[self.current_index]['path']
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
            video_item = self.playlist.pop(from_index)
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
                    video_name = video_path['display']
                    f.write(f"#EXTINF:-1,{video_name}\n")
                    f.write(f"{video_path['path']}\n")
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
        
        for video_item in self.playlist:
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

        # Video-Effekte-Pipeline
        # videobalance für Helligkeit, Kontrast, Sättigung, Farbton
        self.videobalance = Gst.ElementFactory.make("videobalance", "balance")

        # gamma für Gamma-Korrektur
        self.gamma = Gst.ElementFactory.make("gamma", "gamma")

        # videoflip für Rotation und Spiegelung
        self.videoflip = Gst.ElementFactory.make("videoflip", "flip")

        # videocrop für Zuschneiden
        self.videocrop = Gst.ElementFactory.make("videocrop", "crop")

        # videoscale für Zoom
        self.videoscale = Gst.ElementFactory.make("videoscale", "scale")

        # capsfilter für Zoom-Kontrolle
        self.zoom_capsfilter = Gst.ElementFactory.make("capsfilter", "zoomcaps")

        self.videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
        self.videoconvert2 = Gst.ElementFactory.make("videoconvert", "convert2")

        # Video-Sink für GTK
        self.gtksink = Gst.ElementFactory.make("gtk4paintablesink", "sink")

        # Erstelle bin mit Effekte-Kette: videobalance -> gamma -> videoflip -> videoscale -> zoom_capsfilter -> videocrop -> videoconvert -> gtksink
        video_bin = Gst.Bin.new("video_bin")
        video_bin.add(self.videobalance)
        video_bin.add(self.gamma)
        video_bin.add(self.videoconvert)
        video_bin.add(self.videoflip)
        video_bin.add(self.videoscale)
        video_bin.add(self.zoom_capsfilter)
        video_bin.add(self.videocrop)
        video_bin.add(self.videoconvert2)
        video_bin.add(self.gtksink)

        # Verknüpfe Elemente in der Reihenfolge
        self.videobalance.link(self.gamma)
        self.gamma.link(self.videoconvert)
        self.videoconvert.link(self.videoflip)
        self.videoflip.link(self.videoscale)
        self.videoscale.link(self.zoom_capsfilter)
        self.zoom_capsfilter.link(self.videocrop)
        self.videocrop.link(self.videoconvert2)
        self.videoconvert2.link(self.gtksink)

        # Erstelle Ghost-Pad für Eingang
        sink_pad = self.videobalance.get_static_pad("sink")
        ghost_pad = Gst.GhostPad.new("sink", sink_pad)
        video_bin.add_pad(ghost_pad)

        paintable = self.gtksink.get_property("paintable")
        self.video_widget.set_paintable(paintable)
        self.playbin.set_property("video-sink", video_bin)

        # Standard-Equalizer-Werte und Video-Effekte
        self.equalizer_settings = {
            'brightness': 0.0,
            'contrast': 1.0,
            'saturation': 1.0,
            'hue': 0.0,
            'gamma': 1.0,
            'rotation': 0,  # 0=none, 1=90°cw, 2=180°, 3=90°ccw, 4=horizontal-flip, 5=vertical-flip
            'zoom': 1.0,
            'crop_left': 0,
            'crop_right': 0,
            'crop_top': 0,
            'crop_bottom': 0
        }

        # Original Video-Dimensionen für Crop/Zoom
        self.original_video_width = 0
        self.original_video_height = 0

        self.append(self.video_widget)

        # Bus für Nachrichten
        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_gst_message)

        self.current_file = None
        self.current_uri = None  # URI für Thumbnail-Extraction
        self.hw_accel_enabled = False
        self.streams_ready_callback = None
        self.toc_ready_callback = None
        self.eos_callback = None
        self.info_callback = None
        # Zustand für Video-Infos, um Flackern zu vermeiden
        self._video_info = {
            "resolution": "N/A",
            "codec": "N/A",
            "bitrate": "N/A"
        }
        self._streams_info_updated_for_current_video = False

        self.thumbnail_cache = {}
        self.setup_performance_optimizations()

    def setup_performance_optimizations(self):
        """Setzt Performance-Optimierungen"""
        pass
    def setup_element(self, element, name):
        """Helper function to create and check for GStreamer elements."""
        elem = Gst.ElementFactory.make(name, None)
        if not elem:
            print(f"Failed to create GStreamer element: {name}")
        return elem


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
        #clear cache
        self.thumbnail_cache.clear()
        self.last_thumbnail_position = None

        # Cleanup alte Thumbnail-Pipeline
        if hasattr(self, 'thumbnail_pipeline') and self.thumbnail_pipeline:
            try:
                self.thumbnail_pipeline.set_state(Gst.State.NULL)
                self.thumbnail_pipeline = None
                self.thumbnail_appsink = None
            except:
                pass

        # Setze Video-Infos für neue Datei/Stream zurück
        self._video_info = {
            "resolution": "N/A",
            "codec": "N/A",
            "bitrate": "N/A"
        }
        self.current_file = filepath

        if filepath.startswith(("http://", "https")):
            uri = filepath
            self.current_uri = uri
            print(f"Lade Video-Stream: {uri}")
        elif filepath.startswith("fd://"):
            uri = filepath
            self.current_uri = uri # Für Streams ist die URI auch der "Pfad"
            print(f"Lade Video-Stream: {uri}")
        else:
            abs_path = str(Path(filepath).resolve())
            uri = f"file:///{abs_path}" if abs_path.startswith('/') else f"file://{abs_path}"
            self.current_uri = uri
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

        # Cleanup Thumbnail-Pipeline
        if hasattr(self, 'thumbnail_pipeline') and self.thumbnail_pipeline:
            try:
                self.thumbnail_pipeline.set_state(Gst.State.NULL)
                self.thumbnail_pipeline = None
                self.thumbnail_appsink = None
            except:
                pass

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

    def extract_video_thumbnail(self, video_path, thumbnail_path, width=80, height=60):
        """Extrahiert ein Thumbnail aus einem Video für die Playlist"""
        try:
            # Cache-Verzeichnis erstellen falls nicht vorhanden
            cache_dir = os.path.dirname(thumbnail_path)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            # Prüfe ob Thumbnail bereits existiert
            if os.path.exists(thumbnail_path):
                return True

            # Verwende ffmpeg für schnellere und zuverlässigere Thumbnail-Extraktion
            try:
                import subprocess
                # Extrahiere Frame bei 5 Sekunden
                cmd = [
                    'ffmpeg', '-y', '-ss', '5', '-i', video_path,
                    '-vframes', '1', '-vf', f'scale={width}:{height}',
                    thumbnail_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=3)

                if result.returncode == 0 and os.path.exists(thumbnail_path):
                    return True
            except Exception as e:
                print(f"ffmpeg Thumbnail-Extraktion fehlgeschlagen: {e}")

            # Fallback: Nutze GStreamer falls ffmpeg nicht verfügbar
            try:
                # Erstelle einen temporären Pipeline für Thumbnail-Extraktion
                pipeline_str = f'filesrc location="{video_path}" ! decodebin ! videoconvert ! videoscale ! video/x-raw,width={width},height={height} ! jpegenc ! filesink location="{thumbnail_path}"'

                pipeline = Gst.parse_launch(pipeline_str)
                bus = pipeline.get_bus()

                # Setze Pipeline auf PAUSED
                pipeline.set_state(Gst.State.PAUSED)

                # Warte auf PAUSED State mit Timeout
                ret = pipeline.get_state(3 * Gst.SECOND)
                if ret[0] == Gst.StateChangeReturn.SUCCESS or ret[0] == Gst.StateChangeReturn.ASYNC:
                    # Seek zu 5 Sekunden
                    pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, 5 * Gst.SECOND)


                    # Kurz abspielen und dann stoppen
                    pipeline.set_state(Gst.State.PLAYING)

                    # Warte auf EOS oder ERROR mit Timeout
                    bus.timed_pop_filtered(2 * Gst.SECOND, Gst.MessageType.EOS | Gst.MessageType.ERROR)

                    # Cleanup

                    pipeline.set_state(Gst.State.NULL)

                    if os.path.exists(thumbnail_path):
                        return True
                else:
                    pipeline.set_state(Gst.State.NULL)

            except Exception as e:
                print(f"GStreamer Thumbnail-Extraktion fehlgeschlagen: {e}")

            return False

        except Exception as e:
            print(f"Fehler beim Extrahieren des Thumbnails für {video_path}: {e}")
            return False

    def get_thumbnail_path(self, video_path):
        """Gibt den Pfad zum Thumbnail zurück (verwendet MD5 Hash des Pfads)"""
        # Erstelle eindeutigen Hash für Video-Pfad
        hash_obj = hashlib.md5(video_path.encode())
        hash_str = hash_obj.hexdigest()

        # Cache-Verzeichnis
        cache_dir = os.path.expanduser("~/.cache/gnome-chromecast-player/thumbnails")

        return os.path.join(cache_dir, f"{hash_str}.jpg")

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

    def set_gamma(self, gamma):
        """Setzt Gamma-Korrektur (0.01 bis 10.0, Standard: 1.0)"""
        gamma = max(0.01, min(10.0, gamma))
        self.gamma.set_property("gamma", gamma)
        self.equalizer_settings['gamma'] = gamma
        print(f"Gamma: {gamma}")

    def set_rotation(self, rotation):
        """Setzt Video-Rotation und Spiegelung

        Args:
            rotation (int):
                0 = none (identity)
                1 = 90° im Uhrzeigersinn (clockwise)
                2 = 180° (rotate-180)
                3 = 90° gegen Uhrzeigersinn (counterclockwise)
                4 = horizontal spiegeln (horizontal-flip)
                5 = vertikal spiegeln (vertical-flip)
                6 = obere linke Diagonale (upper-left-diagonal)
                7 = obere rechte Diagonale (upper-right-diagonal)
        """
        rotation = max(0, min(7, rotation))
        self.videoflip.set_property("method", rotation)
        self.equalizer_settings['rotation'] = rotation
        rotation_names = ["Keine", "90° CW", "180°", "90° CCW", "Horizontal", "Vertikal", "Diag↖", "Diag↗"]
        print(f"Rotation: {rotation_names[rotation]}")

    def set_zoom(self, zoom):
        """Setzt Zoom-Faktor (0.5 bis 5.0, Standard: 1.0)"""
        zoom = max(0.5, min(5.0, zoom))
        self.equalizer_settings['zoom'] = zoom

        # Zoom wird über capsfilter implementiert - Scale auf gewünschte Größe
        if self.original_video_width > 0 and self.original_video_height > 0:
            target_width = int(self.original_video_width * zoom)
            target_height = int(self.original_video_height * zoom)

            # Stelle sicher, dass die Dimensionen gerade sind, um GDK-Texturfehler zu vermeiden.
            # GDK kann bei einigen Formaten (wie I420) Probleme mit ungeraden Dimensionen haben.
            even_width = (target_width // 2) * 2
            even_height = (target_height // 2) * 2

            caps = Gst.Caps.from_string(f"video/x-raw,width={even_width},height={even_height}")
            self.zoom_capsfilter.set_property("caps", caps)
            print(f"Zoom: {zoom}x ({even_width}x{even_height})")
        else:
            print(f"Zoom: {zoom}x (warte auf Video-Dimensionen)")

    def set_crop(self, left=0, right=0, top=0, bottom=0):
        """Setzt Crop-Werte (in Pixeln von jeder Seite)

        Args:
            left (int): Pixel von links abschneiden
            right (int): Pixel von rechts abschneiden
            top (int): Pixel von oben abschneiden
            bottom (int): Pixel von unten abschneiden
        """
        self.videocrop.set_property("left", max(0, left))
        self.videocrop.set_property("right", max(0, right))
        self.videocrop.set_property("top", max(0, top))
        self.videocrop.set_property("bottom", max(0, bottom))

        self.equalizer_settings['crop_left'] = left
        self.equalizer_settings['crop_right'] = right
        self.equalizer_settings['crop_top'] = top
        self.equalizer_settings['crop_bottom'] = bottom

        if left > 0 or right > 0 or top > 0 or bottom > 0:
            print(f"Crop: L={left} R={right} T={top} B={bottom}")
        else:
            print("Crop: Deaktiviert")

    def reset_video_effects(self):
        """Setzt alle Video-Effekte auf Standard zurück"""
        self.reset_equalizer()
        self.set_gamma(1.0)
        self.set_rotation(0)
        self.set_zoom(1.0)
        self.set_crop(0, 0, 0, 0)
        print("Alle Video-Effekte zurückgesetzt")

    def apply_filter_preset(self, preset_name):
        """Wendet vordefinierte Filter-Presets an

        Args:
            preset_name (str): 'normal', 'sepia', 'grayscale', 'vintage', 'vivid', 'dark', 'bright'
        """
        presets = {
            'normal': {
                'brightness': 0.0, 'contrast': 1.0, 'saturation': 1.0, 'hue': 0.0, 'gamma': 1.0
            },
            'sepia': {
                'brightness': 0.1, 'contrast': 1.1, 'saturation': 0.4, 'hue': 0.15, 'gamma': 1.2
            },
            'grayscale': {
                'brightness': 0.0, 'contrast': 1.0, 'saturation': 0.0, 'hue': 0.0, 'gamma': 1.0
            },
            'blackwhite': {
                'brightness': 0.2, 'contrast': 1.5, 'saturation': 0.0, 'hue': 0.0, 'gamma': 1.0
            },
            'vintage': {
                'brightness': 0.05, 'contrast': 1.2, 'saturation': 0.7, 'hue': 0.1, 'gamma': 1.3
            },
            'vivid': {
                'brightness': 0.1, 'contrast': 1.3, 'saturation': 1.5, 'hue': 0.0, 'gamma': 0.9
            },
            'dark': {
                'brightness': -0.3, 'contrast': 1.2, 'saturation': 1.0, 'hue': 0.0, 'gamma': 1.5
            },
            'bright': {
                'brightness': 0.3, 'contrast': 0.9, 'saturation': 1.1, 'hue': 0.0, 'gamma': 0.8
            },
            'cold': {
                'brightness': 0.0, 'contrast': 1.1, 'saturation': 1.2, 'hue': -0.2, 'gamma': 1.0
            },
            'warm': {
                'brightness': 0.05, 'contrast': 1.0, 'saturation': 1.2, 'hue': 0.2, 'gamma': 1.1
            }
        }

        if preset_name in presets:
            preset = presets[preset_name]
            self.set_equalizer(
                brightness=preset['brightness'],
                contrast=preset['contrast'],
                saturation=preset['saturation'],
                hue=preset['hue']
            )
            self.set_gamma(preset['gamma'])
            print(f"Filter-Preset angewendet: {preset_name}")
        else:
            print(f"Unbekanntes Preset: {preset_name}")

    def _init_thumbnail_pipeline(self):
        """Initialisiert eine wiederverwendbare Pipeline für Thumbnails"""
        try:
            if hasattr(self, 'thumbnail_pipeline') and self.thumbnail_pipeline:
                self.thumbnail_pipeline.set_state(Gst.State.NULL)

            pipeline_str = f'uridecodebin uri="{self.current_uri}" ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=160,height=90 ! appsink name=sink sync=false'

            self.thumbnail_pipeline = Gst.parse_launch(pipeline_str)
            self.thumbnail_appsink = self.thumbnail_pipeline.get_by_name('sink')

            # Konfiguriere den appsink für schnelle Extraktion
            self.thumbnail_appsink.set_property('emit-signals', False)
            self.thumbnail_appsink.set_property('max-buffers', 1)
            self.thumbnail_appsink.set_property('drop', True)

            # Setze Pipeline in PAUSED state (nur einmal!)
            self.thumbnail_pipeline.set_state(Gst.State.PAUSED)

            # Warte bis bereit (nur beim ersten Mal)
            ret = self.thumbnail_pipeline.get_state(3 * Gst.SECOND)
            if ret[0] != Gst.StateChangeReturn.SUCCESS:
                self.thumbnail_pipeline.set_state(Gst.State.NULL)
                self.thumbnail_pipeline = None
                return False

            return True
        except Exception as e:
            print(f"Fehler beim Initialisieren der Thumbnail-Pipeline: {e}")
            self.thumbnail_pipeline = None
            return False

    def get_frame_at_position(self, position_seconds):
        """Extrahiert ein Frame an einer bestimmten Position als Pixbuf für Thumbnails

        Verwendet eine wiederverwendbare Pipeline für schnelles Frame-Extraction.
        """
        try:
            # Stelle sicher, dass Pipeline initialisiert ist
            if not hasattr(self, 'thumbnail_pipeline') or not self.thumbnail_pipeline:
                if not self._init_thumbnail_pipeline():
                    return None

            # Schnelles Seek - nur KEY_UNIT für Performance
            seek_flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT
            position_ns = int(position_seconds * Gst.SECOND)

            success = self.thumbnail_pipeline.seek_simple(
                Gst.Format.TIME,
                seek_flags,
                position_ns
            )

            if not success:
                return None

            # Kurzes Warten auf Seek (reduziert von 2s auf 0.5s)
            bus = self.thumbnail_pipeline.get_bus()
            msg = bus.timed_pop_filtered(
                int(0.5 * Gst.SECOND),
                Gst.MessageType.ASYNC_DONE | Gst.MessageType.ERROR
            )

            if not msg or msg.type == Gst.MessageType.ERROR:
                # Bei Fehler Pipeline neu initialisieren
                self._init_thumbnail_pipeline()
                return None

            # Hole Sample vom appsink
            sample = self.thumbnail_appsink.emit('pull-preroll')

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

                        buffer.unmap(map_info)
                        return pixbuf

                    except Exception as e:
                        buffer.unmap(map_info)
                        print(f"Fehler beim Pixbuf-Erstellen: {e}")

        except Exception as e:
            print(f"Fehler beim Thumbnail-Erstellen: {e}")
            # Bei Fehler Pipeline neu initialisieren
            try:
                self._init_thumbnail_pipeline()
            except:
                pass

        return None

    def parse_toc(self, toc):
        """Extrahiert Kapitel-Informationen aus dem Video"""
        chapters = []
        if not toc:
            return chapters

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
        
        if chapters:
            print(f"✓ {len(chapters)} Kapitel gefunden")
        else:
            print("ℹ Keine Kapitel im Video gefunden")
            
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

        elif t == Gst.MessageType.TOC:
            toc, _ = message.parse_toc()
            if toc and hasattr(self, 'toc_ready_callback'):
                # Sende TOC an die Haupt-UI-Klasse
                GLib.idle_add(self.toc_ready_callback, toc)

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

                                    # Speichere Original-Dimensionen für Crop/Zoom
                                    self.original_video_width = width
                                    self.original_video_height = height

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

        # Picture-in-Picture
        self.pip_window = None

        # Loop-Modus
        try:
            self.loop_mode = LoopMode[self.config.get_setting("loop_mode", "NONE")]
        except KeyError:
            self.loop_mode = LoopMode.NONE

        self.last_equalizer_settings = self.config.get_setting("equalizer")

        # Cleanup beim Schließen
        self.connect("close-request", self.on_close_request)

        # Hauptlayout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Header Bar
        self.setup_header_bar()

        # Content Box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.content_box.set_margin_start(12)
        self.content_box.set_margin_end(12)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(12)

        # Video Player und Info-Overlay
        self.video_overlay = Gtk.Overlay()
        self.content_box.append(self.video_overlay)

        self.video_player = VideoPlayer()

        self.video_overlay.set_child(self.video_player)

        self.info_label = Gtk.Label()
        self.info_label.set_valign(Gtk.Align.START)
        self.info_label.set_halign(Gtk.Align.START)
        self.info_label.set_margin_start(10)
        self.info_label.set_margin_top(10)
        self.info_label.set_margin_top(10)
        self.info_label.add_css_class("info-overlay")
        self.video_overlay.add_overlay(self.info_label)

        # Seitenleiste für Chromecast
        self.setup_sidebar()
        self.content_box.append(self.sidebar)

        self.main_box.append(self.content_box)

        # Timeline/Seek Bar
        self.timeline_widget = self.setup_timeline()
        self.main_box.append(self.timeline_widget)

        # Spiele-Modus (lokal oder chromecast) - muss vor setup_controls() initialisiert werden
        # Startet immer im lokalen Modus
        self.play_mode = "local"

        # Kontrollleiste
        self.setup_controls()
        self.main_box.append(self.control_box)

        self.set_content(self.main_box)

        # Timeline state tracking
        self.timeline_update_timeout = None
        self.is_seeking = False
        self.timeline_seek_handler_id = None
        self.info_overlay_timeout_id = None
        self.info_overlay_shown_for_current_video = False
        self.thumbnail_hover_timeout_id = None

        # Initialisiere Lautstärke
        saved_volume = self.config.get_setting("volume", 1.0)
        self.video_player.set_volume(saved_volume)
        self.volume_scale.set_value(saved_volume * 100)

        # Setze EOS-Callback für Auto-Advance
        self.video_player.eos_callback = self.on_video_ended

        # Setze Info-Callback
        # Doppelklick-Geste für Vollbildmodus
        click_gesture = Gtk.GestureClick.new()
        click_gesture.set_button(1) # Linke Maustaste
        click_gesture.connect("pressed", self.on_video_area_click)
        self.video_player.add_controller(click_gesture)


        # Setze Info-Callback
        self.video_player.info_callback = self.show_video_info

        # Setze Callback für Stream-Erkennung (für Untertitel und Audio)
        self.video_player.streams_ready_callback = self.update_media_menus

        # Setze Callback für Kapitel-Erkennung
        self.video_player.toc_ready_callback = self.update_chapters_menu

        # Drag-and-Drop Setup
        self.setup_drag_and_drop()

        # Tastatur-Events (für F11 Vollbild)
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)

        # CSS für visuelles Drag-and-Drop Feedback
        self.setup_drop_css()

        # Der Modus-Switch ist bereits in setup_controls() initialisiert worden
        # Kein erneutes Setzen nötig, da play_mode beim Start immer "local" ist

        # Window-Größe wiederherstellen
        window_width = self.config.get_setting("window_width", 1000)
        window_height = self.config.get_setting("window_height", 700)
        self.set_default_size(window_width, window_height)

        # Registriere Window-Actions für Menüs
        self.setup_actions()

        # Lade letzte Playlist
        last_playlist = self.config.load_playlist()
        if last_playlist:
            # Konvertiere alte String-Playlists in das neue Dictionary-Format
            self.playlist_manager.playlist = [
                item if isinstance(item, dict) else {'path': item, 'display': Path(item).name}
                for item in last_playlist
            ]
            self.update_playlist_ui()
            print(f"{len(last_playlist)} Video(s) aus letzter Sitzung geladen.")


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
                    if was_empty and not self.current_video_path:
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
        print(f"Video zu Ende - Loop-Modus: {self.loop_mode.name}")

        if self.loop_mode == LoopMode.ONE:
            print("Wiederhole einzelnes Video...")
            self.seek_to_position(0)
            self.on_play(None)
        elif self.loop_mode == LoopMode.ALL:
            print("Wiederhole Playlist...")
            if not self.playlist_manager.has_next():
                # Am Ende der Playlist, springe zum Anfang
                self.playlist_manager.set_current_index(0)
            next_video = self.playlist_manager.next_video()
            if next_video:
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
            # Auto-Advance für LoopMode.NONE
            elif self.playlist_manager.has_next():
                print("Auto-Advance: Spiele nächstes Video ab")
                next_video = self.playlist_manager.next_video()
                if next_video:
                    self.load_and_play_video(next_video)
                    self.update_playlist_ui()

    def setup_header_bar(self):
        """Erstellt die Header Bar"""
        header = Adw.HeaderBar()

        # Datei öffnen Button
        open_button = Gtk.Button()
        open_button.set_icon_name("document-open-symbolic")
        open_button.set_tooltip_text("Video öffnen")
        open_button.connect("clicked", self.on_open_file)
        header.pack_start(open_button)

        # URL öffnen Button (Netzwerk-Symbol)
        self.url_button = Gtk.Button()
        self.url_button.set_icon_name("network-wired-symbolic")
        self.url_button.set_tooltip_text("Video von URL öffnen (z.B. YouTube)")
        self.url_button.connect("clicked", self.on_open_url)
        header.pack_start(self.url_button)

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

        # Video-Effekte-Button
        self.effects_button = Gtk.MenuButton()
        self.effects_button.set_icon_name("video-display-symbolic")
        self.effects_button.set_tooltip_text("Video-Effekte")
        self.effects_button.set_sensitive(False) # Deaktiviert bis Video geladen

        # Erstelle Effekte-Popover
        self.effects_popover = self.create_effects_popover()
        self.effects_button.set_popover(self.effects_popover)
        header.pack_end(self.effects_button)

        # Vollbild-Button
        self.fullscreen_button = Gtk.Button()
        self.fullscreen_button.set_icon_name("view-fullscreen-symbolic")
        self.fullscreen_button.set_tooltip_text("Vollbild (F11)")
        self.fullscreen_button.connect("clicked", self.on_toggle_fullscreen)
        header.pack_end(self.fullscreen_button)

        # Picture-in-Picture Button
        self.pip_button = Gtk.Button()
        self.pip_button.set_icon_name("view-app-grid-symbolic") # Platzhalter-Icon
        self.pip_button.set_tooltip_text("Bild-in-Bild (PiP)")
        self.pip_button.connect("clicked", self.on_toggle_pip)
        header.pack_end(self.pip_button)

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

        # Erweiterte Status-Anzeige (ausklappbar)
        self.chromecast_expander = Gtk.Expander()
        self.chromecast_expander.set_label("Erweiterte Informationen")
        self.chromecast_expander.set_visible(False)  # Nur sichtbar wenn verbunden

        # Status-Details Box
        status_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_details_box.set_margin_top(6)
        status_details_box.set_margin_bottom(6)

        # Device Info
        self.cc_device_label = Gtk.Label(label="Gerät: -")
        self.cc_device_label.set_xalign(0)
        self.cc_device_label.add_css_class("caption")
        status_details_box.append(self.cc_device_label)

        self.cc_model_label = Gtk.Label(label="Modell: -")
        self.cc_model_label.set_xalign(0)
        self.cc_model_label.add_css_class("caption")
        status_details_box.append(self.cc_model_label)

        # App Info
        self.cc_app_label = Gtk.Label(label="App: -")
        self.cc_app_label.set_xalign(0)
        self.cc_app_label.add_css_class("caption")
        status_details_box.append(self.cc_app_label)

        # Playback Status
        self.cc_state_label = Gtk.Label(label="Status: IDLE")
        self.cc_state_label.set_xalign(0)
        self.cc_state_label.add_css_class("caption")
        status_details_box.append(self.cc_state_label)

        # Media Info
        self.cc_media_label = Gtk.Label(label="Media: -")
        self.cc_media_label.set_xalign(0)
        self.cc_media_label.add_css_class("caption")
        self.cc_media_label.set_wrap(True)
        self.cc_media_label.set_max_width_chars(30)
        status_details_box.append(self.cc_media_label)

        # Buffer Status
        self.cc_buffer_label = Gtk.Label(label="Puffer: 0%")
        self.cc_buffer_label.set_xalign(0)
        self.cc_buffer_label.add_css_class("caption")
        status_details_box.append(self.cc_buffer_label)

        # Group Members (if applicable)
        self.cc_group_label = Gtk.Label(label="")
        self.cc_group_label.set_xalign(0)
        self.cc_group_label.add_css_class("caption")
        self.cc_group_label.set_wrap(True)
        self.cc_group_label.set_max_width_chars(30)
        self.cc_group_label.set_visible(False)
        status_details_box.append(self.cc_group_label)

        self.chromecast_expander.set_child(status_details_box)
        chromecast_section.append(self.chromecast_expander)

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

        # Handler für das Klicken auf die Leiste (ohne Ziehen)
        self.timeline_seek_handler_id = self.timeline_scale.connect("value-changed", self.on_timeline_seek)

        # Verwende GestureDrag, um den Start und das Ende des Ziehens zuverlässig zu erkennen
        drag_gesture = Gtk.GestureDrag.new()
        drag_gesture.set_button(1)  # Nur auf linke Maustaste reagieren
        drag_gesture.connect("drag-begin", self.on_timeline_drag_begin)
        drag_gesture.connect("drag-end", self.on_timeline_drag_end)
        self.timeline_scale.add_controller(drag_gesture)


        # Variablen für Thumbnail-Caching
        self.thumbnail_cache = {}
        self.last_thumbnail_position = None
        self.thumbnail_load_in_progress = False
        self.thumbnail_load_cancellable = None

        # Thread-Queue für asynchrone Thumbnail-Generierung
        self.thumbnail_queue = Queue()
        self.thumbnail_thread = None
        self.thumbnail_thread_running = False
        self._start_thumbnail_worker()

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
            # Blockiere das 'value-changed' Signal, um eine Endlosschleife zu verhindern,
            # aber nur, wenn der Handler gültig ist.
            if self.timeline_seek_handler_id and self.timeline_scale.handler_is_connected(self.timeline_seek_handler_id):
                self.timeline_scale.handler_block(self.timeline_seek_handler_id)
                self.timeline_scale.set_value(percentage)
                self.timeline_scale.handler_unblock(self.timeline_seek_handler_id)

            if not self.timeline_scale.get_sensitive():
                self.timeline_scale.set_sensitive(True)
        else:
            if self.timeline_scale.get_sensitive():
                self.timeline_scale.set_sensitive(False)

        # Überprüfe A-B Loop
        self.check_ab_loop()

        # Update Chromecast Status-Anzeige (nur im Chromecast-Modus)
        if self.play_mode == "chromecast":
            self.update_chromecast_status_display()

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

            # Aktualisiere Timeline-Slider sofort
            duration = self.get_current_duration()
            if duration and duration > 0:
                progress = (position / duration) * 100.0
                # Blockiere Handler während wir den Wert setzen
                if self.timeline_seek_handler_id and self.timeline_scale.handler_is_connected(self.timeline_seek_handler_id):
                    self.timeline_scale.handler_block(self.timeline_seek_handler_id)
                self.timeline_scale.set_value(progress)
                if self.timeline_seek_handler_id and self.timeline_scale.handler_is_connected(self.timeline_seek_handler_id):
                    self.timeline_scale.handler_unblock(self.timeline_seek_handler_id)

                # Aktualisiere auch das Zeit-Label
                self.time_label.set_text(self.format_time(position))
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
        if self.timeline_seek_handler_id and self.timeline_scale.handler_is_connected(self.timeline_seek_handler_id):
            self.timeline_scale.handler_block(self.timeline_seek_handler_id)
        print("Timeline seeking started")

    def on_timeline_drag_end(self, gesture, offset_x, offset_y):
        """Wird aufgerufen, wenn der Benutzer das Ziehen des Sliders beendet."""
        # Führe den finalen Seek-Vorgang an der Endposition aus
        self.on_timeline_seek(self.timeline_scale)
        self.is_seeking = False
        print("Timeline seeking ended")
        if self.timeline_seek_handler_id and self.timeline_scale.handler_is_connected(self.timeline_seek_handler_id):
            self.timeline_scale.handler_unblock(self.timeline_seek_handler_id)
        # Setze die Position zurück, um ein sofortiges Thumbnail-Update beim nächsten Hover zu erzwingen
        self.last_thumbnail_position = None
        # Verstecke das Popover, falls es noch offen ist
        self.thumbnail_popover.popdown()

    def on_timeline_seek(self, scale):
        """Wird aufgerufen, wenn der Benutzer den Timeline-Slider bewegt oder klickt."""
        duration = self.get_current_duration()

        # Führe Seek nur aus, wenn der Benutzer aktiv sucht (zieht) oder klickt.
        # Dies verhindert, dass die programmgesteuerte Aktualisierung in update_timeline()
        # einen Seek-Vorgang auslöst.
        if duration > 0 and self.is_seeking:
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
        # Nur im lokalen Modus
        if self.play_mode != "local" or not self.timeline_scale.get_sensitive():
            return

        # Berechne Position für Zeit-Label und Popover-Position
        duration = self.get_current_duration()
        if not duration or duration <= 0:
            return

        try:
            value = self.timeline_scale.emit("get-value-for-pos", x, y)
            hover_position = (value / 100.0) * duration
        except TypeError:
            widget_width = self.timeline_scale.get_width()
            progress = max(0.0, min(1.0, x / widget_width)) if widget_width > 0 else 0
            hover_position = progress * duration

        # Aktualisiere Position und Zeit SOFORT (kein Debounce)
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        self.thumbnail_popover.set_pointing_to(rect)
        self.thumbnail_time_label.set_text(self.format_time(hover_position))

        # Zeige Popover wenn noch nicht sichtbar
        if not self.thumbnail_popover.get_visible():
            self.thumbnail_popover.popup()

        # Berechne Maus-Geschwindigkeit (basierend auf Position-Änderung)
        import time
        current_time = time.time()

        if not hasattr(self, '_last_hover_time'):
            self._last_hover_time = current_time
            self._last_hover_position = hover_position

        time_delta = current_time - self._last_hover_time
        position_delta = abs(hover_position - self._last_hover_position)

        # Berechne Geschwindigkeit (Sekunden pro Sekunde Zeitdelta)
        velocity = position_delta / time_delta if time_delta > 0 else 0

        self._last_hover_time = current_time
        self._last_hover_position = hover_position

        # Nur Thumbnails laden wenn Maus langsam (< 50 Sekunden/Sekunde)
        # Bei schneller Bewegung: nur Position/Zeit updaten, kein Thumbnail
        if velocity < 50:
            # Längerer Debounce für Thumbnail-Update (500ms statt 300ms)
            new_id = GLib.timeout_add(500, self._update_thumbnail_popover, x, y)
            self.thumbnail_hover_timeout_id = new_id

    def _update_thumbnail_popover(self, x, y):
        """Interne Funktion, die nur das Thumbnail aktualisiert (nicht die Position)."""

        # Kein Thumbnail anzeigen während gezogen wird
        if self.is_seeking:
            return False

        duration = self.get_current_duration()
        if not duration or duration <= 0:
            return False

        # Berechne Position
        try:
            value = self.timeline_scale.emit("get-value-for-pos", x, y)
            hover_position = (value / 100.0) * duration
        except TypeError:
            widget_width = self.timeline_scale.get_width()
            progress = max(0.0, min(1.0, x / widget_width)) if widget_width > 0 else 0
            hover_position = progress * duration

        # Prüfe ob Thumbnail im Cache ist (in 15-Sekunden-Schritten für weniger Flackern)
        cache_key = int(hover_position / 15) * 15

        # Nur aktualisieren, wenn wir zu einem anderen Cache-Slot wechseln
        if self.last_thumbnail_position is not None:
            last_cache_key = int(self.last_thumbnail_position / 15) * 15
            if cache_key == last_cache_key:
                # Gleicher Cache-Slot, kein Update nötig
                return False

        self.last_thumbnail_position = cache_key  # Speichere Cache-Key, nicht hover_position

        if cache_key in self.thumbnail_cache:
            # Verwende gecachtes Thumbnail
            pixbuf = self.thumbnail_cache.get(cache_key)
            if pixbuf:
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.thumbnail_image.set_paintable(texture)
        else:
            # Lade Thumbnail asynchron
            GLib.idle_add(self.load_thumbnail_async, cache_key, cache_key, x, y)

        # Setze die ID zurück
        self.thumbnail_hover_timeout_id = None
        return False

    def on_timeline_leave(self, controller):
        """Wird aufgerufen, wenn die Maus die Timeline verlässt."""
        # Lasse Timer einfach ablaufen - setze nur ID zurück
        self.thumbnail_hover_timeout_id = None
        self.thumbnail_popover.popdown()
        self.last_thumbnail_position = None

    def _start_thumbnail_worker(self):
        """Startet den Background-Worker-Thread für Thumbnail-Generierung"""
        if self.thumbnail_thread_running:
            return

        self.thumbnail_thread_running = True

        def worker():
            """Worker-Thread der Thumbnail-Anfragen aus der Queue verarbeitet"""
            from queue import Empty
            while self.thumbnail_thread_running:
                try:
                    # Hole nächste Anfrage mit Timeout (nicht-blockierend)
                    request = self.thumbnail_queue.get(timeout=0.5)
                    if request is None:  # Shutdown-Signal
                        break

                    position, cache_key, x, y = request

                    # Generiere Thumbnail (kann länger dauern, blockiert aber nicht die UI)
                    pixbuf = self.video_player.get_frame_at_position(position)

                    if pixbuf:
                        # Cache Thumbnail (thread-safe da dict-writes atomar sind in CPython)
                        self.thumbnail_cache[cache_key] = pixbuf

                        # Update UI im Main-Thread mit Popover-Position
                        GLib.idle_add(self._display_thumbnail, pixbuf, x, y)

                except Empty:
                    # Timeout ist normal - einfach weiter warten
                    continue
                except Exception as e:
                    if self.thumbnail_thread_running:  # Nur loggen wenn nicht beim Shutdown
                        import traceback
                        print(f"Fehler im Thumbnail-Worker: {e}")
                        traceback.print_exc()

        self.thumbnail_thread = threading.Thread(target=worker, daemon=True)
        self.thumbnail_thread.start()

    def _display_thumbnail(self, pixbuf, x, y):
        """Zeigt ein Thumbnail an (wird im Main-Thread aufgerufen)"""
        try:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.thumbnail_image.set_paintable(texture)

            # Zeige Popover an der Position
            rect = Gdk.Rectangle()
            rect.x = int(x)
            rect.y = int(y)
            rect.width = 1
            rect.height = 1
            self.thumbnail_popover.set_pointing_to(rect)
            self.thumbnail_popover.popup()
        except Exception as e:
            print(f"Fehler beim Anzeigen des Thumbnails: {e}")
        return False

    def load_thumbnail_async(self, position, cache_key, x, y):
        """Lädt Thumbnail asynchron über den Worker-Thread"""
        # Leere die Queue - wir wollen nur das neueste Thumbnail
        while not self.thumbnail_queue.empty():
            try:
                self.thumbnail_queue.get_nowait()
            except:
                break

        # Füge neue Anfrage hinzu (mit Position für Popover)
        self.thumbnail_queue.put((position, cache_key, x, y))
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

    def setup_performance_optimizations(self):
        """Setzt Performance-Optimierungen"""

        # GStreamer Pipeline optimieren
        if self.play_mode == "local":
            # Setze niedrigere Latenz für lokale Wiedergabe

            # 500ms statt 250ms für flüssigere Wiedergabe
            if self.timeline_update_timeout:
                GLib.source_remove(self.timeline_update_timeout)


            self.timeline_update_timeout = GLib.timeout_add(500, self.update_timeline)
            print(f"Timeline updates started (500ms interval)")

            # Setze properties für playbin
            self.video_player.playbin.set_property("video-sink", self.video_player.gtksink)
            self.video_player.playbin.set_property("audio-sink", Gst.ElementFactory.make("autoaudiosink", "audio-sink"))

            # Hardware-Beschleunigung explizit setzen
            self.video_player.setup_hardware_acceleration()
            self.chromecast_expander.set_visible(False)

        else:
            self.timeline_update_timeout = GLib.timeout_add(500, self.update_timeline)

        # Clear Thumbnail Cache wenn zu groß
        if len(self.video_player.thumbnail_cache) > 50:
            self.video_player.thumbnail_cache.clear()
            print("Thumbnail cache cleared for performance")


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

        # Next Button
        self.next_button = Gtk.Button()
        self.next_button.set_icon_name("media-skip-forward-symbolic")
        self.next_button.set_tooltip_text("Nächstes Video")
        self.next_button.connect("clicked", self.on_next_video)
        self.next_button.set_sensitive(False)
        self.control_box.append(self.next_button)

        # A-B Loop Buttons
        # Loop-Modus Button
        self.loop_button = Gtk.Button()
        self.loop_button.connect("clicked", self.on_toggle_loop_mode)
        self.control_box.append(self.loop_button)
        # Setze initialen Zustand
        self.update_loop_button_ui()


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

        # Mode Toggle - Prominent mit Icons
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        mode_box.set_margin_start(24)
        mode_box.add_css_class("card")  # Gibt dem Modus-Switcher einen Rahmen
        mode_box.set_margin_top(6)
        mode_box.set_margin_bottom(6)
        mode_box.set_margin_start(12)
        mode_box.set_margin_end(12)

        # Lokal Icon
        local_icon = Gtk.Image.new_from_icon_name("computer-symbolic")
        mode_box.append(local_icon)

        mode_label = Gtk.Label(label="<b>Wiedergabe-Modus:</b>")
        mode_label.set_use_markup(True)
        mode_box.append(mode_label)

        self.mode_switch = Gtk.Switch()
        self.mode_switch.set_active(self.play_mode == "chromecast")
        self.mode_switch.connect("notify::active", self.on_mode_changed)
        self.mode_switch.set_tooltip_text("Zwischen lokaler Wiedergabe und Chromecast umschalten")
        mode_box.append(self.mode_switch)

        self.mode_label = Gtk.Label()
        self.mode_label.set_use_markup(True)
        self._update_mode_label()
        mode_box.append(self.mode_label)

        # Chromecast Icon
        chromecast_icon = Gtk.Image.new_from_icon_name("network-wireless-symbolic")
        mode_box.append(chromecast_icon)

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
        self.last_equalizer_settings['brightness'] = value
        self.video_player.set_equalizer(brightness=value)

    def on_contrast_changed(self, scale):
        """Callback für Kontrast-Änderung"""
        value = scale.get_value()
        self.last_equalizer_settings['contrast'] = value
        self.video_player.set_equalizer(contrast=value)

    def on_saturation_changed(self, scale):
        """Callback für Sättigung-Änderung"""
        value = scale.get_value()
        self.last_equalizer_settings['saturation'] = value
        self.video_player.set_equalizer(saturation=value)

    def on_hue_changed(self, scale):
        """Callback für Farbton-Änderung"""
        value = scale.get_value()
        self.last_equalizer_settings['hue'] = value
        self.video_player.set_equalizer(hue=value)

    def on_equalizer_reset(self, _button):
        """Reset Equalizer auf Standard-Werte"""
        self.brightness_scale.set_value(0.0)
        self.contrast_scale.set_value(1.0)
        self.saturation_scale.set_value(1.0)
        self.hue_scale.set_value(0.0)
        self.last_equalizer_settings = None
        self.video_player.reset_equalizer()

    def create_effects_popover(self):
        """Erstellt das Popover für Video-Effekte (Rotation, Zoom, Crop, Gamma, Filter-Presets)"""
        popover = Gtk.Popover()

        # Hauptcontainer mit Tabs/Notebook
        notebook = Gtk.Notebook()
        notebook.set_margin_top(12)
        notebook.set_margin_bottom(12)
        notebook.set_margin_start(12)
        notebook.set_margin_end(12)

        # === TAB 1: Rotation & Spiegelung ===
        rotation_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        rotation_box.set_margin_top(12)
        rotation_box.set_margin_bottom(12)
        rotation_box.set_margin_start(12)
        rotation_box.set_margin_end(12)

        rotation_label = Gtk.Label(label="Rotation & Spiegelung")
        rotation_label.add_css_class("title-4")
        rotation_box.append(rotation_label)

        # Rotation Buttons
        rotation_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        btn_none = Gtk.Button(label="Normal")
        btn_none.connect("clicked", lambda b: self.on_rotation_changed(0))
        rotation_buttons_box.append(btn_none)

        btn_90cw = Gtk.Button(label="90° ↻")
        btn_90cw.connect("clicked", lambda b: self.on_rotation_changed(1))
        rotation_buttons_box.append(btn_90cw)

        btn_180 = Gtk.Button(label="180°")
        btn_180.connect("clicked", lambda b: self.on_rotation_changed(2))
        rotation_buttons_box.append(btn_180)

        btn_90ccw = Gtk.Button(label="90° ↺")
        btn_90ccw.connect("clicked", lambda b: self.on_rotation_changed(3))
        rotation_buttons_box.append(btn_90ccw)

        rotation_box.append(rotation_buttons_box)

        # Spiegelung Buttons
        flip_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        btn_h_flip = Gtk.Button(label="↔ Horizontal")
        btn_h_flip.connect("clicked", lambda b: self.on_rotation_changed(4))
        flip_buttons_box.append(btn_h_flip)

        btn_v_flip = Gtk.Button(label="↕ Vertikal")
        btn_v_flip.connect("clicked", lambda b: self.on_rotation_changed(5))
        flip_buttons_box.append(btn_v_flip)

        rotation_box.append(flip_buttons_box)

        notebook.append_page(rotation_box, Gtk.Label(label="Rotation"))

        # === TAB 2: Zoom & Crop ===
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        zoom_box.set_margin_top(12)
        zoom_box.set_margin_bottom(12)
        zoom_box.set_margin_start(12)
        zoom_box.set_margin_end(12)

        # Zoom
        zoom_title = Gtk.Label(label="Zoom")
        zoom_title.add_css_class("title-4")
        zoom_title.set_xalign(0)
        zoom_box.append(zoom_title)

        self.zoom_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 3.0, 0.1)
        self.zoom_scale.set_value(1.0)
        self.zoom_scale.set_draw_value(True)
        self.zoom_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.zoom_scale.set_hexpand(True)
        self.zoom_scale.connect("value-changed", self.on_zoom_changed)
        zoom_box.append(self.zoom_scale)

        # Crop
        crop_title = Gtk.Label(label="Zuschneiden (Crop)")
        crop_title.add_css_class("title-4")
        crop_title.set_xalign(0)
        crop_title.set_margin_top(12)
        zoom_box.append(crop_title)

        # Crop Top
        crop_top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        crop_top_label = Gtk.Label(label="Oben:")
        crop_top_label.set_width_chars(8)
        crop_top_box.append(crop_top_label)
        self.crop_top_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 500, 10)
        self.crop_top_scale.set_value(0)
        self.crop_top_scale.set_draw_value(True)
        self.crop_top_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.crop_top_scale.set_hexpand(True)
        self.crop_top_scale.connect("value-changed", self.on_crop_changed)
        crop_top_box.append(self.crop_top_scale)
        zoom_box.append(crop_top_box)

        # Crop Bottom
        crop_bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        crop_bottom_label = Gtk.Label(label="Unten:")
        crop_bottom_label.set_width_chars(8)
        crop_bottom_box.append(crop_bottom_label)
        self.crop_bottom_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 500, 10)
        self.crop_bottom_scale.set_value(0)
        self.crop_bottom_scale.set_draw_value(True)
        self.crop_bottom_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.crop_bottom_scale.set_hexpand(True)
        self.crop_bottom_scale.connect("value-changed", self.on_crop_changed)
        crop_bottom_box.append(self.crop_bottom_scale)
        zoom_box.append(crop_bottom_box)

        # Crop Left
        crop_left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        crop_left_label = Gtk.Label(label="Links:")
        crop_left_label.set_width_chars(8)
        crop_left_box.append(crop_left_label)
        self.crop_left_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 500, 10)
        self.crop_left_scale.set_value(0)
        self.crop_left_scale.set_draw_value(True)
        self.crop_left_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.crop_left_scale.set_hexpand(True)
        self.crop_left_scale.connect("value-changed", self.on_crop_changed)
        crop_left_box.append(self.crop_left_scale)
        zoom_box.append(crop_left_box)

        # Crop Right
        crop_right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        crop_right_label = Gtk.Label(label="Rechts:")
        crop_right_label.set_width_chars(8)
        crop_right_box.append(crop_right_label)
        self.crop_right_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 500, 10)
        self.crop_right_scale.set_value(0)
        self.crop_right_scale.set_draw_value(True)
        self.crop_right_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.crop_right_scale.set_hexpand(True)
        self.crop_right_scale.connect("value-changed", self.on_crop_changed)
        crop_right_box.append(self.crop_right_scale)
        zoom_box.append(crop_right_box)

        notebook.append_page(zoom_box, Gtk.Label(label="Zoom/Crop"))

        # === TAB 3: Gamma & Filter-Presets ===
        gamma_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        gamma_box.set_margin_top(12)
        gamma_box.set_margin_bottom(12)
        gamma_box.set_margin_start(12)
        gamma_box.set_margin_end(12)

        # Gamma
        gamma_title = Gtk.Label(label="Gamma-Korrektur")
        gamma_title.add_css_class("title-4")
        gamma_title.set_xalign(0)
        gamma_box.append(gamma_title)

        self.gamma_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 3.0, 0.1)
        self.gamma_scale.set_value(1.0)
        self.gamma_scale.set_draw_value(True)
        self.gamma_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.gamma_scale.set_hexpand(True)
        self.gamma_scale.connect("value-changed", self.on_gamma_changed)
        gamma_box.append(self.gamma_scale)

        # Filter-Presets
        presets_title = Gtk.Label(label="Filter-Presets")
        presets_title.add_css_class("title-4")
        presets_title.set_xalign(0)
        presets_title.set_margin_top(12)
        gamma_box.append(presets_title)

        # Preset Buttons Grid
        preset_grid = Gtk.Grid()
        preset_grid.set_column_spacing(6)
        preset_grid.set_row_spacing(6)

        presets = [
            ("Normal", "normal"),
            ("Sepia", "sepia"),
            ("Graustufen", "grayscale"),
            ("Schwarz-Weiß", "blackwhite"),
            ("Vintage", "vintage"),
            ("Lebhaft", "vivid"),
            ("Dunkel", "dark"),
            ("Hell", "bright"),
            ("Kalt", "cold"),
            ("Warm", "warm")
        ]

        for i, (label, preset_name) in enumerate(presets):
            btn = Gtk.Button(label=label)
            btn.connect("clicked", lambda b, p=preset_name: self.on_preset_clicked(p))
            preset_grid.attach(btn, i % 2, i // 2, 1, 1)

        gamma_box.append(preset_grid)

        notebook.append_page(gamma_box, Gtk.Label(label="Gamma/Filter"))

        # Reset Button
        reset_button = Gtk.Button(label="Alle Effekte zurücksetzen")
        reset_button.set_margin_top(12)
        reset_button.connect("clicked", self.on_effects_reset)

        # Hauptbox
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.append(notebook)
        main_box.append(reset_button)

        popover.set_child(main_box)
        return popover

    def on_rotation_changed(self, rotation):
        """Callback für Rotation-Änderung"""
        self.video_player.set_rotation(rotation)

    def on_zoom_changed(self, scale):
        """Callback für Zoom-Änderung"""
        value = scale.get_value()
        self.video_player.set_zoom(value)

    def on_crop_changed(self, scale):
        """Callback für Crop-Änderung"""
        left = int(self.crop_left_scale.get_value())
        right = int(self.crop_right_scale.get_value())
        top = int(self.crop_top_scale.get_value())
        bottom = int(self.crop_bottom_scale.get_value())
        self.video_player.set_crop(left, right, top, bottom)

    def on_gamma_changed(self, scale):
        """Callback für Gamma-Änderung"""
        value = scale.get_value()
        self.video_player.set_gamma(value)

    def on_preset_clicked(self, preset_name):
        """Callback für Filter-Preset"""
        self.video_player.apply_filter_preset(preset_name)
        # Update Equalizer-Sliders um die Werte zu reflektieren
        settings = self.video_player.get_equalizer()
        self.brightness_scale.set_value(settings['brightness'])
        self.contrast_scale.set_value(settings['contrast'])
        self.saturation_scale.set_value(settings['saturation'])
        self.hue_scale.set_value(settings['hue'])
        self.gamma_scale.set_value(settings['gamma'])

    def on_effects_reset(self, _button):
        """Reset alle Video-Effekte"""
        self.video_player.reset_video_effects()
        # Reset UI-Sliders
        self.zoom_scale.set_value(1.0)
        self.crop_left_scale.set_value(0)
        self.crop_right_scale.set_value(0)
        self.crop_top_scale.set_value(0)
        self.crop_bottom_scale.set_value(0)
        self.gamma_scale.set_value(1.0)
        # Reset auch Equalizer-Sliders
        self.brightness_scale.set_value(0.0)
        self.contrast_scale.set_value(1.0)
        self.saturation_scale.set_value(1.0)
        self.hue_scale.set_value(0.0)

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

    def update_chromecast_status_display(self):
        """Aktualisiert die erweiterte Chromecast-Status-Anzeige"""
        if not hasattr(self, 'chromecast_expander'):
            return

        status = self.cast_manager.get_extended_status()

        if status['connected']:
            # Zeige Expander
            self.chromecast_expander.set_visible(True)

            # Update Labels
            self.cc_device_label.set_text(f"Gerät: {status['device_name']}")
            self.cc_model_label.set_text(f"Modell: {status.get('device_model', 'N/A')}")
            self.cc_app_label.set_text(f"App: {status['app_name']}")

            # Status mit Farbe
            state = status['player_state']
            state_color = ""
            if state == "PLAYING":
                state_color = "🟢"
            elif state == "PAUSED":
                state_color = "🟡"
            elif state == "BUFFERING":
                state_color = "🔵"
            elif state == "IDLE":
                state_color = "⚪"
            self.cc_state_label.set_text(f"Status: {state_color} {state}")

            # Media Info
            media_title = status['media_title']
            if len(media_title) > 35:
                media_title = media_title[:32] + "..."
            self.cc_media_label.set_text(f"Media: {media_title}")

            # Buffer
            buffer_percent = status['buffer_percent']
            self.cc_buffer_label.set_text(f"Fortschritt: {buffer_percent}%")

            # Group Members (falls vorhanden)
            members = self.cast_manager.get_group_members()
            if len(members) > 1:
                self.cc_group_label.set_text(f"Gruppe ({len(members)}): {', '.join(members)}")
                self.cc_group_label.set_visible(True)
            else:
                self.cc_group_label.set_visible(False)
        else:
            # Verstecke Expander wenn nicht verbunden
            self.chromecast_expander.set_visible(False)

    def on_show_goto_dialog(self, _button):
        """Zeigt Dialog zum Springen zu einer bestimmten Zeit"""
        duration = self.get_current_duration()
        if not duration or duration <= 0:
            self.status_label.set_text("Kein Video geladen")
            return

        current_position = self.get_current_position() or 0

        time_entry = Gtk.Entry()
        time_entry.set_placeholder_text("z.B. 1:23:45 oder 5:30")
        # Setze aktuelle Zeit als Vorgabe
        time_entry.set_text(self.format_time(current_position))
        time_entry.set_max_width_chars(10)
        time_entry.set_hexpand(True)

        # Use a Gtk.Box to hold the entry and info label
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.append(Gtk.Label(label="Gib die Zielzeit ein (Format: MM:SS oder HH:MM:SS)"))
        content_box.append(time_entry)
        
        info_label = Gtk.Label(label=f"Video-Dauer: {self.format_time(duration)}")
        info_label.add_css_class("dim-label")
        content_box.append(info_label)

        dialog = Adw.AlertDialog.new(
            "Zu Zeit springen",
            None # Body text is in the body_widget
        )
        dialog.set_extra_child(content_box)
        dialog.add_response("cancel", "Abbrechen")
        dialog.add_response("jump", "Springen")
        dialog.set_response_appearance("jump", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("jump")

        def on_response(d, response):
            if response == "jump":
                time_str = time_entry.get_text().strip()
                seconds = self.parse_time_string(time_str)
                if seconds is not None and 0 <= seconds <= duration:
                    self.seek_to_position(seconds)
                    self.status_label.set_text(f"Gesprungen zu {self.format_time(seconds)}")
                else:
                    self.status_label.set_text("Ungültige Zeitangabe")

        dialog.connect("response", on_response)
        dialog.present(self)

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

    def on_toggle_pip(self, _button):
        """Schaltet den Picture-in-Picture-Modus um."""
        if self.pip_window:
            self.exit_pip_mode()
        else:
            self.enter_pip_mode()

    def enter_pip_mode(self):
        """Wechselt in den PiP-Modus.

        Anstatt das Video-Widget zu verschieben (was zu Problemen führt),
        erstellen wir ein neues Video-Sink für das PiP-Fenster und weisen
        playbin an, dieses zu verwenden.
        """
        # PiP ist verfügbar, wenn ein Video geladen ist (lokal oder URL) und der Modus lokal ist.
        if not (self.current_video_path or self.video_player.current_file) or self.play_mode != "local":
            self.status_label.set_text("PiP nur bei lokaler Wiedergabe verfügbar")
            return

        # PiP-Fenster erstellen
        self.pip_window = Gtk.Window(application=self.get_application())
        self.pip_window.set_title("PiP")
        self.pip_window.set_default_size(320, 180)
        self.pip_window.set_keep_above(True)
        self.pip_window.set_decorated(False)
        self.pip_window.connect("close-request", self.exit_pip_mode)

        # Erstelle ein neues Video-Sink für das PiP-Fenster
        self.pip_video_sink = Gst.ElementFactory.make("gtk4paintablesink", "pipsink")
        pip_paintable = self.pip_video_sink.get_property("paintable")
        pip_picture = Gtk.Picture.new_for_paintable(pip_paintable)

        # Overlay für den "Wiederherstellen"-Button
        pip_overlay = Gtk.Overlay()
        pip_overlay.set_child(pip_picture)

        restore_button = Gtk.Button.new_from_icon_name("view-restore-symbolic")
        restore_button.set_tooltip_text("Vollbild wiederherstellen")
        restore_button.connect("clicked", self.exit_pip_mode)
        restore_button.set_halign(Gtk.Align.CENTER)
        restore_button.set_valign(Gtk.Align.CENTER)
        restore_button.set_opacity(0.5)
        pip_overlay.add_overlay(restore_button)

        self.pip_window.set_child(pip_overlay)

        # Wechsle das Video-Sink von playbin zum neuen PiP-Sink
        self.video_player.playbin.set_property("video-sink", self.pip_video_sink)

        # Hauptfenster verstecken und PiP-Fenster anzeigen
        self.set_visible(False)
        self.pip_window.present()
        print("PiP-Modus aktiviert")

    def exit_pip_mode(self, widget=None):
        """Beendet den PiP-Modus."""
        if not self.pip_window:
            return True

        # Wechsle das Video-Sink zurück zum Hauptfenster
        self.video_player.playbin.set_property("video-sink", self.video_player.video_bin)

        # Zerstöre das PiP-Fenster und seine Ressourcen
        self.pip_window.destroy()
        self.pip_window = None
        self.pip_video_sink = None

        # Zeige das Hauptfenster wieder an
        self.set_visible(True)
        print("PiP-Modus beendet")
        return True  # Verhindert, dass das Fenster geschlossen wird, wenn über 'x' beendet

    def on_toggle_loop_mode(self, button):
        """Schaltet durch die Wiederholungsmodi."""
        if self.loop_mode == LoopMode.NONE:
            self.loop_mode = LoopMode.ALL
        elif self.loop_mode == LoopMode.ALL:
            self.loop_mode = LoopMode.ONE
        else: # LoopMode.ONE
            self.loop_mode = LoopMode.NONE
        
        self.config.set_setting("loop_mode", self.loop_mode.name)
        self.update_loop_button_ui()

    def update_loop_button_ui(self):
        """Aktualisiert Icon und Tooltip des Loop-Buttons."""
        if self.loop_mode == LoopMode.NONE:
            self.loop_button.set_icon_name("media-playlist-consecutive-symbolic")
            self.loop_button.set_tooltip_text("Wiederholung: Aus")
        elif self.loop_mode == LoopMode.ALL:
            self.loop_button.set_icon_name("media-playlist-repeat-symbolic")
            self.loop_button.set_tooltip_text("Wiederholung: Alle")
        else: # LoopMode.ONE
            self.loop_button.set_icon_name("media-playlist-repeat-song-symbolic")
            self.loop_button.set_tooltip_text("Wiederholung: Einzeln")

    def on_open_url(self, button):
        """Zeigt einen Dialog zum Öffnen einer Video-URL an."""
        entry = Gtk.Entry()
        entry.set_placeholder_text("https://www.youtube.com/watch?v=...")
        entry.set_hexpand(True)

        # Use a Gtk.Box to hold the entry and provide padding
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        entry.set_margin_top(12)
        entry.set_margin_bottom(12)
        entry.set_margin_start(12)
        entry.set_margin_end(12)
        content_box.append(Gtk.Label(label="Fügen Sie eine URL von YouTube oder einer anderen unterstützten Seite ein."))
        content_box.append(entry)

        dialog = Adw.AlertDialog.new(
            "Video von URL öffnen",
            None # Body text is in the body_widget
        )
        dialog.set_extra_child(content_box)
        dialog.add_response("cancel", "Abbrechen")
        dialog.add_response("play", "Abspielen")
        dialog.set_response_appearance("play", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("play")
        def on_response(d, response):
            if response == "play":
                url = entry.get_text().strip()
                if url and ("http://" in url or "https://" in url):
                    self.load_from_url(url)
                else:
                    self.status_label.set_text("Ungültige URL eingegeben.")
        
        dialog.connect("response", on_response)
        dialog.present(self)

    def load_from_url(self, url):
        """Lädt Metadaten und Stream-URL von einer Webseite."""
        
        # Bereinige YouTube-URL von Playlist-Parametern etc.
        cleaned_url = self.clean_youtube_url(url)
        if cleaned_url != url:
            print(f"Bereinigte URL: {cleaned_url}")
            url = cleaned_url

        self.status_label.set_text("Lade Video-Informationen von URL...")
        self.loading_spinner.start()
        self.loading_spinner.set_visible(True)
        self.url_button.set_sensitive(False) # Verhindere mehrfaches Klicken

        def get_stream_info():
            try:
                # Prüfe, ob yt-dlp installiert ist
                subprocess.run(['yt-dlp', '--version'], check=True, capture_output=True)
    
                # Hole Titel
                title_process = subprocess.run(['yt-dlp', '--no-playlist', '--get-title', '-e', url], capture_output=True, text=True, check=True)
                title = title_process.stdout.strip()
    
                # Hole die direkte Stream-URL für ein kombiniertes Format (Video+Audio)
                # Dies ermöglicht Seeking. Wir wählen ein Format, das wahrscheinlich kombiniert ist.
                stream_url_process = subprocess.run(
                    ['yt-dlp', '--no-playlist', '-f', 'best[ext=mp4]/best', '--get-url', url],
                    capture_output=True, text=True, check=True
                )
                stream_url = stream_url_process.stdout.strip()
    
                if not stream_url.startswith("http"):
                    raise ValueError("yt-dlp hat keine gültige Stream-URL zurückgegeben.")
    
                GLib.idle_add(self.on_stream_info_loaded, url, title, stream_url)

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_message = "Fehler: yt-dlp nicht gefunden oder URL ungültig."
                if isinstance(e, FileNotFoundError):
                    error_message = "Fehler: 'yt-dlp' ist nicht installiert. Bitte installieren."
                print(error_message, e)
                GLib.idle_add(lambda: (
                    self.status_label.set_text(error_message),
                    self.loading_spinner.stop(),
                    self.loading_spinner.set_visible(False),
                    self.url_button.set_sensitive(True)
                ))

        thread = threading.Thread(target=get_stream_info, daemon=True)
        thread.start()

    def on_stream_info_loaded(self, original_url, title, stream_url):
        """Wird aufgerufen, wenn die Stream-Infos erfolgreich geladen wurden."""
        self.loading_spinner.stop()
        self.loading_spinner.set_visible(False)
        
        print(f"Titel: {title}")
        print(f"Stream-URL erhalten: {stream_url[:70]}...") # Kürze URL für die Ausgabe

        # Füge zur Playlist hinzu (verwende Original-URL als "Pfad")
        if self.playlist_manager.add_video(original_url):
            self.playlist_manager.set_current_index(self.playlist_manager.get_playlist_length() - 1)
        else:
            index = next((i for i, item in enumerate(self.playlist_manager.playlist) if item['path'] == original_url), -1)
            self.playlist_manager.set_current_index(index) # Setze existierendes Video als aktuell
        
        # Überschreibe den Namen in der Playlist mit dem echten Titel
        self.playlist_manager.playlist[self.playlist_manager.current_index]['display'] = title
        self.update_playlist_ui()

        # Spiele den Stream ab
        self.load_and_play_video(stream_url, is_url=True, title=title)

    def clean_youtube_url(self, url):
        """Entfernt Playlist- und andere unnötige Parameter von einer YouTube-URL."""
        if "youtube.com" not in url and "youtu.be" not in url:
            return url
        
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            if 'v' in query_params:
                # Behalte nur den 'v' Parameter
                return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', urlencode({'v': query_params['v'][0]}), ''))
        except Exception:
            pass # Bei Fehler, gib Original-URL zurück
        return url


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
                if self.playlist_manager.add_video(filepath):
                    self.playlist_manager.set_current_index(self.playlist_manager.get_playlist_length() - 1)
                else:
                    # Setze existierendes Video als aktuell
                    index = next((i for i, item in enumerate(self.playlist_manager.playlist) if item['path'] == filepath), -1)
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
                self.effects_button.set_sensitive(True)  # Video-Effekte sind immer für lokale Wiedergabe verfügbar

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
        if button:
            button.set_sensitive(False)

        def on_devices_found(devices):
            if button:
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

            # Speichere aktuelle Position falls Video läuft
            current_position = None
            if self.current_video_path:
                current_position = self.video_player.get_position()

            # Wechsle automatisch in Chromecast-Modus nach erfolgreicher Verbindung
            # Handler blockieren, damit on_mode_changed nicht doppelt aufgerufen wird
            self.mode_switch.handler_block_by_func(self.on_mode_changed)
            self.mode_switch.set_active(True)
            self.mode_switch.handler_unblock_by_func(self.on_mode_changed)

            # Setze play_mode manuell
            self.play_mode = "chromecast"
            self.config.set_setting("play_mode", "chromecast")
            self._update_mode_label()

            print(f"Chromecast-Modus aktiviert nach Verbindung mit '{device_name}'")

            # Wenn ein Video geladen war, starte automatisch Streaming
            if self.current_video_path:
                print(f"Starte automatisches Streaming von: {Path(self.current_video_path).name}")

                # Stoppe lokale Wiedergabe
                self.video_player.stop()

                # Starte Chromecast-Streaming in Thread
                def start_streaming():
                    from pathlib import Path
                    filename = Path(self.current_video_path).name
                    video_path = self.current_video_path

                    # Konvertierung falls nötig
                    if video_path.lower().endswith(('.mkv', '.avi')):
                        GLib.idle_add(self.status_label.set_text, "Konvertiere Video...")
                        converted_path = self.video_converter.convert_to_mp4(video_path)
                        if converted_path:
                            video_path = converted_path

                    video_url = self.http_server.get_video_url(video_path)
                    if video_url:
                        success = self.cast_manager.play_video(self.current_video_path, video_url)
                        if success:
                            # Springe zur gespeicherten Position falls vorhanden
                            if current_position and current_position > 0:
                                import time
                                time.sleep(2)  # Warte bis Streaming gestartet ist
                                self.cast_manager.seek(current_position)

                            GLib.idle_add(lambda: (
                                self.status_label.set_text(f"Streamt: {filename}"),
                                self.start_timeline_updates(),
                                self.inhibit_suspend(),
                                self.play_button.set_sensitive(True),
                                self.play_button.set_icon_name("media-playback-pause-symbolic"),
                                False
                            ))
                        else:
                            GLib.idle_add(self.status_label.set_text, "Streaming fehlgeschlagen")
                    else:
                        GLib.idle_add(self.status_label.set_text, "HTTP-Server-Fehler")

                import threading
                thread = threading.Thread(target=start_streaming, daemon=True)
                thread.start()
            else:
                self.status_label.set_text(f"Chromecast bereit: {device_name}")
        else:
            self.status_label.set_text(f"Verbindung fehlgeschlagen")
        return False

    def _update_mode_label(self):
        """Aktualisiert das Modus-Label mit Farbe und Formatierung"""
        if self.play_mode == "chromecast":
            self.mode_label.set_markup('<span foreground="#4A90E2"><b>Chromecast</b></span>')
        else:
            self.mode_label.set_markup('<span foreground="#7CB342"><b>Lokal</b></span>')

    def on_mode_changed(self, switch, gparam):
        """Wechselt zwischen lokalem und Chromecast-Modus"""
        if switch.get_active():
            # Wechsel zu Chromecast-Modus

            # Prüfe ob bereits nach Chromecasts gesucht wurde
            if not self.cast_manager._discovery_browser and not self.cast_manager.selected_cast:
                # Noch keine Suche durchgeführt - zeige Hinweis-Dialog
                dialog = Adw.AlertDialog.new(
                    "Chromecast-Gerät suchen",
                    "Um Chromecast verwenden zu können, müssen Sie zuerst nach verfügbaren Geräten suchen.\n\n"
                    "Klicken Sie auf das Chromecast-Symbol oben rechts, um nach Geräten zu suchen."
                )
                dialog.add_response("ok", "Verstanden")
                dialog.add_response("search", "Jetzt suchen")
                dialog.set_response_appearance("search", Adw.ResponseAppearance.SUGGESTED)
                dialog.set_default_response("search")

                def on_dialog_response(d, response):
                    if response == "search":
                        # Öffne Chromecast-Auswahl
                        self.on_scan_chromecasts(None)
                    else:
                        # Schalte zurück zu Lokal-Modus
                        self.mode_switch.set_active(False)

                dialog.connect("response", on_dialog_response)
                dialog.present(self)
                return

            self.play_mode = "chromecast"
            self.config.set_setting("play_mode", "chromecast")
            self._update_mode_label()

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
            self._update_mode_label()

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
            try:
                self.play_button.disconnect_by_func(self.on_play)
            except TypeError:
                pass # War nicht verbunden
            self.play_button.set_icon_name("media-playback-pause-symbolic")
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
                try:
                    self.play_button.disconnect_by_func(self.on_play)
                except TypeError:
                    pass # War nicht verbunden
                self.play_button.set_icon_name("media-playback-pause-symbolic")
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
                                    (lambda: self.play_button.disconnect_by_func(self.on_play) if self.play_button.handler_is_connected(self.play_button.connect("clicked", self.on_play)) else None)(),
                                    self.play_button.set_icon_name("media-playback-pause-symbolic"),
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
            try:
                self.play_button.disconnect_by_func(self.on_pause)
            except TypeError:
                pass # War nicht verbunden
            self.play_button.set_icon_name("media-playback-start-symbolic")
            self.play_button.connect("clicked", self.on_play)
        else:
            self.cast_manager.pause()
            # Bei Pause Standby wieder erlauben
            self.uninhibit_suspend()
            try:
                self.play_button.disconnect_by_func(self.on_pause)
            except TypeError:
                pass # War nicht verbunden
            self.play_button.set_icon_name("media-playback-start-symbolic")
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

            # Thumbnail-Bild
            thumbnail_image = Gtk.Image()
            thumbnail_image.set_pixel_size(60)  # Größe des Thumbnails

            # Versuche Thumbnail zu laden (nur für lokale Videos, nicht URLs)
            video_file_path = video_path.get('path', '')
            if video_file_path and not video_file_path.startswith('http'):
                thumbnail_path = self.video_player.get_thumbnail_path(video_file_path)

                # Wenn Thumbnail existiert, lade es
                if os.path.exists(thumbnail_path):
                    try:
                        thumbnail_image.set_from_file(thumbnail_path)
                    except Exception as e:
                        print(f"Fehler beim Laden des Thumbnails: {e}")
                        thumbnail_image.set_from_icon_name("video-x-generic-symbolic")
                else:
                    # Thumbnail existiert nicht, zeige Platzhalter-Icon
                    thumbnail_image.set_from_icon_name("video-x-generic-symbolic")

                    # Extrahiere Thumbnail asynchron im Hintergrund
                    def extract_async():
                        if self.video_player.extract_video_thumbnail(video_file_path, thumbnail_path):
                            # Aktualisiere UI im Hauptthread
                            GLib.idle_add(lambda: thumbnail_image.set_from_file(thumbnail_path))

                    threading.Thread(target=extract_async, daemon=True).start()
            else:
                # Für URLs oder fehlende Pfade zeige Video-Icon
                thumbnail_image.set_from_icon_name("video-x-generic-symbolic")

            entry_box.append(thumbnail_image)

            # Icon für aktuelles Video
            if index == self.playlist_manager.current_index:
                icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
                entry_box.append(icon)

            # Video-Name
            label = Gtk.Label(label=video_path['display'])
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
            if video_path and video_path.startswith("http"):
                self.load_from_url(video_path)
            elif video_path:
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

        dialog = Adw.AlertDialog.new(
            "Wiedergabe fortsetzen?",
            f"Möchten Sie '{filename}' an der gespeicherten Position ({time_str}) fortsetzen?"
        )
        dialog.add_response("cancel", "Von Anfang an")
        dialog.add_response("resume", "Fortsetzen")
        dialog.set_response_appearance("resume", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("resume")
        dialog.set_close_response("cancel")

        def on_response(d, response):
            if response == "resume":
                # Lade Video und springe zur Position
                self.load_and_play_video(filepath, resume_position=position, autoplay=autoplay)
            else:
                # Von vorne beginnen und Lesezeichen entfernen
                self.bookmark_manager.remove_bookmark(filepath)
                self.load_and_play_video(filepath, autoplay=autoplay)

        dialog.connect("response", on_response)
        dialog.present(self)

    def load_and_play_video(self, filepath, resume_position=None, autoplay=True, is_url=False, title=None):
        """Lädt und spielt ein Video ab"""
        # Speichere Position des vorherigen Videos
        if self.current_video_path and self.current_video_path != filepath:
            self.save_current_position()

        # Leere Thumbnail-Cache bei neuem Video
        self.thumbnail_cache.clear()
        self.last_thumbnail_position = None
        
        # Erlaube, dass das Info-Overlay für das neue Video einmal angezeigt wird
        self.info_overlay_shown_for_current_video = False
        self._streams_info_updated_for_current_video = False

        if not is_url:
            self.current_video_path = filepath
            filename = Path(filepath).name
        else:
            # Speichere die Original-URL als "Pfad" für Lesezeichen und andere Funktionen
            self.current_video_path = filepath # Für YouTube-Streams ist dies die Stream-URL
            filename = title or "Online Stream"

        # Gespeicherte Equalizer-Einstellungen anwenden
        if self.last_equalizer_settings:
            print("Wende gespeicherte Equalizer-Einstellungen an...")
            self.last_equalizer_settings = self.config.get_setting("equalizer")
            self.video_player.set_equalizer(**self.last_equalizer_settings)
            self.update_equalizer_ui()
        
        if self.play_mode == "local":
            # Beende einen eventuell laufenden yt-dlp Prozess (falls von alter Methode noch vorhanden)
            if hasattr(self, 'yt_dlp_process') and self.yt_dlp_process:
                self.yt_dlp_process.terminate()
                self.yt_dlp_process = None

            # Lade das Video. Dies funktioniert jetzt für lokale Dateien UND für Stream-URLs.
            self.video_player.load_video(filepath)

            # Starte die Wiedergabe
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
            self.effects_button.set_sensitive(True)  # Video-Effekte sind immer für lokale Wiedergabe verfügbar
            self.ab_button_a.set_sensitive(True)
            self.ab_button_b.set_sensitive(True)
            self.goto_button.set_sensitive(True)

            if autoplay:
                # Play-Button aktualisieren
                try:
                    self.play_button.disconnect_by_func(self.on_play)
                except TypeError:
                    pass # War nicht verbunden
                self.play_button.set_icon_name("media-playback-pause-symbolic")
                self.play_button.connect("clicked", self.on_pause)
            
            self.status_label.set_text(f"Spielt: {filename}" if autoplay else f"Bereit: {filename}")

            # Timeline aktivieren nach kurzem Delay
            def enable_timeline(is_stream=False):
                duration = self.video_player.get_duration()
                if duration > 0:
                    self.timeline_scale.set_sensitive(True)
                    self.duration_label.set_text(self.format_time(duration))
                    self.time_label.set_text("00:00")
                    self.timeline_scale.set_value(0)

                    # Wenn resume_position gesetzt ist, springe dorthin
                    if resume_position:
                        GLib.timeout_add(100, lambda: self.seek_to_position(resume_position))
                elif is_stream:
                    # Bei Streams kann die Dauer anfangs 0 sein. Wir aktivieren die Timeline trotzdem.
                    self.timeline_scale.set_sensitive(True)
                return False

            GLib.timeout_add(500, enable_timeline, is_url)
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
                                (lambda: self.play_button.disconnect_by_func(self.on_play) if self.play_button.handler_is_connected(self.play_button.connect("clicked", self.on_play)) else None)(),
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
        try:
            self.play_button.disconnect_by_func(self.on_pause)
        except TypeError:
            pass # War nicht verbunden
        try:
            # Stelle sicher, dass nur ein on_play Handler verbunden ist
            self.play_button.disconnect_by_func(self.on_play)
        except TypeError:
            pass
        self.play_button.connect("clicked", self.on_play)


    
    def on_key_press_event(self, widget, event):
        """Behandelt Tastendrücke auf dem Hauptfenster."""
        keyval = event.get_keyval()[1]
        shortcuts = self.config.get_setting("keyboard_shortcuts", {})

        # Dynamisches Mapping von Key-Namen zu Gdk.KEY_* Konstanten
        key_map = {v: getattr(Gdk, f"KEY_{v}") for v in shortcuts.values()}

        action_map = {
            "fullscreen": lambda: self.on_toggle_fullscreen(None),
            "play_pause": self.toggle_play_pause,
            "seek_forward": lambda: self.seek_relative(5),
            "seek_backward": lambda: self.seek_relative(-5),
            "volume_up": lambda: self.change_volume_relative(0.05),
            "volume_down": lambda: self.change_volume_relative(-0.05),
            "mute": self.toggle_mute,
            "next_video": lambda: self.on_next_video(None),
            "previous_video": lambda: self.on_previous_video(None),
            "screenshot": self.take_screenshot,
            "ab_loop_a": lambda: self.on_set_loop_a(None) if self.ab_button_a.get_sensitive() else None,
            "ab_loop_b": lambda: self.on_set_loop_b(None) if self.ab_button_b.get_sensitive() else None,
            "ab_loop_clear": lambda: self.on_clear_loop(None) if self.ab_button_clear.get_sensitive() else None,
            "goto_time": lambda: self.on_show_goto_dialog(None) if self.goto_button.get_sensitive() else None,
            "toggle_info": self.toggle_persistent_info_overlay,
        }

        for action_name, key_name in shortcuts.items():
            # Prüfe sowohl Klein- als auch Großschreibung
            if keyval == key_map.get(key_name) or (key_name.isalpha() and keyval == key_map.get(key_name.upper())):
                if action_name in action_map:
                    action_map[action_name]()
                    return True # Event wurde behandelt

        return False # Event weiterleiten

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
        elif keyval == key_map.get(shortcuts.get("screenshot", "s"), Gdk.KEY_s) or keyval == key_map.get(shortcuts.get("screenshot", "s").upper(), Gdk.KEY_S):
            self.take_screenshot()
            return True
        elif keyval == key_map.get(shortcuts.get("ab_loop_a", "a"), Gdk.KEY_a) or keyval == key_map.get(shortcuts.get("ab_loop_a", "a").upper(), Gdk.KEY_A):
            if self.ab_button_a.get_sensitive():
                self.on_set_loop_a(None)
            return True
        elif keyval == key_map.get(shortcuts.get("ab_loop_b", "b"), Gdk.KEY_b) or keyval == key_map.get(shortcuts.get("ab_loop_b", "b").upper(), Gdk.KEY_B):
            if self.ab_button_b.get_sensitive():
                self.on_set_loop_b(None)
            return True
        elif keyval == key_map.get(shortcuts.get("ab_loop_clear", "c"), Gdk.KEY_c) or keyval == key_map.get(shortcuts.get("ab_loop_clear", "c").upper(), Gdk.KEY_C):
            if self.ab_button_clear.get_sensitive():
                self.on_clear_loop(None)
            return True
        elif keyval == key_map.get(shortcuts.get("goto_time", "g"), Gdk.KEY_g) or keyval == key_map.get(shortcuts.get("goto_time", "g").upper(), Gdk.KEY_G):
            if self.goto_button.get_sensitive():
                self.on_show_goto_dialog(None)
            return True
        elif keyval == key_map.get(shortcuts.get("toggle_info", "i"), Gdk.KEY_i) or keyval == key_map.get(shortcuts.get("toggle_info", "i").upper(), Gdk.KEY_I):
            self.toggle_persistent_info_overlay()
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
        # Finde den aktuellen Wiedergabestatus
        current_state = self.video_player.playbin.get_state(0).state
        is_playing = (current_state == Gst.State.PLAYING)

        # Führe die entsprechende Aktion aus
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
        if self.is_fullscreen():
            self.unfullscreen()
            self._toggle_ui_for_fullscreen(False)
        else:
            self.fullscreen()
            self._toggle_ui_for_fullscreen(True)

    def _toggle_ui_for_fullscreen(self, fullscreen_active):
        """Zeigt/versteckt UI-Elemente für den Vollbildmodus."""
        self.main_box.get_first_child().set_visible(not fullscreen_active)  # HeaderBar
        self.sidebar.set_visible(not fullscreen_active)
        self.timeline_widget.set_visible(not fullscreen_active)
        self.control_box.set_visible(not fullscreen_active)

        # Entferne/Setze Ränder für echten Vollbildmodus
        if fullscreen_active:
            self.content_box.set_margin_start(0)
            self.content_box.set_margin_end(0)
            self.content_box.set_margin_top(0)
            self.content_box.set_margin_bottom(0)
        else:
            self.content_box.set_margin_start(12)
            self.content_box.set_margin_end(12)
            self.content_box.set_margin_top(12)
            self.content_box.set_margin_bottom(12)

        # Mauszeiger im Vollbildmodus ausblenden
        window = self.get_native()
        if window:
            if fullscreen_active:
                # Erstelle einen leeren Cursor, um ihn auszublenden
                cursor = Gdk.Cursor.new_from_name("none")
                window.set_cursor(cursor)
            else:
                # Setze den Cursor auf den Standard zurück
                window.set_cursor(None)

    def on_video_area_click(self, gesture, n_press, x, y):
        """Behandelt Klicks im Videobereich (für Doppelklick-Vollbild)."""
        if n_press == 2:  # Doppelklick
            self.on_toggle_fullscreen(None)

    def show_video_info(self, video_info):
        """Zeigt das Info-Overlay für einige Sekunden an."""
        info_text = (
            f"<b>Auflösung:</b> {video_info['resolution']}\n"
            f"<b>Codec:</b> {video_info['codec']}\n"
            f"<b>Bitrate:</b> {video_info['bitrate']}"
        )
        self.info_label.set_markup(info_text)
        self.info_label.set_visible(True)

        # Wenn das Overlay für dieses Video bereits angezeigt wurde und nicht persistent ist,
        # dann zeige es nicht erneut an.
        is_persistent = getattr(self, '_info_overlay_persistent', False)
        if self.info_overlay_shown_for_current_video and not is_persistent:
            return # Nichts tun


        # Entferne einen eventuell laufenden Timer, um das Ausblenden zurückzusetzen
        if self.info_overlay_timeout_id:
            GLib.source_remove(self.info_overlay_timeout_id)
            self.info_overlay_timeout_id = None

        # Wenn das Overlay dauerhaft angezeigt werden soll, nicht ausblenden
        is_persistent = getattr(self, '_info_overlay_persistent', False)
        if not is_persistent:
            # Standardverhalten: Nach 5 Sekunden ausblenden
            self.info_label.set_opacity(1.0)
            self.info_overlay_timeout_id = GLib.timeout_add_seconds(5, self.hide_info_overlay)
            self.info_overlay_shown_for_current_video = True # Markiere als angezeigt
        else:
            self.info_label.set_opacity(1.0)

    def toggle_persistent_info_overlay(self):
        """Schaltet die permanente Anzeige des Info-Overlays um."""
        is_persistent = not getattr(self, '_info_overlay_persistent', False)
        self._info_overlay_persistent = is_persistent
        self.info_label.set_visible(is_persistent)
        if is_persistent:
            self.info_label.set_opacity(1.0)
            self.status_label.set_text("Video-Infos dauerhaft eingeblendet")
        else:
            self.status_label.set_text("Video-Infos werden automatisch ausgeblendet")
        return False # Verhindert, dass der Callback erneut aufgerufen wird

    def hide_info_overlay(self):
        """Versteckt das Info-Overlay und setzt den Timer zurück."""
        self.info_label.set_opacity(0.0)
        self.info_overlay_timeout_id = None
        return False # Timer nur einmal ausführen


    def update_media_menus(self):
        """Aktualisiert Untertitel-, Audio- und Kapitel-Menüs."""
        if self._streams_info_updated_for_current_video:
            return False # Already updated for this video

        self.update_subtitle_menu()
        self.update_audio_menu() 
        # Kapitel werden über eine separate TOC-Nachricht (`toc_ready_callback`) behandelt,
        # daher hier nicht mehr aufrufen.
        self._streams_info_updated_for_current_video = True
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

    def update_chapters_menu(self, toc):
        """Aktualisiert das Kapitel-Menü basierend auf verfügbaren Kapiteln."""
        print("Suche nach Kapiteln...")
        chapters = self.video_player.parse_toc(toc)

        if not chapters or len(chapters) == 0:
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
            version="1.9.0",
            developers=["DaHool"],
            copyright="© 2025 DaHool",
            license_type=Gtk.License.MIT_X11,
            website="https://github.com/berlinux2016/gnome-chromecast-player",
            issue_url="https://github.com/berlinux2016/gnome-chromecast-player/issues",
            comments="Ein moderner GTK4-Videoplayer mit Chromecast-Unterstützung, der für eine nahtlose Wiedergabe sowohl lokal als auch auf Chromecast-Geräten optimiert ist. Inklusive Hardware-Beschleunigung für AMD und NVIDIA GPUs.\n\nMit Liebe für Simone programmiert ❤️"
        )

        # Füge Version-Informationen als Credit-Sections hinzu
        about.add_credit_section(
            "Was ist neu in Version 1.9.0?",
            [
                "Spulen (Seeking) für YouTube-Videos aktiviert",
                "Stabilitätsverbesserungen für die Timeline",
                "Verbesserte Logik für das Info-Overlay (verhindert Flackern)",
                "Zahlreiche Fehlerbehebungen und Code-Optimierungen"
            ]
        )
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

        # Speichere Equalizer-Einstellungen
        if self.last_equalizer_settings:
            self.config.set_setting("equalizer", self.last_equalizer_settings)

        # Speichere aktuelle Playlist
        self.config.save_playlist(self.playlist_manager.playlist)
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

        # Stoppe Thumbnail-Worker-Thread
        try:
            if hasattr(self, 'thumbnail_thread_running') and self.thumbnail_thread_running:
                print("Stoppe Thumbnail-Worker...")
                self.thumbnail_thread_running = False
                self.thumbnail_queue.put(None)  # Shutdown-Signal
                if self.thumbnail_thread and self.thumbnail_thread.is_alive():
                    self.thumbnail_thread.join(timeout=1.0)
        except Exception as e:
            print(f"Fehler beim Stoppen des Thumbnail-Workers: {e}")

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
    print("=== Video Player Starting ===", file=sys.stderr, flush=True)
    print(f"Python: {sys.version}", file=sys.stderr, flush=True)
    print(f"Args: {sys.argv}", file=sys.stderr, flush=True)

    try:
        app = VideoPlayerApp()
        print("App created successfully", file=sys.stderr, flush=True)
        result = app.run(sys.argv)
        print(f"App.run() returned: {result}", file=sys.stderr, flush=True)
        return result
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())