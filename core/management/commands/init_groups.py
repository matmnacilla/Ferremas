from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Inicializa los grupos de usuarios'

    def handle(self, *args, **kwargs):
        # Crear los grupos si no existen
        grupos = ['clientes', 'vendedores', 'bodegueros', 'administradores']
        
        for grupo in grupos:
            Group.objects.get_or_create(name=grupo)
            self.stdout.write(self.style.SUCCESS(f'Grupo "{grupo}" creado o ya existente'))
