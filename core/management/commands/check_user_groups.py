from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib import messages

class Command(BaseCommand):
    help = 'Verifica y corrige usuarios sin grupos asignados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Asigna automáticamente el grupo "clientes" a usuarios sin grupo',
        )

    def handle(self, *args, **options):
        # Obtener todos los usuarios
        users = User.objects.all()
        users_without_groups = []
        
        for user in users:
            if not user.groups.exists():
                users_without_groups.append(user)
        
        if users_without_groups:
            self.stdout.write(
                self.style.WARNING(
                    f'Se encontraron {len(users_without_groups)} usuarios sin grupos asignados:'
                )
            )
            
            for user in users_without_groups:
                self.stdout.write(f'  - {user.username} ({user.email})')
            
            if options['fix']:
                try:
                    # Intentar obtener el grupo "clientes"
                    clientes_group = Group.objects.get(name='clientes')
                    
                    for user in users_without_groups:
                        user.groups.add(clientes_group)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Grupo "clientes" asignado a {user.username}'
                            )
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Se asignó el grupo "clientes" a {len(users_without_groups)} usuarios'
                        )
                    )
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            'El grupo "clientes" no existe. Crea los grupos necesarios primero.'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'Usa --fix para asignar automáticamente el grupo "clientes" a estos usuarios'
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('Todos los usuarios tienen grupos asignados correctamente')
            ) 