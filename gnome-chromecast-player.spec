Name:           gnome-chromecast-player
Version:        2.0.0
Release:        2%{?dist}
Summary:        Modern GTK4 video player with Chromecast support

License:        MIT
URL:            https://github.com/berlinux2016/gnome-chromecast-player
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

Requires:       python3 >= 3.9
Requires:       python3-pip
Requires:       gtk4
Requires:       libadwaita
Requires:       python3-gobject
Requires:       gstreamer1
Requires:       gstreamer1-plugins-base
Requires:       gstreamer1-plugins-good
Requires:       gstreamer1-plugins-bad-free
Requires:       gstreamer1-plugins-bad-freeworld
Requires:       gstreamer1-plugins-ugly-free
Requires:       gstreamer1-vaapi
Requires:       python3-requests
Requires:       yt-dlp
Requires:       ffmpeg

%description
A modern GTK4/Libadwaita video player with Chromecast streaming support.
Features include hardware acceleration (VA-API, NVDEC, Vulkan Video), YouTube streaming,
playlist support, frame-by-frame navigation, playback speed control,
A-B loop, video effects, equalizer, and much more.

%prep
%autosetup

%build
# Nothing to build for pure Python application

%install
# Create directory structure
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_datadir}/%{name}
install -d %{buildroot}%{_datadir}/applications
install -d %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
install -d %{buildroot}%{_datadir}/metainfo

# Install main application
install -m 755 videoplayer.py %{buildroot}%{_datadir}/%{name}/videoplayer.py

# Create wrapper script
cat > %{buildroot}%{_bindir}/%{name} << 'EOF'
#!/bin/bash
# Force GTK4 to use OpenGL renderer instead of Vulkan to avoid NVIDIA driver crashes
export GSK_RENDERER=gl
exec python3 %{_datadir}/%{name}/videoplayer.py "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/%{name}

# Install desktop file
install -m 644 gnome-chromecast-player.desktop %{buildroot}%{_datadir}/applications/

# Install icon (if exists)
if [ -f gnome-chromecast-player.svg ]; then
    install -m 644 gnome-chromecast-player.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/
fi

# Install AppStream metadata (if exists)
if [ -f gnome-chromecast-player.appdata.xml ]; then
    install -m 644 gnome-chromecast-player.appdata.xml %{buildroot}%{_datadir}/metainfo/
fi

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop
if [ -f %{buildroot}%{_datadir}/metainfo/%{name}.appdata.xml ]; then
    appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/%{name}.appdata.xml
fi

%post
# Install pychromecast via pip (not available as RPM in Fedora)
if ! python3 -c "import pychromecast" 2>/dev/null; then
    echo "Installing pychromecast via pip..."
    pip3 install --user pychromecast 2>/dev/null || \
    python3 -m pip install --user pychromecast 2>/dev/null || \
    echo "Warning: Could not install pychromecast automatically. Please run: pip3 install --user pychromecast"
fi

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/metainfo/%{name}.appdata.xml

%changelog
* Thu Dec 18 2025 berlinux2016 <berlinux2016@github.com> - 2.0.0-2
- Added Vulkan Video decoder support for NVIDIA GPUs
- Added gstreamer1-plugins-bad-freeworld dependency
- Fixed pychromecast installation via pip in post-install script
- Fixed GTK4 crash on NVIDIA by forcing OpenGL renderer (GSK_RENDERER=gl)

* Sun Dec 14 2025 berlinux2016 <berlinux2016@github.com> - 2.0.0-1
- Version 2.0.0 release
- Added Recent Files feature (max. 10 entries)
- Added Playback Speed Shortcuts ([ / ] keys)
- Added Frame-by-Frame Navigation (, / . keys)
- Added Shortcuts Help Dialog (H key)
- Fixed critical Play/Pause button handler bugs
- Improved Chromecast streaming workflow

* Tue Dec 09 2025 berlinux2016 <berlinux2016@github.com> - 1.3.0-1
- Added Playlist Thumbnails with async extraction
- Intelligent caching system for thumbnails
- Performance optimizations

* Mon Dec 08 2025 berlinux2016 <berlinux2016@github.com> - 1.2.0-1
- Added YouTube video streaming support
- Added live-scrubbing for timeline
- Drag & Drop support for video files
- Improved UI responsiveness

* Sun Dec 07 2025 berlinux2016 <berlinux2016@github.com> - 1.0.0-1
- Initial RPM release
- GTK4/Libadwaita UI
- Chromecast streaming support
- Hardware acceleration (VA-API, NVDEC)
- Automatic MKV/AVI to MP4 conversion
