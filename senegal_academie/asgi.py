"""
ASGI config for senegal_academie project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'senegal_academie.settings')

application = get_asgi_application()
