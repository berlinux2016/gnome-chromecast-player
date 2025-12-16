# Translation Integration Guide

This guide shows how to integrate the i18n translation system into videoplayer.py.

## Current Status

✅ Translation files created:
- `locale/de/LC_MESSAGES/gnome-chromecast-player.po` (18K) - German
- `locale/en/LC_MESSAGES/gnome-chromecast-player.po` (12K) - English
- Both compiled to `.mo` files

## Integration Steps

### Step 1: Import Translation Module

Add at the top of `videoplayer.py` after the other imports:

```python
# Add after line 32 (after other imports)
from i18n import _, get_current_language, init_translation

# Initialize translations
init_translation()
```

### Step 2: Wrap Translatable Strings

Replace hardcoded German strings with translation calls:

#### Before:
```python
self.set_title("Video Chromecast Player")
button.set_tooltip_text("Video öffnen")
self.status_label.set_text("Kein Video geladen")
```

#### After:
```python
self.set_title(_("Video Chromecast Player"))
button.set_tooltip_text(_("Open Video"))
self.status_label.set_text(_("No video loaded"))
```

### Step 3: Format Strings with Variables

For strings with variables, use Python string formatting:

#### Before:
```python
self.status_label.set_text(f"{len(video_files)} Video(s) zur Playlist hinzugefügt")
```

#### After:
```python
self.status_label.set_text(_("%d video(s) added to playlist") % len(video_files))

# Or with named placeholders:
message = _("Jumped to %(time)s") % {"time": self.format_time(seconds)}
```

### Step 4: Plural Forms

For plurals, add to `i18n.py`:

```python
def ngettext(singular, plural, n):
    """Handle plural forms"""
    if _translation is None:
        init_translation()
    return _translation.ngettext(singular, plural, n)
```

Then use in code:

```python
from i18n import _, ngettext

message = ngettext(
    "%d video added",
    "%d videos added",
    count
) % count
```

## Priority Strings to Translate

### High Priority (User-facing UI)

1. **Button labels** (lines 2931-3903):
   ```python
   open_button.set_tooltip_text(_("Open Video"))
   scan_button.set_tooltip_text(_("Search Chromecast Devices"))
   ```

2. **Status messages** (lines 2883-5010):
   ```python
   self.status_label.set_text(_("No devices found"))
   self.status_label.set_text(_("Converting video..."))
   ```

3. **Dialog texts** (lines 4568-4835):
   ```python
   content_box.append(Gtk.Label(label=_("Enter target time (format: MM:SS or HH:MM:SS)")))
   ```

4. **Section labels** (lines 3122-3362):
   ```python
   playlist_label = Gtk.Label(label=_("Playlist"))
   label = Gtk.Label(label=_("Chromecast Devices"))
   ```

5. **Effect labels** (lines 3974-4276):
   ```python
   title_label = Gtk.Label(label=_("Video Equalizer"))
   brightness_label = Gtk.Label(label=_("Brightness"))
   ```

### Medium Priority (Status/Debug messages)

6. **Console output** (lines 406-1024):
   ```python
   print(_("=== Automatic Video Conversion ==="))
   print(_("✓ Conversion successful!"))
   ```

### Low Priority (Comments and docstrings)

7. **Docstrings** - Keep in English for code documentation
8. **Comments** - Keep in English for developers

## Quick Reference: Common Translations

```python
# Buttons
_("Open Video")          # Video öffnen
_("Play")                # Wiedergabe
_("Pause")               # Pause
_("Stop")                # Stopp
_("Next")                # Weiter
_("Previous")            # Zurück

# Status
_("Loading...")          # Lädt...
_("Converting...")       # Konvertiere...
_("No video loaded")     # Kein Video geladen
_("Paused")              # Pausiert
_("Playing")             # Läuft

# Chromecast
_("No devices found")                    # Keine Geräte gefunden
_("Search Chromecast Devices")           # Chromecast-Geräte suchen
_("Connected to")                        # Verbunden mit

# Errors
_("Error: %s")           # Fehler: %s
_("File no longer exists")  # Datei existiert nicht mehr
```

## Example: Converting a Section

### Before (German):
```python
def create_playlist_section(self):
    playlist_label = Gtk.Label(label="Playlist")
    self.playlist_count_label = Gtk.Label(label="(0)")

    add_playlist_button = Gtk.Button()
    add_playlist_button.set_tooltip_text("Videos zur Playlist hinzufügen")

    clear_playlist_button = Gtk.Button()
    clear_playlist_button.set_tooltip_text("Playlist leeren")
```

### After (Multilingual):
```python
from i18n import _

def create_playlist_section(self):
    playlist_label = Gtk.Label(label=_("Playlist"))
    self.playlist_count_label = Gtk.Label(label="(0)")

    add_playlist_button = Gtk.Button()
    add_playlist_button.set_tooltip_text(_("Add videos to playlist"))

    clear_playlist_button = Gtk.Button()
    clear_playlist_button.set_tooltip_text(_("Clear playlist"))
```

## Testing Translations

### Test German:
```bash
LANG=de_DE.UTF-8 ./videoplayer.py
```

### Test English:
```bash
LANG=en_US.UTF-8 ./videoplayer.py
```

### Test with specific language:
```python
# At program start
from i18n import set_language
set_language('de')  # Force German
set_language('en')  # Force English
```

## Automated Translation Script

Create a script to automatically replace common patterns:

```bash
#!/bin/bash
# replace-strings.sh - Helper script to replace common strings

# Backup original file
cp videoplayer.py videoplayer.py.backup

# Replace common button tooltips
sed -i 's/set_tooltip_text("Video öffnen")/set_tooltip_text(_("Open Video"))/g' videoplayer.py
sed -i 's/set_tooltip_text("Vollbild (F11)")/set_tooltip_text(_("Fullscreen (F11)"))/g' videoplayer.py

# Replace status messages
sed -i 's/set_text("Keine Geräte gefunden")/set_text(_("No devices found"))/g' videoplayer.py
sed -i 's/set_text("Kein Video geladen")/set_text(_("No video loaded"))/g' videoplayer.py

# Replace labels
sed -i 's/label="Playlist"/label=_("Playlist")/g' videoplayer.py
sed -i 's/label="Chromecast-Geräte"/label=_("Chromecast Devices")/g' videoplayer.py

echo "Replacement complete. Check videoplayer.py for changes."
echo "Original backed up to videoplayer.py.backup"
```

## Checklist for Full Integration

- [ ] Add `from i18n import _` import at top
- [ ] Wrap all `set_label()` strings
- [ ] Wrap all `set_text()` strings
- [ ] Wrap all `set_tooltip_text()` strings
- [ ] Wrap all `label=` parameters
- [ ] Wrap dialog title strings
- [ ] Wrap status message strings
- [ ] Convert format strings to use `%` or `.format()`
- [ ] Test with `LANG=de_DE.UTF-8`
- [ ] Test with `LANG=en_US.UTF-8`
- [ ] Update all `.po` files with new strings
- [ ] Recompile `.mo` files

## Common Issues

### Issue 1: Translation not showing

**Problem**: Strings still show in German even with `LANG=en_US.UTF-8`

**Solution**:
1. Check if `.mo` file exists and is compiled
2. Verify `locale/` directory is in the correct location
3. Ensure `i18n.py` is imported correctly
4. Test: `python3 -c "from i18n import _; print(_('Open Video'))"`

### Issue 2: Format string errors

**Problem**: `TypeError: not all arguments converted during string formatting`

**Solution**: Ensure format specifiers match:
```python
# Wrong
_("Video: %s") % (name, count)

# Correct
_("Video: %s, Count: %d") % (name, count)
```

### Issue 3: Missing translations

**Problem**: Some strings show msgid instead of translation

**Solution**:
1. Check if string exists in `.po` file
2. Verify `.mo` file is recompiled after changes
3. Restart application to reload translations

## Resources

- GNU gettext manual: https://www.gnu.org/software/gettext/manual/
- Python i18n best practices: https://docs.python.org/3/library/gettext.html
- GTK internationalization: https://developer.gnome.org/documentation/tutorials/translation.html

## Next Steps

1. **Phase 1**: Integrate high-priority UI strings (buttons, labels, tooltips)
2. **Phase 2**: Integrate status messages and dialogs
3. **Phase 3**: Integrate console output messages
4. **Phase 4**: Add more languages (French, Spanish, etc.)
5. **Phase 5**: Create automated tests for translations

## Support

For questions about translation integration:
- Check [I18N-GUIDE.md](I18N-GUIDE.md)
- Review `i18n.py` module documentation
- Open an issue on GitHub
