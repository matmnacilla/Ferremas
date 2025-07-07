from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from core.models import Empleado

class Command(BaseCommand):
    help = 'Diagnostica problemas de autenticación y configuración'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== DIAGNÓSTICO DE AUTENTICACIÓN ===\n'))
        
        # 1. Verificar grupos
        self.stdout.write('1. Verificando grupos...')
        required_groups = ['clientes', 'vendedores', 'bodegueros', 'administradores']
        existing_groups = Group.objects.all()
        
        for group_name in required_groups:
            if existing_groups.filter(name=group_name).exists():
                self.stdout.write(f'  ✓ Grupo "{group_name}" existe')
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Grupo "{group_name}" NO existe')
                )
        
        # 2. Verificar usuarios
        self.stdout.write('\n2. Verificando usuarios...')
        users = User.objects.all()
        self.stdout.write(f'  Total de usuarios: {users.count()}')
        
        users_without_groups = []
        users_by_group = {}
        
        for user in users:
            if not user.groups.exists():
                users_without_groups.append(user)
            else:
                for group in user.groups.all():
                    if group.name not in users_by_group:
                        users_by_group[group.name] = []
                    users_by_group[group.name].append(user)
        
        if users_without_groups:
            self.stdout.write(
                self.style.WARNING(f'  Usuarios sin grupo: {len(users_without_groups)}')
            )
            for user in users_without_groups:
                self.stdout.write(f'    - {user.username} ({user.email})')
        else:
            self.stdout.write('  ✓ Todos los usuarios tienen grupos asignados')
        
        # Mostrar usuarios por grupo
        for group_name in required_groups:
            if group_name in users_by_group:
                self.stdout.write(f'  Usuarios en "{group_name}": {len(users_by_group[group_name])}')
                for user in users_by_group[group_name]:
                    self.stdout.write(f'    - {user.username}')
        
        # 3. Verificar empleados
        self.stdout.write('\n3. Verificando empleados...')
        empleados = Empleado.objects.all()
        self.stdout.write(f'  Total de empleados: {empleados.count()}')
        
        for empleado in empleados:
            if empleado.usuario:
                self.stdout.write(f'  - {empleado.usuario.username} ({empleado.cargo})')
                if empleado.usuario.groups.exists():
                    groups = [g.name for g in empleado.usuario.groups.all()]
                    self.stdout.write(f'    Grupos: {", ".join(groups)}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠️ Sin grupos asignados')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  - Empleado sin usuario asociado (ID: {empleado.id})')
                )
        
        # 4. Verificar superusuarios
        self.stdout.write('\n4. Verificando superusuarios...')
        superusers = User.objects.filter(is_superuser=True)
        self.stdout.write(f'  Total de superusuarios: {superusers.count()}')
        
        for superuser in superusers:
            self.stdout.write(f'  - {superuser.username} ({superuser.email})')
            if superuser.groups.exists():
                groups = [g.name for g in superuser.groups.all()]
                self.stdout.write(f'    Grupos: {", ".join(groups)}')
            else:
                self.stdout.write('    Sin grupos asignados')
        
        # 5. Recomendaciones
        self.stdout.write('\n5. Recomendaciones:')
        
        if users_without_groups:
            self.stdout.write(
                self.style.WARNING('  - Ejecuta: python manage.py check_user_groups --fix')
            )
        
        missing_groups = [g for g in required_groups if not existing_groups.filter(name=g).exists()]
        if missing_groups:
            self.stdout.write(
                self.style.ERROR('  - Crea los grupos faltantes:')
            )
            for group in missing_groups:
                self.stdout.write(f'    python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.create(name=\'{group}\')"')
        
        if superusers.count() == 0:
            self.stdout.write(
                self.style.WARNING('  - Crea un superusuario: python manage.py createsuperuser')
            )
        
        self.stdout.write('\n=== FIN DEL DIAGNÓSTICO ===') 