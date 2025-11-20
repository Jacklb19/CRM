from django.apps import AppConfig


class SalesTeamConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sales_team'
    
    def ready(self):
        import sales_team.models  # Importar signals
