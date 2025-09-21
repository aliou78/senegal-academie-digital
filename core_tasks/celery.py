import os
from celery import Celery

# Indique à Django d’utiliser ton fichier settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Charger la config depuis settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Découvre automatiquement toutes les tâches dans les apps Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
