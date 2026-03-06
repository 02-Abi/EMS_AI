# ml_engine/apps.py
from django.apps import AppConfig

class MlEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_engine'

    def ready(self):
        import ml_engine.signals