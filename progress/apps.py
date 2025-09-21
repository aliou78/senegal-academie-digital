from django.apps import AppConfig


class ProgressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'progress'
# progress/apps.py
from django.apps import AppConfig

class ProgressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'progress'
    verbose_name = 'Suivi des Progrès'
    
    def ready(self):
        import progress.signals  # Importer les signaux