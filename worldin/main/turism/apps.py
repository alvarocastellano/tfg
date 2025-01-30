from django.apps import AppConfig


class TurismConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main.turism'

    def ready(self):
        import main.turism.signals