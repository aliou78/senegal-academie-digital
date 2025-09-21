"""
WSGI config for senegal_academie project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'senegal_academie.settings')

application = get_wsgi_application()
