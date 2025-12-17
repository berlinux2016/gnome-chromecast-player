<div align="center">

# 🎬 Video Chromecast Player

### Modern GTK4 Video Player with Chromecast Streaming and Hardware Acceleration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GTK Version](https://img.shields.io/badge/GTK-4-blue.svg)](https://www.gtk.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)](https://www.linux.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Arch Linux](https://img.shields.io/badge/Arch_Linux-Supported-1793D1?logo=arch-linux)](https://archlinux.org/)
[![GitHub](https://img.shields.io/badge/GitHub-berlinux2016%2Fgnome--chromecast--player-blue?logo=github)](https://github.com/berlinux2016/gnome-chromecast-player)

**Cross-Distribution Linux Video Player** | **Multilingual (EN/DE)** | **Hardware Accelerated**

*Developed by **DaHool** with ❤️ for Simone*

[Features](#-features) • [Installation](#-installation) • [Arch Linux](#arch-linux-recommended) • [Usage](#-usage) • [Hardware Acceleration](#-hardware-acceleration) • [Troubleshooting](#-troubleshooting)

</div>

---

## 📸 Screenshots

> 🚧 Screenshots coming soon

<!--
![Main Window](screenshots/main-window.png)
*Main window with timeline and controls*

![Chromecast Mode](screenshots/chromecast-mode.png)
*Chromecast streaming with device selection*
-->

## ✨ Features

### 🎨 Modern User Interface
- **GTK4/Libadwaita** UI in GNOME style
- **YouTube Video Streaming** - Direct playback of YouTube videos via URL input
- **Playlist Support** - Multiple videos in queue with auto-advance
- **Playlist Thumbnails** - Automatic video preview images in the playlist
- **Recent Files** - History of recently opened videos (max. 10)
- **Fullscreen Mode** - F11 for fullscreen playback
- **Drag & Drop** - Drag videos directly into the window
- **Timeline/Seek Function** with real-time position display
- **Volume Control** with slider for local and Chromecast playback
- **Video Info Overlay** - Shows codec, resolution, and bitrate
- **Video Effects** - Rotation, mirroring, zoom, crop, gamma correction
- **Filter Presets** - 10 predefined filters (sepia, vintage, black & white, etc.)
- **Subtitle Support** - Automatic detection of SRT, ASS, VTT files
- **Audio Track Selection** - Switch between multiple audio tracks
- **Bookmarks/Resume** - Automatic saving and resuming of playback
- **Playback Speed** - 0.25x to 3.0x with dropdown menu and keyboard shortcuts
- **Frame-by-Frame Navigation** - Precise single-frame navigation with , and . keys
- **Screenshot Function** - Frame capture with S key
- **Video Equalizer** - Adjust brightness, contrast, saturation, and hue
- **A-B Loop** - Repeat loop between two points for learning videos
- **Go-To Time** - Jump to specific time position (MM:SS or HH:MM:SS)
- **Chapter Detection** - Automatic detection and navigation of MKV/MP4 chapters
- **Timeline Thumbnails** - Preview images when hovering over timeline
- **Keyboard Shortcuts** - Extensive keyboard control with help dialog (H key)
- **Playlist Import** - M3U and PLS format support
- **Intuitive Controls**: Previous, Next, Play, Pause, Stop, Seek, Volume

### ⚡ Hardware Acceleration
- **AMD GPUs**: VA-API for decoding + encoding (up to 8K)
- **NVIDIA GPUs**: NVDEC/NVENC for decoding + encoding (up to 8K)
- **Automatic GPU Detection** at startup
- **Minimal CPU Load** (< 5% at 4K playback)
- **Lightning-Fast Video Conversion** (10-20x faster than software)

### 📡 Chromecast Integration
- **Automatic Device Discovery** on network (< 1 second)
- **Video Streaming** to all Chromecast devices
- **Xiaomi TV Compatibility** with special fixes
- **Timeline Synchronization** between local and Chromecast
- **Intelligent Caching**: Converted videos are stored for faster access
- **Subtitle Support** - Display subtitles on Chromecast device
- **Audio Track Selection** - Select audio tracks for Chromecast playback
- **Multi-Room Audio** - Synchronized playback on multiple devices
- **Group Support** - Connection with Chromecast groups
- **Extended Status Display** - Detailed Chromecast information in real-time

### 🎞️ Video Formats & Codecs
- **All Common Containers**: MP4, MKV, AVI, WebM, MOV, FLV, OGG, MPEG, TS, WMV
- **Hardware Codecs**: H.264, H.265/HEVC, VP9, AV1, VC-1
- **Software Codecs**: MPEG-2, MPEG-4, DivX, XviD, Theora
- **Automatic MKV/AVI → MP4 Conversion** for Chromecast

### 🔒 Legal Safety
- **No Software Codecs Included** - only hardware APIs
- **Patent-Safe** - Hardware encoders are not subject to patent restrictions
- **Open Source** - MIT License

## 💻 Supported Linux Distributions

Video Chromecast Player is designed to work on **all major Linux distributions**:

- ✅ **Arch Linux** - Native support with automated installer and AUR package
- ✅ **Fedora** - Fully tested and optimized
- ✅ **Ubuntu / Debian** - Compatible with apt-based systems
- ✅ **openSUSE** - Works with zypper package manager
- ✅ **Manjaro / EndeavourOS** - All Arch-based distributions
- ✅ **Other distributions** - Should work on any modern Linux with GTK4

### 🌍 Multilingual Support

The application supports multiple languages:
- 🇬🇧 **English** - Full UI translation
- 🇩🇪 **German (Deutsch)** - Vollständige deutsche Übersetzung
- Automatically detects your system language
- Easy to add more languages (see [I18N-GUIDE.md](I18N-GUIDE.md))

## System Requirements

- **Any Linux distribution** with GTK4 support
- Python 3.9 or higher
- GTK4
- Libadwaita
- GStreamer 1.0
- **AMD, NVIDIA, or Intel GPU** (for hardware acceleration - optional but recommended)

## 📦 Installation

### Arch Linux (Recommended)

For Arch Linux users, we provide native support:

#### Option 1: Automated Installation Script
```bash
chmod +x install-arch.sh
./install-arch.sh
```

The script automatically:
- Detects your GPU (AMD/NVIDIA/Intel)
- Installs appropriate hardware acceleration drivers
- Installs all system and Python dependencies
- Creates desktop entry and icon

#### Option 2: AUR Package (Coming Soon)
```bash
yay -S gnome-chromecast-player
# or
paru -S gnome-chromecast-player
```

📖 **Detailed Guide**: See [INSTALL-ARCH.md](INSTALL-ARCH.md) for complete Arch Linux installation instructions.

### Fedora Linux

#### Automatic Installation
```bash
chmod +x install.sh
./install.sh
```

The script installs:
- RPM Fusion repositories (if not already installed)
- All GStreamer packages and codecs
- Hardware acceleration drivers (AMD VA-API / NVIDIA NVDEC)
- Python dependencies
- Desktop shortcut for GNOME

### Debian / Ubuntu Linux

#### Building from Source with Debian Package

The recommended way to install on Debian/Ubuntu is to build a .deb package:

```bash
# Install build dependencies
sudo apt install debhelper devscripts debhelper dh-python gettext

# Build the package
chmod +x build-deb.sh
./build-deb.sh

# Install the package
sudo dpkg -i ../gnome-chromecast-player_*.deb
sudo apt-get install -f  # Install missing dependencies if needed
```

The package will automatically:
- Install all required dependencies
- Set up the application in /usr/bin
- Create desktop entry and menu integration
- Install translations (English/German)
- Configure hardware acceleration support

#### Manual Installation (Debian/Ubuntu)

If you prefer manual installation:

```bash
# Install system dependencies
sudo apt install -y \
    python3 \
    python3-pip \
    python3-gi \
    gir1.2-gtk-4.0 \
    gir1.2-adw-1 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-vaapi \
    gstreamer1.0-gtk4 \
    ffmpeg \
    yt-dlp

# Install hardware acceleration (choose based on your GPU)
# For AMD:
sudo apt install -y mesa-va-drivers

# For NVIDIA:
sudo apt install -y nvidia-driver nvidia-vdpau-driver

# For Intel:
sudo apt install -y intel-media-va-driver

# Install Python dependencies
pip3 install --user -r requirements.txt

# Make executable
chmod +x videoplayer.py
```

### Other Distributions

For openSUSE or other distributions, adapt the package names accordingly

### Manual Installation

If you want to perform the installation manually:

#### 1. Enable RPM Fusion

```bash
sudo dnf install -y \
    https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
    https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
```

#### 2. Install System Dependencies

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

#### 3. AMD Hardware Acceleration

```bash
sudo dnf install -y \
    mesa-va-drivers \
    mesa-vdpau-drivers \
    libva \
    libva-utils \
    libva-vdpau-driver \
    gstreamer1-vaapi
```

#### 4. Complete Codecs (RPM Fusion)

```bash
sudo dnf install -y \
    gstreamer1-plugins-bad-freeworld \
    gstreamer1-plugins-ugly \
    gstreamer1-plugin-openh264 \
    mozilla-openh264 \
    ffmpeg \
    ffmpeg-libs
```

#### 5. Python Dependencies

```bash
pip3 install --user -r requirements.txt
```

#### 6. Make Executable

```bash
chmod +x videoplayer.py
```

## 📖 Usage

### Starting the Application

```bash
./videoplayer.py
```

Or search for "Video Chromecast Player" in your GNOME applications.

### Playing Videos

1. Click the folder icon in the header bar to open a video file
2. The video will automatically be added to the playlist and displayed in the preview
3. Use the controls at the bottom:
   - **Previous Button**: Previous video in playlist
   - **Play Button**: Start playback
   - **Pause Button**: Pause playback
   - **Stop Button**: Stop playback
   - **Next Button**: Next video in playlist
   - **Volume Slider**: Adjust volume (0-100%)
   - **Timeline Slider**: Jump to any position

### Using the Playlist

1. **Add Videos**:
   - Click **+** in the playlist section to select multiple videos
   - **OR** simply drag video files into the window via drag & drop
2. Videos are played in order
3. After a video ends, the next one starts automatically (auto-advance)
4. Click a video in the playlist to jump directly to it
5. Use **Previous** and **Next** buttons to navigate
6. Remove individual videos with the **X** button
7. **Import Playlist**:
   - Click the **Import Button** (folder icon) in the playlist section
   - Select a `.m3u` or `.pls` file
   - The contained videos will be automatically added to the playlist
8. Clear the entire playlist with the **Trash** button

**Playlist Thumbnails:**
- Each video in the playlist automatically shows a **preview image** (thumbnail) from the video
- Thumbnails are automatically extracted and cached the first time
- Preview images are generated from the middle of the video (approx. 5 seconds)
- Thumbnails are **60x60 pixels** for optimal performance
- Cached thumbnails are stored in `~/.cache/gnome-chromecast-player/thumbnails/`
- For YouTube videos or URLs, a standard video icon is displayed

### Using Drag & Drop

1. Open your file manager and navigate to your videos
2. Select one or more video files
3. Drag them into the video player window
4. The videos will be automatically added to the playlist
5. The first video automatically starts playback (if no video is already playing)
6. **Visual Feedback**: The area is outlined in blue when hovering

### Playing YouTube Videos

1. Click the **YouTube Button** (▶ icon) in the header bar
2. A dialog opens with an input field for the YouTube URL
3. Paste the URL of a YouTube video (e.g., `https://www.youtube.com/watch?v=...`)
4. Click **Load Video**
5. The video is automatically extracted and added to the playlist
6. **Note**: Requires `yt-dlp` for video extraction
7. Works for both local playback and Chromecast streaming

### Fullscreen Mode

1. Press the **F11** key to enter and exit fullscreen mode
2. Alternatively, you can use the fullscreen button in the header bar

### Keyboard Shortcuts

**Press H for a complete overview of all keyboard shortcuts in the player!**

#### Playback
- **Spacebar**: Play / Pause
- **←/→**: 5 seconds back/forward
- **,/.**: Frame backward/forward (frame-by-frame)
- **[/]**: Decrease/increase speed
- **N**: Next video in playlist
- **P**: Previous video in playlist

#### Volume & Audio
- **↑/↓**: Increase/decrease volume (5%)
- **M**: Mute / Unmute

#### View
- **F11 or F**: Toggle fullscreen mode
- **I**: Info overlay on/off

#### A-B Loop & Export
- **A**: Set loop point A
- **B**: Set loop point B
- **C**: Clear loop
- **E**: Export clip (A-B)

#### Navigation
- **G**: Jump to time
- **S**: Take screenshot (local only)

#### Help
- **H**: Show keyboard shortcuts overview

### Using Subtitles

1. **Automatic Detection**: Place a subtitle file (`.srt`, `.ass`, `.vtt`) in the same folder as your video. The file must have the same name (e.g., `MyMovie.mp4` and `MyMovie.srt`).
2. **Select**: When a video with subtitles is loaded, the subtitle button (speech bubble) in the header bar becomes active.
3. Click the button to select a subtitle track or disable subtitles.

### Selecting Audio Track

1. For videos with multiple audio tracks (e.g., multilingual movies), the audio button (speaker) in the header bar becomes active.
2. Click the button to switch between available audio tracks.
3. Audio tracks display language, title, and codec (e.g., "Track 1 (deu) [AC-3]").

### Bookmarks / Resume Playback

1. **Automatic Saving**: The player automatically saves your position when closing or switching videos.
2. **Resume**: When reopening a video, a dialog is shown to resume playback or start from the beginning.
3. **Smart Saving**: Positions are only saved if more than 5 seconds have been played and the video is not in the last 30 seconds.
4. **Bookmark Management**: Bookmarks are automatically removed when you watch a video to the end or start from the beginning.

### Adjusting Playback Speed

1. Click the speed button (fast-forward icon) in the header bar.
2. Select a speed: **0.5x**, **0.75x**, **Normal (1.0x)**, **1.25x**, **1.5x**, or **2.0x**.
3. The speed is applied immediately (local playback only).
4. Perfect for learning (slow) or quick review (fast).

### Taking Screenshots

1. Press the **S key** during playback (local playback only).
2. The screenshot is automatically saved to: `~/Pictures/Video-Screenshots/`
3. Filename format: `VideoName_20251209_153045.png` (with timestamp).
4. A confirmation appears in the status bar.

### Using Video Equalizer

1. Click the equalizer button (color icon) in the header bar.
2. Adjust the following values with the sliders:
   - **Brightness**: -1.0 to +1.0 (0 = default)
   - **Contrast**: 0.0 to 2.0 (1.0 = default)
   - **Saturation**: 0.0 to 2.0 (1.0 = default)
   - **Hue**: -1.0 to +1.0 (0 = default)
3. Changes are applied immediately.
4. Click **Reset** to restore all values to default.
5. Perfect for videos with poor color quality or dark scenes.

### Using Video Effects

1. Click the **Video Effects Button** (image icon) in the header bar
2. A window with 3 tabs opens:

**Tab 1 - Rotation & Mirroring:**
   - **Normal**: No rotation
   - **90° ↻**: Rotate 90° clockwise
   - **180°**: Rotate 180°
   - **90° ↺**: Rotate 90° counterclockwise
   - **↔ Horizontal**: Mirror horizontally
   - **↕ Vertical**: Mirror vertically

**Tab 2 - Zoom & Crop:**
   - **Zoom**: 0.5x to 3.0x magnification (default: 1.0x)
   - **Crop**: Crop pixels from each side
     - Top: 0-500 pixels
     - Bottom: 0-500 pixels
     - Left: 0-500 pixels
     - Right: 0-500 pixels

**Tab 3 - Gamma & Filters:**
   - **Gamma Correction**: 0.1 to 3.0 (default: 1.0)
     - Higher values = brighter
     - Lower values = darker
   - **Filter Presets**: 10 predefined effects
     - **Normal**: Default settings
     - **Sepia**: Vintage sepia tone
     - **Grayscale**: Black & white without contrast
     - **Black & White**: High contrast black & white
     - **Vintage**: Retro look with reduced colors
     - **Vivid**: Bold, saturated colors
     - **Dark**: Dark film look
     - **Bright**: Brightened video
     - **Cool**: Cooler blue tone
     - **Warm**: Warmer orange tone

3. Click **Reset All Effects** to restore all settings to default
4. Perfect for videos with wrong orientation, unwanted borders, or for creative effects

### Using A-B Loop (Repeat Loop)

1. Play a video and navigate to the desired **start point**.
2. Press the **A key** or click the **A button** to set point A.
3. Navigate to the desired **end point**.
4. Press the **B key** or click the **B button** to set point B.
5. The loop is now active - the video automatically jumps back to point A when point B is reached.
6. To clear the loop, press the **C key** or click the **Clear button** (X).
7. Perfect for learning videos, language training, or music loops.

### Using Go-To Time (Jump to Specific Time)

1. Press the **G key** or click the **Go-To button** (jump icon) in the control bar.
2. A dialog opens with an input field for the target time.
3. Enter the time in format **MM:SS** (e.g., `5:30`) or **HH:MM:SS** (e.g., `1:23:45`).
4. The input field is pre-filled with the current position.
5. Click **Jump** to jump to the entered time.
6. Perfect for quickly navigating to known timestamps.

### Using Chapters (Chapter Navigation)

1. For videos with chapters (MKV/MP4 with chapter metadata), the **Chapter button** (list icon) in the header bar becomes active.
2. Click the button to see a list of all chapters.
3. Each entry shows the chapter title and start time (e.g., "Chapter 1: Intro (00:05:30)").
4. Click a chapter to jump directly to it.
5. Perfect for structured videos like tutorials, movies, or lectures.

### Using Timeline Thumbnails (Preview on Hover)

1. When a video is loaded in **local mode**, move the mouse over the timeline.
2. A **preview popover** automatically appears with a thumbnail of the current frame.
3. The time position is displayed below the thumbnail.
4. Move the mouse along the timeline to see different positions.
5. Thumbnails are cached for faster display.
6. **Note**: Feature is only available in local mode, not for Chromecast playback.

### Using Chromecast

1. Make sure your Chromecast and your computer are on the same network
2. Click the Wi-Fi icon in the header bar to search for Chromecast devices
3. Found devices are displayed in the right sidebar
4. Click a device to connect
5. The mode switch automatically changes to "Chromecast"
6. Open a video and start playback
7. **MKV/AVI files are automatically converted to MP4** - this can take a few seconds the first time
8. Converted videos are cached in `~/.cache/video-chromecast-player/` for faster access next time

### Advanced Chromecast Features

**Extended Status Display:**
1. After connecting to a Chromecast, an **"Extended Information"** expander appears in the sidebar
2. Expand it to see detailed information:
   - Device name and model
   - Active app
   - Playback status (PLAYING 🟢, PAUSED 🟡, BUFFERING 🔵, IDLE ⚪)
   - Currently playing media
   - Playback progress in percent
   - Group members (if in a group)

**Chromecast Groups (Multi-Room Audio):**
1. Create groups in the **Google Home App** on your smartphone
2. Add multiple Chromecast devices to a group
3. In the video player, groups are automatically displayed during device search
4. Connect to a group like a normal device
5. Audio is played synchronized on all devices in the group
6. The status display shows all group members

**Subtitles for Chromecast:**
- Subtitles are automatically transmitted with the video (experimental)
- Works with VTT format (better supported than SRT)
- HTTP server provides subtitle files

**Audio Track Selection:**
- Multiple audio tracks are supported on Chromecast
- Switch between available audio tracks possible

### Modes

- **Local**: Video is played on your computer
- **Chromecast**: Video is streamed to the connected Chromecast device

You can switch between modes with the switch in the control bar.

## ⚡ Hardware Acceleration

The player automatically detects your GPU and uses the appropriate hardware acceleration. This significantly reduces CPU load, especially with high-resolution videos (4K, 8K).

### AMD Graphics Cards (VA-API)

The player uses VA-API for hardware decoding and encoding.

**Check Hardware Acceleration:**
```bash
vainfo
```

**Expected Output:**
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

**Supported Codecs:**
- **H.264/AVC** (up to 4K)
- **H.265/HEVC** (up to 8K, 10-bit)
- **VP9** (up to 4K)
- **AV1** (on newer AMD cards)
- **MPEG-2**, **VC-1**

### NVIDIA Graphics Cards (NVDEC/NVENC)

The player uses NVDEC for hardware decoding and NVENC for hardware encoding.

**Requirements:**
- NVIDIA proprietary drivers must be installed
- FFmpeg with NVENC support (installed by install.sh)

**Check Hardware Acceleration:**
```bash
nvidia-smi
ffmpeg -encoders | grep nvenc
```

**Expected Output:**
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

**Supported Codecs:**
- **H.264/AVC** (up to 8K on newer cards)
- **H.265/HEVC** (up to 8K on newer cards)
- **AV1** (on RTX 40 series and newer)

**Performance Benefits:**
- Extremely fast video conversion (often 10-20x faster than software)
- Minimal CPU load (< 5%)
- Supports multiple parallel encoding sessions

## 🎞️ Supported Video Formats

Through RPM Fusion, **all common video formats** are supported:

### Container Formats
- **MP4** - H.264, H.265/HEVC, AV1
- **MKV** (Matroska) - all codecs
- **AVI** - DivX, XviD, etc.
- **WebM** - VP8, VP9, AV1
- **MOV** (QuickTime)
- **FLV** (Flash Video)
- **OGG/OGV** - Theora, Vorbis
- **MPG/MPEG** - MPEG-1, MPEG-2
- **TS** (Transport Stream)
- **WMV** - Windows Media Video

### Video Codecs
- **H.264/AVC** ✓ Hardware
- **H.265/HEVC** ✓ Hardware
- **VP8, VP9** ✓ Hardware
- **AV1** ✓ Hardware (on supported GPUs)
- **MPEG-2, MPEG-4**
- **DivX, XviD**
- **Theora**
- **VC-1** ✓ Hardware

### Audio Codecs
- **AAC, MP3, Opus, Vorbis, FLAC, AC3, DTS** and many more

## 🔧 Troubleshooting

### Automatic Debugging

For quick diagnosis of problems, run:
```bash
./debug-chromecast.sh
```

This script checks:
- Network connection
- Firewall configuration
- Python dependencies
- Chromecast devices on network
- HTTP server ports

### Automatically Configure Firewall

If Chromecast problems occur, run:
```bash
./fix-firewall.sh
```

This script automatically opens all necessary ports.

### Chromecast Not Found

**Symptom**: When clicking "Search Chromecast Devices", no devices are displayed.

**Solutions**:
1. Check if your computer and Chromecast are on the same Wi-Fi
2. Run the firewall fix script:
   ```bash
   ./fix-firewall.sh
   ```

   Or manually:
   ```bash
   sudo firewall-cmd --permanent --add-service=mdns
   sudo firewall-cmd --permanent --add-port=8008-8009/tcp
   sudo firewall-cmd --permanent --add-port=8765-8888/tcp
   sudo firewall-cmd --reload
   ```

3. Restart the Chromecast (unplug and plug back in)
4. Wait the full 15 seconds when scanning

### Video Won't Play

- Run the installation script to install all codecs
- Check console output for errors: `./videoplayer.py`
- Test GStreamer directly:
  ```bash
  gst-launch-1.0 filesrc location=your-video.mp4 ! decodebin ! autovideosink
  ```

### Hardware Acceleration Not Working

1. Check VA-API:
   ```bash
   vainfo
   ```

2. Check if GStreamer finds VA-API:
   ```bash
   gst-inspect-1.0 vaapi
   ```

3. Check environment variables:
   ```bash
   echo $LIBVA_DRIVER_NAME  # should be "radeonsi"
   ```

### Chromecast Streaming Not Working

**Symptom**: Connection to Chromecast works, but video is not played.

**Solutions**:

1. **Automatic Conversion**
   - The player automatically converts MKV/AVI to MP4
   - The first time this can take 10-60 seconds
   - Status is displayed in the app ("Converting video...")
   - Converted files are cached for faster access
   - If conversion fails, make sure FFmpeg is installed:
     ```bash
     sudo dnf install ffmpeg
     ```

2. **Manual Conversion** (if automatic doesn't work)
   ```bash
   # Fast conversion (without re-encoding)
   ffmpeg -i video.mkv -c copy video.mp4

   # With re-encoding (guaranteed compatibility)
   ffmpeg -i video.mkv -c:v libx264 -c:a aac video.mp4
   ```

3. **Clear Cache** (if problems with cached videos)
   ```bash
   rm -rf ~/.cache/video-chromecast-player/
   ```

4. **Open Firewall Ports**
   The HTTP server requires open ports:
   ```bash
   ./fix-firewall.sh
   ```

3. **Check Detailed Logs**
   Start the app in terminal for detailed error information:
   ```bash
   ./videoplayer.py
   ```

4. **Test HTTP Server Reachability**
   The app automatically tests if the HTTP server can be reached from Chromecast.
   If this test fails, it's a firewall problem.

5. **Network Problems**
   - Make sure computer and Chromecast are on the same subnet
   - Some routers block communication between devices (AP Isolation)
   - Disable "Client Isolation" in your router settings

## 📦 Dependencies

### System Packages (Distribution-specific)

**Arch Linux:**
- `gtk4`, `libadwaita` - UI framework
- `gstreamer`, `gst-plugins-*` - Multimedia framework
- `libva-mesa-driver` or `nvidia-utils` - Hardware acceleration
- `python-gobject` - Python GTK bindings
- `ffmpeg` - Video codecs

**Fedora:**
- `gtk4`, `libadwaita` - UI framework
- `gstreamer1-*` - Multimedia framework
- `mesa-va-drivers` - AMD hardware acceleration
- `python3-gobject` - Python GTK bindings
- `ffmpeg` - Video codecs (via RPM Fusion)

**Ubuntu/Debian:**
- `libgtk-4-1`, `libadwaita-1-0` - UI framework
- `gstreamer1.0-*` - Multimedia framework
- `va-driver-all` - Hardware acceleration
- `python3-gi` - Python GTK bindings
- `ffmpeg` - Video codecs

### Python Packages (All distributions)
- `PyGObject>=3.42.0` - Python GTK/GObject bindings
- `pychromecast>=13.0.0` - Chromecast control
- `zeroconf>=0.132.0` - Network service discovery

Install via pip:
```bash
pip3 install --user -r requirements.txt
```

## ⚡ Performance Tips

### CPU Load During Video Playback

With AMD hardware acceleration:
- **4K H.264**: ~5-10% CPU (without: 40-60%)
- **4K HEVC**: ~5-15% CPU (without: 60-80%)
- **1080p**: ~2-5% CPU (without: 20-40%)

### Check if Hardware Acceleration is Active

Start the player in terminal and watch for this message:
```
Hardware acceleration (VA-API) enabled
```

Use `htop` or `top` during playback to monitor CPU load.

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**DaHool** - [GitHub](https://github.com/berlinux2016/gnome-chromecast-player)

Made with love for Simone ❤️

## 🛠️ Development

### Project Structure

```
gnome-chromecast-player/
├── videoplayer.py              # Main application
├── i18n.py                     # Translation module
├── requirements.txt            # Python dependencies
│
├── install.sh                  # Fedora installer
├── install-arch.sh             # Arch Linux installer
├── PKGBUILD                    # AUR package build script
│
├── locale/                     # Translations
│   ├── de/LC_MESSAGES/         # German translations
│   └── en/LC_MESSAGES/         # English translations
│
├── README.md                   # This file
├── INSTALL-ARCH.md             # Arch Linux installation guide
├── I18N-GUIDE.md               # Translation guide
└── TRANSLATION-INTEGRATION-GUIDE.md  # i18n integration guide
```

### 🌍 Contributing Translations

We welcome translations! Currently supported:
- 🇬🇧 English
- 🇩🇪 German (Deutsch)

To add a new language, see [I18N-GUIDE.md](I18N-GUIDE.md).

### 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. Create a **Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. Open a **Pull Request**

#### Coding Standards
- Follow PEP 8 for Python code
- Comment complex logic in English
- Test your changes thoroughly on AMD and NVIDIA hardware (if possible)
- Add translations for new UI strings (see [I18N-GUIDE.md](I18N-GUIDE.md))

#### Bug Reports
If you find a bug:
1. Check if it's already reported as an issue
2. Create a new issue with:
   - Detailed description
   - Steps to reproduce
   - System information (Fedora version, GPU, etc.)
   - Log output from `./videoplayer.py`

## ⚠️ Known Limitations

1. Chromecast streaming requires videos to be accessible via HTTP
2. Some video codecs require additional plugins
3. The application was primarily tested on Fedora 43

## 🚀 Roadmap / Planned Features

### 🎨 Video Effects & Processing
- [x] **Video Rotation & Mirroring** - Rotate (90°, 180°, 270°) and mirror (horizontal/vertical) ✓
- [x] **Crop & Zoom** - Dynamic cropping and zooming during playback ✓
- [x] **Filter Presets** - Predefined effects (sepia, black & white, vintage) ✓
- [x] **Gamma Correction** - Extended gamma adjustment for better display ✓
- [ ] **RGB Channel Control** - Individual adjustment of red, green, and blue channels

### 📋 Playlist Management
- [x] **Playlist Thumbnails** - Automatic video preview images in playlist ✓
- [ ] **Playlist Search** - Quick filtering and searching in playlist
- [ ] **Smart Playlists** - Automatic playlists (recently played, most watched)
- [ ] **Playlist Categories** - Organization with tags and categories
- [ ] **Sort Options** - Sort by name, size, date, duration
- [ ] **Playlist Statistics** - Total duration, number of videos, average length
- [ ] **Network Playlists** - Support HTTP URLs for M3U playlists

### 📡 Extended Streaming Features
- [ ] **Twitch Integration** - Play live streams and VODs directly
- [ ] **Vimeo Support** - Native Vimeo video support
- [ ] **Dailymotion Support** - Stream Dailymotion videos
- [ ] **HLS Adaptive Streaming** - Automatic quality adjustment on bandwidth changes
- [ ] **Batch URL Download** - Load multiple URLs simultaneously
- [ ] **Stream Recorder** - Record live streams

### 🎯 User Experience
- [ ] **Context Menu** - Right-click menu with common actions
- [x] **Keyboard Shortcuts Help** - Visual overview of all shortcuts (H key) ✓
- [x] **Recent Files** - History of recently opened videos ✓
- [ ] **Quick Settings Panel** - Dashboard with frequently used settings
- [ ] **Save Window Position** - Automatically remember window position
- [ ] **Gesture Control** - Touch gestures for tablets and touchscreens
- [ ] **Dark Mode Toggle** - Manual toggle between light/dark theme

### ⚡ Power User Features
- [ ] **Segment Export** - Export video segments from A to B
- [ ] **Batch Conversion** - Convert multiple videos simultaneously
- [x] **Frame Stepping** - Single frames forward/backward (,/. keys) ✓
- [ ] **Metadata Editor** - Edit video tags, title, description
- [ ] **Codec Analysis** - Detailed codec information and bitrate graphs
- [ ] **Marking System** - Custom markers for important timestamps
- [ ] **GIF Export** - Export video segments as animated GIFs
- [ ] **Comparison Mode** - Compare two videos side by side

### 📊 Visualization & Statistics
- [ ] **Bitrate Graph** - Visual display of video bitrate
- [ ] **FPS Display** - Current framerate in real-time
- [ ] **CPU/GPU Monitoring** - Show system resource usage
- [ ] **Buffer Status** - Detailed display of buffer percentage
- [ ] **Chapter Minimap** - Visual chapter markers on timeline
- [ ] **Audio Waveform** - Audio waveform visualization
- [ ] **Thumbnail Grid** - Storyboard view of all video thumbnails

### 🔧 Chromecast Extensions
- [x] **Chromecast Subtitles** - Subtitle control on remote device ✓
- [x] **Chromecast Audio Tracks** - Audio track selection for Chromecast ✓
- [x] **Multi-Room Audio** - Synchronized playback on multiple devices ✓
- [x] **Chromecast Groups** - Support for audio groups ✓
- [x] **Extended Status Display** - Detailed Chromecast information ✓

### 🌐 Network & Integration
- [ ] **DLNA/UPnP Support** - Network media server integration
- [ ] **SMB/NFS Support** - Direct playback from network shares
- [ ] **Cloud Storage** - OneDrive, Google Drive, Dropbox integration
- [ ] **Auto-Subtitle Download** - Automatic download from OpenSubtitles.org

### 🎵 Audio Features
- [ ] **Audio Equalizer** - Bass, treble, and multi-band EQ
- [ ] **Audio Normalization** - Automatic volume adjustment
- [ ] **Surround Sound** - 5.1/7.1 audio spatialization
- [ ] **Audio Track Export** - Export audio tracks as separate files

### ⌨️ Additional Keyboard Shortcuts
- [ ] **J/L Keys** - -10/+10 seconds seek (VLC-style)
- [ ] **0-9 Keys** - Jump to 0%-90% of video length
- [x] **[/] Keys** - Decrease/increase playback speed ✓
- [x] **,/. Keys** - Frame backward/forward ✓
- [ ] **T Key** - Toggle subtitles on/off
- [x] **H Key** - Show shortcuts help ✓
- [ ] **Ctrl+O** - Open file dialog
- [ ] **Ctrl+U** - Open URL dialog
- [ ] **Ctrl+Q** - Quit application

### 🔄 Import/Export
- [ ] **Settings Backup** - Export/import configurations
- [ ] **Bookmark Export** - Backup all playback positions
- [ ] **Subtitle Extraction** - Extract subtitles from videos
- [ ] **Chapter Export** - Export chapter information (JSON/XML)
- [ ] **Metadata Export** - Video information as CSV/JSON

## 📊 Version History

### Version 2.0.1 (December 2025)
- 🌍 **Multilingual Support** - Complete internationalization (i18n) system with gettext
- 🇬🇧 **English Translation** - Full English UI translation
- 🇩🇪 **German Translation** - Vollständige deutsche Übersetzung (250+ Strings)
- 🏛️ **Arch Linux Support** - Native Arch Linux installation script with GPU detection
- 📦 **AUR Package** - PKGBUILD for Arch User Repository submission
- 📚 **Multi-Distribution Documentation** - Installation guides for Arch, Fedora, Ubuntu, and more
- 🔧 **Translation System** - Professional gettext-based i18n module (i18n.py)
- 🌐 **Auto Language Detection** - Automatic system language detection
- 📖 **Translation Guides** - Comprehensive documentation for translators and developers

### Version 2.0.0 (December 2025)
- ✨ **Recent Files** - History of recently opened videos (max. 10 entries)
- 🕐 Recent Files button in header bar with clock icon
- 📋 Automatic tracking of local video files
- 🗑️ "Clear History" option in menu
- 💾 Storage in `~/.config/video-chromecast-player/recent_files.json`
- ✨ **Playback Speed Shortcuts** - Keyboard shortcuts for speed changes
- ⌨️ **[** Key: Decrease speed (0.25x to 3.0x)
- ⌨️ **]** Key: Increase speed (0.25x to 3.0x)
- 🎯 10 speed levels with status feedback
- ✨ **Frame-by-Frame Navigation** - Precise single-frame navigation
- ⌨️ **,** Key: Frame backward (25 FPS / 0.04s)
- ⌨️ **.** Key: Frame forward (25 FPS / 0.04s)
- 🎬 Automatic pause for frame analysis
- 🎯 Perfect for screenshots and video analysis
- ✨ **Shortcuts Help Dialog** - Keyboard shortcuts overview
- ⌨️ **H** Key: Show shortcuts dialog
- 📖 Organized in 6 categories (Playback, Volume, View, A-B Loop, Navigation, Help)
- 📜 Scrollable list of all keyboard shortcuts
- 🎨 Professional design with monospace font for key names

### Version 1.3.0 (December 2025)
- ✨ **Playlist Thumbnails** - Automatic video preview images in playlist
- 🖼️ Each video shows a 60x60 pixel thumbnail from the middle of the video
- ⚡ Asynchronous thumbnail extraction without UI blocking
- 💾 Intelligent caching system in `~/.cache/gnome-chromecast-player/thumbnails/`
- 🎨 Placeholder icon for YouTube videos and URLs
- 🔧 `extract_video_thumbnail()` method for GStreamer-based extraction
- 🔧 `get_thumbnail_path()` method with MD5 hash for unique cache filenames
- 📊 Automatic cache management and reuse of existing thumbnails

### Version 1.2.0 (December 2025)
- ✨ **Chromecast Subtitles** - Subtitle support for Chromecast playback (VTT format)
- ✨ **Chromecast Audio Tracks** - Selection of audio tracks on remote device
- ✨ **Multi-Room Audio** - Synchronized playback on multiple Chromecast devices
- ✨ **Chromecast Groups** - Automatic detection and connection with groups
- ✨ **Extended Status Display** - Expandable detail display in sidebar
- 📊 Real-time status: Device name, model, app, playback status with icons
- 📊 Progress display in percent for Chromecast playback
- 🎵 Group members display for multi-room playback
- 🔧 `enable_subtitles()` and `disable_subtitles()` methods
- 🔧 `set_audio_track()` for audio track switching
- 🔧 `get_extended_status()` with 15+ status information
- 🔧 `discover_cast_groups()` and `connect_to_group()` for groups
- 🔧 `get_group_members()` shows all devices in group
- 🎨 Status icons: 🟢 PLAYING, 🟡 PAUSED, 🔵 BUFFERING, ⚪ IDLE
- 🎨 Automatic UI updates every 250ms in Chromecast mode

### Version 1.1.0 (December 2025)
- ✨ **Video Rotation & Mirroring** - Rotate (90°, 180°, 270°) and mirror (horizontal/vertical)
- ✨ **Zoom & Crop** - Dynamic zooming (0.5x-3.0x) and video cropping
- ✨ **Gamma Correction** - Extended brightness adjustment (0.1-3.0)
- ✨ **Filter Presets** - 10 predefined effects (sepia, vintage, black & white, grayscale, vivid, bright, dark, cool, warm)
- 🎨 New video effects button in header bar with tab interface
- 🎯 Tab 1: Rotation & mirroring with 6 options
- 🎯 Tab 2: Zoom (0.5x-3.0x) and crop (0-500px per side)
- 🎯 Tab 3: Gamma correction and 10 filter presets
- 🔄 Reset all effects button for quick reset
- ⚡ Extended GStreamer pipeline: videobalance → gamma → videoflip → videocrop → videoscale
- 💾 Real-time application of all effects without performance loss
- 🎨 Preset synchronization with equalizer settings

### Version 1.0.9 (December 2025)
- ✨ **YouTube Video Streaming** - Direct playback of YouTube videos via URL input
- 🎬 YouTube button in header bar for easy access
- 🔗 URL dialog for pasting YouTube links
- 📺 Support for local and Chromecast playback of YouTube content
- ⚡ Automatic video extraction with yt-dlp integration
- 🎯 Seamless integration into existing playlist functionality

### Version 1.8.0 (December 2025)
- ✨ **Go-To Time** - Jump to specific time position with dialog (MM:SS or HH:MM:SS)
- ✨ **Chapter Detection** - Automatic detection and navigation of MKV/MP4 chapters
- ✨ **Timeline Thumbnails** - Preview images on timeline hover with intelligent caching
- 🎯 Go-To button in control bar with jump icon
- 📑 Chapter button in header bar shows all available chapters
- 🖼️ Hover popover over timeline with 160x90 thumbnail preview
- 🎮 New keyboard shortcut: G for Go-To time dialog
- ⚡ GStreamer TOC API for chapter extraction
- 💾 Thumbnail cache for performant preview display

### Version 1.7.0 (December 2025)
- ✨ **Video Equalizer** - Real-time adjustment of brightness, contrast, saturation, and hue
- ✨ **A-B Loop** - Repeat loop between two points for learning videos
- 🎨 Equalizer button in header bar with 4 sliders and reset function
- 🔄 A-B Loop buttons (A, B, Clear) in control bar
- 🎮 New keyboard shortcuts: A (loop start), B (loop end), C (clear loop)
- 🎞️ Visual marking of active loop points with colored buttons
- ⚡ GStreamer videobalance element for hardware-accelerated video adjustments

### Version 1.6.0 (December 2025)
- ✨ **Playback Speed** - Adjustable speed from 0.5x to 2.0x
- ✨ **Screenshot Function** - Frame capture with S key, saves to ~/Pictures/Video-Screenshots/
- 🎚️ Speed button in header bar with 6 predefined speeds
- 📸 Automatic naming of screenshots with video name and timestamp
- 🎮 New keyboard shortcut: S for screenshot

### Version 1.5.0 (December 2025)
- ✨ **Audio Track Selection** - Switch between multiple audio tracks in multilingual videos
- ✨ **Bookmarks/Resume Function** - Automatic saving and resuming of playback
- 🔧 Intelligent bookmark system - Only at meaningful positions (not start/end)
- 💬 Resume dialog when opening videos with saved position

### Version 1.4.0 (December 2025)
- ✨ **Playlist Import** - M3U and PLS format support

### Version 1.3.0 (December 2025)
- ✨ **Keyboard Shortcuts** - Control via spacebar, arrow keys, etc.
- ✨ **Fullscreen Mode** - F11 for fullscreen playback
- ✨ **Drag & Drop** - Drag videos directly into window
- ✨ **Video Info Overlay** - Shows codec, resolution, and bitrate
- ✨ **Subtitle Support** - Automatic detection of SRT, ASS, VTT files

### Version 1.2.0 (December 2025)
- ✨ **Playlist Support** - Multiple videos in queue with auto-advance
- ✨ **Drag & Drop** - Drag videos directly into window (single or multiple)
- ✨ Timeline/seek function for local and Chromecast playback
- ✨ Volume control with slider for local and Chromecast playback
- ✨ NVIDIA hardware acceleration (NVDEC/NVENC)
- 🐛 Improved Chromecast compatibility (Xiaomi TVs)
- ⚡ Chromecast device search 30x faster (500ms instead of 15s)
- 🔧 Mode switching between local and Chromecast optimized
- 🎚️ Automatic volume synchronization on mode change
- ⏭️ Previous/Next video buttons for playlist navigation
- 🎵 Playlist management: Add, remove, select
- 🎨 Visual feedback for drag-and-drop (blue border)

### Version 1.0.0 (December 2025)
- 🎉 First release
- ✨ AMD VA-API hardware acceleration
- ✨ Automatic MKV/AVI to MP4 conversion
- ✨ GTK4/Libadwaita UI
- ✨ Chromecast streaming with HTTP server
