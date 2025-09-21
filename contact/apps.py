from django.apps import AppConfig


class ContactConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contact'
# contact/apps.py
from django.apps import AppConfig

class ContactConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contact"

    def ready(self):
        # import signals to register them
        import contact.signals  # noqa
