#!/usr/bin/env python3
"""
Internationalization (i18n) module for Video Chromecast Player
Provides gettext-based translations for multiple languages
"""

import gettext
import os
import locale
from pathlib import Path

# Get the application directory
APP_DIR = Path(__file__).parent.absolute()
LOCALE_DIR = APP_DIR / "locale"

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch'
}

# Initialize translation
_translation = None
_current_language = None

def init_translation(lang=None):
    """
    Initialize the translation system

    Args:
        lang: Language code (e.g., 'en', 'de'). If None, uses system locale.
    """
    global _translation, _current_language

    # Determine language
    if lang is None:
        # Try to get system language
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang = system_locale.split('_')[0]  # Extract language code (e.g., 'de' from 'de_DE')
        except:
            pass

    # Fallback to English
    if lang not in SUPPORTED_LANGUAGES:
        lang = 'en'

    _current_language = lang

    # Load translation
    try:
        _translation = gettext.translation(
            'gnome-chromecast-player',
            localedir=str(LOCALE_DIR),
            languages=[lang],
            fallback=True
        )
    except Exception as e:
        print(f"Warning: Could not load translation for '{lang}': {e}")
        _translation = gettext.NullTranslations()

    return _translation

def _(text):
    """
    Translate a text string

    Args:
        text: The text to translate

    Returns:
        Translated text
    """
    global _translation

    if _translation is None:
        init_translation()

    return _translation.gettext(text)

def get_current_language():
    """Get the current language code"""
    return _current_language or 'en'

def set_language(lang):
    """
    Change the current language

    Args:
        lang: Language code (e.g., 'en', 'de')
    """
    if lang in SUPPORTED_LANGUAGES:
        init_translation(lang)
        return True
    return False

def get_supported_languages():
    """Get a dictionary of supported languages"""
    return SUPPORTED_LANGUAGES.copy()

# Initialize with system locale by default
init_translation()
