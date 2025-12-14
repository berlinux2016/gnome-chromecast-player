# Makefile for GNOME Chromecast Player

APP_NAME = gnome-chromecast-player
VERSION = 2.0.0
PREFIX ?= /usr/local
DESTDIR ?=

BINDIR = $(DESTDIR)$(PREFIX)/bin
SHAREDIR = $(DESTDIR)$(PREFIX)/share
APPDIR = $(SHAREDIR)/$(APP_NAME)
DESKTOPDIR = $(SHAREDIR)/applications
ICONDIR = $(SHAREDIR)/icons/hicolor/scalable/apps
METAINFODIR = $(SHAREDIR)/metainfo

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
NC = \033[0m

.PHONY: all install uninstall clean rpm local-install local-uninstall check help

all:
	@echo "$(BLUE)GNOME Chromecast Player v$(VERSION)$(NC)"
	@echo ""
	@echo "Available targets:"
	@echo "  make install          - Install to $(PREFIX)"
	@echo "  make uninstall        - Remove from $(PREFIX)"
	@echo "  make rpm              - Build RPM package"
	@echo "  make local-install    - Install to ~/.local"
	@echo "  make local-uninstall  - Remove from ~/.local"
	@echo "  make check            - Check dependencies"
	@echo "  make clean            - Clean build artifacts"

install:
	@echo "$(BLUE)[INSTALL]$(NC) Installing to $(PREFIX)..."
	install -d $(BINDIR)
	install -d $(APPDIR)
	install -d $(DESKTOPDIR)
	install -d $(ICONDIR)
	install -d $(METAINFODIR)

	install -m 755 videoplayer.py $(APPDIR)/videoplayer.py

	@echo '#!/bin/bash' > $(BINDIR)/$(APP_NAME)
	@echo 'exec python3 $(PREFIX)/share/$(APP_NAME)/videoplayer.py "$$@"' >> $(BINDIR)/$(APP_NAME)
	chmod 755 $(BINDIR)/$(APP_NAME)

	install -m 644 $(APP_NAME).desktop $(DESKTOPDIR)/

	@if [ -f "$(APP_NAME).svg" ]; then \
		install -m 644 $(APP_NAME).svg $(ICONDIR)/; \
	fi

	@if [ -f "$(APP_NAME).appdata.xml" ]; then \
		install -m 644 $(APP_NAME).appdata.xml $(METAINFODIR)/; \
	fi

	@echo "$(GREEN)[SUCCESS]$(NC) Installation complete!"
	@if [ "$(PREFIX)" = "/usr/local" ] || [ "$(PREFIX)" = "/usr" ]; then \
		echo "$(BLUE)[INFO]$(NC) Updating desktop database..."; \
		update-desktop-database $(DESKTOPDIR) 2>/dev/null || true; \
		echo "$(BLUE)[INFO]$(NC) Updating icon cache..."; \
		gtk-update-icon-cache -f -t $(SHAREDIR)/icons/hicolor 2>/dev/null || true; \
	fi

uninstall:
	@echo "$(BLUE)[UNINSTALL]$(NC) Removing from $(PREFIX)..."
	rm -f $(BINDIR)/$(APP_NAME)
	rm -rf $(APPDIR)
	rm -f $(DESKTOPDIR)/$(APP_NAME).desktop
	rm -f $(ICONDIR)/$(APP_NAME).svg
	rm -f $(METAINFODIR)/$(APP_NAME).appdata.xml

	@if [ "$(PREFIX)" = "/usr/local" ] || [ "$(PREFIX)" = "/usr" ]; then \
		echo "$(BLUE)[INFO]$(NC) Updating desktop database..."; \
		update-desktop-database $(DESKTOPDIR) 2>/dev/null || true; \
		echo "$(BLUE)[INFO]$(NC) Updating icon cache..."; \
		gtk-update-icon-cache -f -t $(SHAREDIR)/icons/hicolor 2>/dev/null || true; \
	fi

	@echo "$(GREEN)[SUCCESS]$(NC) Uninstallation complete!"

rpm:
	@echo "$(BLUE)[RPM]$(NC) Building RPM package..."
	./build-rpm.sh

local-install:
	@echo "$(BLUE)[LOCAL]$(NC) Installing to ~/.local..."
	./install-local.sh install

local-uninstall:
	@echo "$(BLUE)[LOCAL]$(NC) Removing from ~/.local..."
	./install-local.sh uninstall

check:
	@echo "$(BLUE)[CHECK]$(NC) Checking dependencies..."
	@echo ""
	@echo "Build dependencies:"
	@for pkg in rpm-build rpmdevtools desktop-file-utils libappstream-glib; do \
		if rpm -q $$pkg >/dev/null 2>&1; then \
			echo "  $(GREEN)✓$(NC) $$pkg"; \
		else \
			echo "  $(BLUE)✗$(NC) $$pkg (not installed)"; \
		fi; \
	done
	@echo ""
	@echo "Runtime dependencies:"
	@for pkg in python3 gtk4 libadwaita python3-gobject gstreamer1 \
		gstreamer1-plugins-base gstreamer1-plugins-good \
		gstreamer1-plugins-bad-free gstreamer1-vaapi \
		python3-pychromecast python3-requests yt-dlp ffmpeg; do \
		if rpm -q $$pkg >/dev/null 2>&1; then \
			echo "  $(GREEN)✓$(NC) $$pkg"; \
		else \
			echo "  $(BLUE)✗$(NC) $$pkg (not installed)"; \
		fi; \
	done
	@echo ""

clean:
	@echo "$(BLUE)[CLEAN]$(NC) Cleaning build artifacts..."
	rm -rf ~/rpmbuild/BUILD/$(APP_NAME)-$(VERSION)
	rm -f ~/rpmbuild/SOURCES/$(APP_NAME)-$(VERSION).tar.gz
	rm -f ~/rpmbuild/SPECS/$(APP_NAME).spec
	@echo "$(GREEN)[SUCCESS]$(NC) Clean complete!"

help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║   GNOME Chromecast Player v$(VERSION) - Build Help     ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "Installation targets:"
	@echo "  make install              - Install system-wide to $(PREFIX)"
	@echo "  make uninstall            - Uninstall from $(PREFIX)"
	@echo "  make local-install        - Install to ~/.local (user only)"
	@echo "  make local-uninstall      - Remove from ~/.local"
	@echo ""
	@echo "Package building:"
	@echo "  make rpm                  - Build RPM package (Fedora/RHEL)"
	@echo ""
	@echo "Utilities:"
	@echo "  make check                - Check installed dependencies"
	@echo "  make clean                - Clean build artifacts"
	@echo "  make help                 - Show this help message"
	@echo ""
	@echo "Custom installation prefix:"
	@echo "  make install PREFIX=/opt/custom"
	@echo ""
	@echo "Examples:"
	@echo "  sudo make install         - Install system-wide"
	@echo "  make local-install        - Install for current user"
	@echo "  make rpm                  - Build RPM for distribution"
	@echo ""
