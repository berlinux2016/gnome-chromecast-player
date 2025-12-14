Name:           gnome-chromecast-player
Version:        2.0.0
Release:        1%{?dist}
Summary:        Modern GTK4 video player with Chromecast support

License:        MIT
URL:            https://github.com/berlinux2016/gnome-chromecast-player
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib

Requires:       python3 >= 3.9
Requires:       gtk4
Requires:       libadwaita
Requires:       python3-gobject
Requires:       gstreamer1
Requires:       gstreamer1-plugins-base
Requires:       gstreamer1-plugins-good
Requires:       gstreamer1-plugins-bad-free
Requires:       gstreamer1-plugins-ugly-free
Requires:       gstreamer1-vaapi
Requires:       python3-pychromecast
Requires:       python3-requests
Requires:       yt-dlp
Requires:       ffmpeg

%description
A modern GTK4/Libadwaita video player with Chromecast streaming support.
Features include hardware acceleration (VA-API, NVDEC), YouTube streaming,
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

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_datadir}/metainfo/%{name}.appdata.xml

%changelog
* Sat Dec 14 2025 berlinux2016 <berlinux2016@github.com> - 2.0.0-1
- Version 2.0.0 release
- Added Recent Files feature (max. 10 entries)
- Added Playback Speed Shortcuts ([ / ] keys)
- Added Frame-by-Frame Navigation (, / . keys)
- Added Shortcuts Help Dialog (H key)
- Fixed critical Play/Pause button handler bugs
- Improved Chromecast streaming workflow

* Mon Dec 09 2025 berlinux2016 <berlinux2016@github.com> - 1.3.0-1
- Added Playlist Thumbnails with async extraction
- Intelligent caching system for thumbnails
- Performance optimizations

* Sun Dec 08 2025 berlinux2016 <berlinux2016@github.com> - 1.2.0-1
- Added YouTube video streaming support
- Added live-scrubbing for timeline
- Drag & Drop support for video files
- Improved UI responsiveness

* Sat Dec 07 2025 berlinux2016 <berlinux2016@github.com> - 1.0.0-1
- Initial RPM release
- GTK4/Libadwaita UI
- Chromecast streaming support
- Hardware acceleration (VA-API, NVDEC)
- Automatic MKV/AVI to MP4 conversion
