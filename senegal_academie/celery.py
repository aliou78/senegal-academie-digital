import os
from celery import Celery

# Configuration de Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'senegal_academie.settings')

app = Celery('senegal_academie')

# Configuration depuis les settings Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
