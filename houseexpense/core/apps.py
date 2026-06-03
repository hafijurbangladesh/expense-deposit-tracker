from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'houseexpense.core'
    verbose_name = 'Core'
    
    def ready(self):
        import houseexpense.core.signals  # Import signals when app is ready
