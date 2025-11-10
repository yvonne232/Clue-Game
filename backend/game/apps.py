from django.apps import AppConfig


class GameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "game"

    def ready(self):
        """Import and register signals when Django starts"""
        import game.signals  # noqa
