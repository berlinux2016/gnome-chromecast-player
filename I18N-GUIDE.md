# Internationalization (i18n) Guide

This guide explains how to use and maintain translations for the Video Chromecast Player.

## Overview

The application supports multiple languages using GNU gettext. Currently supported languages:

- **English (en)** - Default language
- **German (de)** - Deutsche Übersetzung

## For Users

### Changing Language

The application automatically detects your system language. To manually change the language:

```bash
# Run with German
LANG=de_DE.UTF-8 ./videoplayer.py

# Run with English
LANG=en_US.UTF-8 ./videoplayer.py
```

You can also set this permanently in your system settings.

## For Developers

### Project Structure

```
locale/
├── messages.pot                    # Translation template (source)
├── de/
│   └── LC_MESSAGES/
│       ├── gnome-chromecast-player.po   # German translation source
│       └── gnome-chromecast-player.mo   # Compiled German translation
└── en/
    └── LC_MESSAGES/
        ├── gnome-chromecast-player.po   # English translation source
        └── gnome-chromecast-player.mo   # Compiled English translation
```

### Adding Translations to Code

1. Import the translation function:
   ```python
   from i18n import _
   ```

2. Wrap translatable strings:
   ```python
   # Before
   button.set_label("Open Video")

   # After
   button.set_label(_("Open Video"))
   ```

3. Use in f-strings:
   ```python
   status = _("Connected to")
   message = f"{status} {device_name}"
   ```

### Extracting Translatable Strings

When you add new translatable strings to the code:

1. Extract strings to update the template:
   ```bash
   xgettext --language=Python --keyword=_ --output=locale/messages.pot videoplayer.py i18n.py
   ```

2. Update existing translations:
   ```bash
   # Update German
   msgmerge --update locale/de/LC_MESSAGES/gnome-chromecast-player.po locale/messages.pot

   # Update English
   msgmerge --update locale/en/LC_MESSAGES/gnome-chromecast-player.po locale/messages.pot
   ```

3. Edit the `.po` files to add translations

4. Compile translations:
   ```bash
   # German
   msgfmt locale/de/LC_MESSAGES/gnome-chromecast-player.po -o locale/de/LC_MESSAGES/gnome-chromecast-player.mo

   # English
   msgfmt locale/en/LC_MESSAGES/gnome-chromecast-player.po -o locale/en/LC_MESSAGES/gnome-chromecast-player.mo
   ```

### Adding a New Language

1. Create the language directory:
   ```bash
   mkdir -p locale/[LANG]/LC_MESSAGES
   ```

2. Initialize translation from template:
   ```bash
   msginit --input=locale/messages.pot --locale=[LANG] --output=locale/[LANG]/LC_MESSAGES/gnome-chromecast-player.po
   ```

3. Translate the strings in the `.po` file

4. Compile the translation:
   ```bash
   msgfmt locale/[LANG]/LC_MESSAGES/gnome-chromecast-player.po -o locale/[LANG]/LC_MESSAGES/gnome-chromecast-player.mo
   ```

5. Add language to `i18n.py`:
   ```python
   SUPPORTED_LANGUAGES = {
       'en': 'English',
       'de': 'Deutsch',
       '[LANG]': '[Native Name]'
   }
   ```

## Translation Workflow

### For Translators

1. **Get the latest template**:
   ```bash
   git pull origin main
   ```

2. **Edit translations**:
   Use a PO editor like:
   - **Poedit** - GUI editor for .po files
   - **Lokalize** - KDE translation tool
   - **gtranslator** - GNOME translation tool
   - Any text editor

3. **Edit the .po file**:
   ```po
   #: videoplayer.py:123
   msgid "Open Video"
   msgstr "Video öffnen"
   ```

4. **Test translations**:
   ```bash
   # Compile
   msgfmt locale/de/LC_MESSAGES/gnome-chromecast-player.po -o locale/de/LC_MESSAGES/gnome-chromecast-player.mo

   # Test
   LANG=de_DE.UTF-8 ./videoplayer.py
   ```

5. **Submit translations**:
   - Open a pull request with updated `.po` and `.mo` files
   - Or create an issue with the translated `.po` file attached

## Best Practices

### For Developers

1. **Keep strings simple**:
   ```python
   # Good
   _("Open Video")

   # Bad - contains formatting
   _("Open Video: %s" % filename)  # Use f-strings instead
   ```

2. **Provide context**:
   ```python
   # Add comments for translators
   # TRANSLATORS: This is the window title
   window.set_title(_("Video Chromecast Player"))
   ```

3. **Don't translate code**:
   ```python
   # Good
   if mode == "local":
       status = _("Playing locally")

   # Bad
   if mode == _("local"):  # Don't translate variable values
   ```

4. **Handle plurals**:
   ```python
   from i18n import ngettext

   message = ngettext(
       "1 video found",
       "%d videos found",
       count
   ) % count
   ```

### For Translators

1. **Keep the same formatting**:
   - Preserve `%s`, `%d`, etc. placeholders
   - Keep the same number of spaces
   - Maintain special characters like `\n`

2. **Context matters**:
   - Read surrounding code comments
   - Check how the string is used in the UI
   - Ask if unclear

3. **Be consistent**:
   - Use the same translation for the same term
   - Follow platform conventions (GTK/GNOME terminology)

4. **Test your translations**:
   - Check that text fits in UI elements
   - Verify special characters display correctly
   - Test keyboard shortcuts (may need localization)

## Common Issues

### Translation Not Loading

1. Check `.mo` files are compiled:
   ```bash
   ls -la locale/*/LC_MESSAGES/*.mo
   ```

2. Verify locale directory exists:
   ```bash
   file locale/de/LC_MESSAGES/gnome-chromecast-player.mo
   ```

3. Test with verbose output:
   ```bash
   LANG=de_DE.UTF-8 python3 -c "from i18n import _; print(_('Open Video'))"
   ```

### Fuzzy Translations

When updating translations, msgmerge marks changed strings as "fuzzy":

```po
#, fuzzy
msgid "New string"
msgstr "Old translation"
```

- Review and update the translation
- Remove the `#, fuzzy` line
- Recompile the `.mo` file

### Character Encoding

Always use UTF-8 encoding for `.po` files:

```po
"Content-Type: text/plain; charset=UTF-8\n"
```

## Useful Tools

- **Poedit**: https://poedit.net/
- **Lokalize**: Part of KDE
- **gtranslator**: Part of GNOME
- **gettext**: Command-line tools
  ```bash
  sudo pacman -S gettext  # Arch
  sudo dnf install gettext  # Fedora
  ```

## Resources

- GNU gettext manual: https://www.gnu.org/software/gettext/manual/
- Python gettext module: https://docs.python.org/3/library/gettext.html
- Translation Project: https://translationproject.org/

## Contributing Translations

We welcome translations! To contribute:

1. Fork the repository
2. Add/update translations in `locale/[LANG]/LC_MESSAGES/`
3. Test your translations
4. Submit a pull request

Languages we'd love to see:
- Spanish (es)
- French (fr)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Chinese (zh)
- Japanese (ja)
- And more!

## Maintenance Checklist

Before each release:

- [ ] Extract new strings: `xgettext ...`
- [ ] Update all `.po` files: `msgmerge ...`
- [ ] Review fuzzy translations
- [ ] Compile all `.mo` files: `msgfmt ...`
- [ ] Test each language
- [ ] Update version in `.po` files
- [ ] Commit `.po` and `.mo` files

## Contact

For translation questions or help:
- Open an issue: https://github.com/berlinux2016/gnome-chromecast-player/issues
- Email: [your-email@example.com]
