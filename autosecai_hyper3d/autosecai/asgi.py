"""ASGI config for AutoSecAI."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autosecai.settings")

application = get_asgi_application()

