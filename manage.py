#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import argparse
from django.conf import settings


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')

    argv = customCommands()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(argv)


def customCommands():
    argv = sys.argv

    # Django commands other than 'runserver' disables NLP modules, or by explicitly passing 'disable-nlp'
    if not 'runserver' in argv or '--disable-nlp' in argv:
        print("NLP disabled.")
        settings.ENABLE_NLP = False
    else:
        settings.ENABLE_NLP = True

    settings.ENABLE_SECTIONIZER = True
    settings.ENABLE_TOKENIZER = True
    settings.ENABLE_SENTENCIZER = True
    settings.ENABLE_ENTITYMATCHER = True
    settings.ENABLE_PHRASENORMALIZER = True

    # 'sectionizer-only' commands disables NLP but leaves sectionizer enabled only
    if '--sectionizer-only' in argv:
        print("Running in sectionizer-only mode, all other NLP functions disabled.")
        settings.ENABLE_NLP = True
        settings.ENABLE_TOKENIZER = False
        settings.ENABLE_SENTENCIZER = False
        settings.ENABLE_ENTITYMATCHER = False
        settings.ENABLE_PHRASENORMALIZER = False

    parser = argparse.ArgumentParser()
    parser.add_argument('--sectionizer-only',
                        help="Enable only Sectionizer of the NLP module only.", action="store_true")
    parser.add_argument('--disable-nlp',
                        help="Disable NLP.", action="store_true")
    args, argv = parser.parse_known_args(argv)

    return argv


if __name__ == '__main__':
    main()
