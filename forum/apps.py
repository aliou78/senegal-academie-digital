from django.apps import AppConfig

class ForumsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forum"

    def ready(self):
        # enregistre les signaux si tu en as
        import forum.signals  # noqa
