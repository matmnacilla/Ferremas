from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import F, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from .models import Producto, Empleado, Venta, Categoria, Carrito, CarritoItem
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
import time
from django.contrib.auth.decorators import login_required
import json

# Comentamos temporalmente la función es_admin y el decorador
# def es_admin(user):
#     return user.groups.filter(name='administradores').exists()

# def admin_required(view_func):
#     def wrapper(request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect('loginAdmin')
#         if not es_admin(request.user):
#             messages.error(request, 'No tienes permisos para acceder a esta sección.')
#             return redirect('index')
#         return view_func(request, *args, **kwargs)
#     return wrapper

# Create your views here.
def index(request):
    # Obtener productos destacados (activos, incluyendo ofertas y normales)
    productos_destacados = Producto.objects.filter(
        activo=True
    ).order_by('-fecha_actualizacion')[:6]  # Aumentamos a 6 para mostrar más productos
    
    # Si el usuario está autenticado, verificar su grupo
    if request.user.is_authenticated:
        # Verificar si el usuario pertenece a algún grupo específico
        if request.user.groups.filter(name='clientes').exists():
            return render(request, 'core/index.html', {
                'productos_destacados': productos_destacados
            })
        elif request.user.groups.filter(name='vendedores').exists():
            return redirect('panelVendedor')
        elif request.user.groups.filter(name='bodegueros').exists():
            return redirect('panelBodeguero')
        elif request.user.groups.filter(name='administradores').exists():
            return redirect('panelAdmin')
    
    # Si no está autenticado o no pertenece a ningún grupo, mostrar la página normal
    return render(request, 'core/index.html', {
        'productos_destacados': productos_destacados
    })

def logout_view(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='clientes').exists():
            logout(request)
            return redirect('index')
        elif request.user.groups.filter(name='vendedores').exists():
            logout(request)
            return redirect('loginTrabajador')
        elif request.user.groups.filter(name='bodegueros').exists():
            logout(request)
            return redirect('loginTrabajador')
        elif request.user.groups.filter(name='administradores').exists():
            logout(request)
            return redirect('loginAdmin')
        else:
            logout(request)
            return redirect('index')
    return redirect('index')


def registercliente(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password']
        password2 = request.POST['confirmPassword']

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('registrarse')
        elif len(password1) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return redirect('registrarse')
        elif len(username) < 3:
            messages.error(request, 'El nombre de usuario debe tener al menos 3 caracteres.')
            return redirect('registrarse')
        
        # Validación de email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'El correo electrónico no es válido.')
            return redirect('registrarse')

        # Verificaciones de existencia
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return redirect('registrarse')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está en uso.')
            return redirect('registrarse')

        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            cliente_group = Group.objects.get(name='clientes')
            user.groups.add(cliente_group)
            user.save()
            messages.success(request, 'Usuario creado correctamente')
            return redirect('index')
        except IntegrityError:
            messages.error(request, 'Error al crear el usuario. Por favor, intente nuevamente.')
            return redirect('registrarse')
        except Group.DoesNotExist:
            messages.error(request, 'Error en la configuración del sistema. Contacte al administrador.')
            return redirect('registrarse')

    return render(request, 'core/registrarse.html')

def login_view(request):
    return render(request, 'core/login.html')

def logincliente(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        # Primero intentamos obtener el usuario por email
        try:
            username = User.objects.get(email=email).username
            user = authenticate(request, username=username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            if user.groups.filter(name='clientes').exists():
                login(request, user)
                return redirect('index')
            elif user.groups.filter(name='vendedores').exists():
                messages.error(request, 'Los vendedores deben iniciar sesión en el panel de trabajadores.')
                return redirect('loginTrabajador')
            elif user.groups.filter(name='bodegueros').exists():
                messages.error(request, 'Los bodegueros deben iniciar sesión en el panel de trabajadores.')
                return redirect('loginTrabajador')
            elif user.groups.filter(name='administradores').exists():
                messages.error(request, 'Los administradores deben iniciar sesión en el panel de administración.')
                return redirect('loginAdmin')
            else:
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('index')
        else:
            messages.error(request, 'Credenciales de inicio de sesión incorrectas.')
            return redirect('login_view')

    return render(request, 'core/login.html')



def loginadmin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Agregamos prints para depuración
        print(f"Intentando login con usuario: {username}")
        
        try:
            # Verificamos si el usuario existe
            user = User.objects.filter(username=username).first()
            if user:
                print(f"Usuario encontrado: {user.username}")
                print(f"Grupos del usuario: {[g.name for g in user.groups.all()]}")
                
                # Intentamos autenticar
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    print("Autenticación exitosa")
                    if user.groups.filter(name='administradores').exists():
                        print("Usuario es administrador")
                        login(request, user)
                        print("Login realizado")
                        print(f"Usuario autenticado: {request.user.is_authenticated}")
                        # Intentamos redirigir de varias formas
                        from django.http import HttpResponseRedirect
                        response = HttpResponseRedirect('/panelAdmin/')
                        print("Redirección configurada")
                        return response
                    else:
                        print("Usuario no es administrador")
                        messages.error(request, 'No tienes permisos de administrador')
                else:
                    print("Autenticación fallida")
                    messages.error(request, 'Credenciales incorrectas')
            else:
                print("Usuario no encontrado")
                messages.error(request, 'Usuario no existe')
                
        except Exception as e:
            print(f"Error durante el login: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
        
        # Si llegamos aquí, hubo un error
        return render(request, 'core/loginAdmin.html')

    return render(request, 'core/loginAdmin.html')








def catalogo(request):
    # Obtener el parámetro de ofertas de la URL
    mostrar_ofertas = request.GET.get('ofertas') == 'true'
    
    # Base query para productos activos
    productos_query = Producto.objects.filter(activo=True)
    
    # Si se solicita ver solo ofertas, agregar el filtro
    if mostrar_ofertas:
        productos_query = productos_query.filter(precio_oferta__isnull=False)
    
    # Filtrar por categorías si se seleccionaron
    categorias_seleccionadas = request.GET.getlist('categoria')
    if categorias_seleccionadas:
        productos_query = productos_query.filter(categoria__nombre__in=categorias_seleccionadas)
    
    # Filtrar por precio mínimo
    precio_min = request.GET.get('precio_min')
    if precio_min and precio_min.isdigit():
        productos_query = productos_query.filter(
            Q(precio__gte=precio_min) | 
            Q(precio_oferta__gte=precio_min)
        )
    
    # Filtrar por precio máximo
    precio_max = request.GET.get('precio_max')
    if precio_max and precio_max.isdigit():
        productos_query = productos_query.filter(
            Q(precio__lte=precio_max) | 
            Q(precio_oferta__lte=precio_max)
        )
    
    # Ordenar por fecha de creación
    productos = productos_query.order_by('-fecha_creacion')
    
    # Obtener categorías activas
    categorias = Categoria.objects.filter(activa=True).order_by('nombre')
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'mostrar_ofertas': mostrar_ofertas
    }
    return render(request, 'core/catalogo.html', context)

@login_required
def carrito(request):
    try:
        # Obtener el carrito del usuario
        carrito = Carrito.objects.get(usuario=request.user)
        # Obtener los items del carrito con sus productos
        carrito_items = CarritoItem.objects.filter(carrito=carrito).select_related('producto')
        
        # Calcular el total del carrito
        total_carrito = sum(item.subtotal for item in carrito_items)
        
        context = {
            'carrito_items': carrito_items,
            'total_carrito': total_carrito
        }
    except Carrito.DoesNotExist:
        context = {
            'carrito_items': [],
            'total_carrito': 0
        }
    
    return render(request, 'core/carrito.html', context)

def detalleProducto(request, id):
    producto = get_object_or_404(Producto, id=id, activo=True)
    context = {
        'producto': producto
    }
    return render(request, 'core/detalleProducto.html', context)

def registrarse(request):
    return render(request, 'core/registrarse.html')


def loginTrabajador(request):
    return render(request, 'core/loginTrabajador.html')

def panelAdmin(request):
    try:
        # Estadísticas de productos
        total_productos = Producto.objects.count()
        productos_stock_bajo = Producto.objects.filter(stock__lte=F('stock_minimo')).count()
        productos_oferta = Producto.objects.filter(precio_oferta__isnull=False, precio_oferta__gt=F('precio')).count()
        productos_activos = Producto.objects.filter(activo=True).count()
        
        # Estadísticas de ventas
        total_ventas = Venta.objects.count()
        ventas_mes = Venta.objects.filter(
            fecha__year=timezone.now().year,
            fecha__month=timezone.now().month
        ).count()
        
        # Estadísticas de empleados
        empleados_activos = Empleado.objects.filter(activo=True).count()
        
        # Obtener listas para las tablas
        productos = Producto.objects.all().order_by('-fecha_creacion')
        empleados = Empleado.objects.select_related('usuario').all()
        categorias = Categoria.objects.filter(activa=True).order_by('nombre')

        context = {
            'total_productos': total_productos,
            'productos_stock_bajo': productos_stock_bajo,
            'productos_oferta': productos_oferta,
            'productos_activos': productos_activos,
            'total_ventas': total_ventas,
            'ventas_mes': ventas_mes,
            'empleados_activos': empleados_activos,
            'productos': productos,
            'empleados': empleados,
            'categorias': categorias,
            'seccion_activa': request.GET.get('seccion', 'dashboard')
        }
        
        return render(request, 'core/panelAdmin.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar el panel de administración: {str(e)}')
        return redirect('index')

def panelBodeguero(request):
    return render(request, 'core/panelBodeguero.html')

def panelVendedor(request):
    return render(request, 'core/panelVendedor.html')

def procesoCompra(request):
    return render(request, 'core/procesoCompra.html')

# Vistas para Productos
def lista_productos(request):
    productos = Producto.objects.all().order_by('-fecha_creacion')
    return render(request, 'core/panelAdmin.html', {
        'productos': productos,
        'seccion_activa': 'productos'
    })

def crear_categoria(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            if not nombre:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la categoría es requerido'
                }, status=400)
            
            # Verificar si ya existe una categoría con el mismo nombre
            if Categoria.objects.filter(nombre=nombre).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una categoría con ese nombre'
                }, status=400)
            
            categoria = Categoria.objects.create(
                nombre=nombre,
                descripcion=request.POST.get('descripcion', ''),
                imagen=request.FILES.get('imagen'),
                activa=True
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Categoría creada exitosamente',
                    'categoria': {
                        'id': categoria.id,
                        'nombre': categoria.nombre
                    }
                })
            else:
                messages.success(request, 'Categoría creada exitosamente')
                return redirect('panelAdmin')
                
        except Exception as e:
            error_msg = f'Error al crear la categoría: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                }, status=400)
            else:
                messages.error(request, error_msg)
                return redirect('panelAdmin')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)
    return redirect('panelAdmin')

def generar_password():
    """Genera una contraseña temporal fácil de recordar pero segura."""
    # Generar una palabra aleatoria de 4-6 letras
    palabras = ['ferre', 'mas', 'tienda', 'venta', 'bodega', 'admin', 'user', 'work']
    palabra = random.choice(palabras)
    
    # Agregar 2 números al final
    numeros = ''.join(random.choices(string.digits, k=2))
    
    # Agregar un carácter especial
    especiales = '!@#$%'
    especial = random.choice(especiales)
    
    # Combinar todo
    password = f"{palabra}{numeros}{especial}"
    return password

def enviar_credenciales_email(email, username, password):
    """Envía un correo con las credenciales al nuevo empleado."""
    subject = 'Bienvenido a Ferremas - Tus credenciales de acceso'
    message = f"""
    Bienvenido a Ferremas!
    
    Tus credenciales de acceso son:
    Usuario: {username}
    Contraseña temporal: {password}
    
    Por seguridad, deberás cambiar tu contraseña al iniciar sesión por primera vez.
    
    Puedes acceder al sistema en: http://127.0.0.1:8000/loginTrabajador/
    
    Saludos,
    Equipo Ferremas
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Error al enviar email: {str(e)}")
        return False

def crear_producto(request):
    if request.method == 'POST':
        try:
            # Validar datos
            if not request.POST.get('nombre'):
                raise ValueError('El nombre del producto es requerido')
            if not request.POST.get('precio') or float(request.POST.get('precio')) <= 0:
                raise ValueError('El precio debe ser mayor a 0')
            if not request.POST.get('stock') or int(request.POST.get('stock')) < 0:
                raise ValueError('El stock no puede ser negativo')
            if not request.POST.get('categoria'):
                raise ValueError('La categoría es requerida')

            # Obtener categoría
            try:
                categoria = Categoria.objects.get(nombre=request.POST['categoria'])
            except Categoria.DoesNotExist:
                raise ValueError('La categoría seleccionada no existe')

            # Validar imagen si se proporciona
            imagen = request.FILES.get('imagen')
            if imagen and not imagen.content_type.startswith('image/'):
                raise ValueError('El archivo debe ser una imagen')

            # Generar código único usando timestamp y número aleatorio
            timestamp = int(time.time())  # Segundos en lugar de milisegundos
            random_num = random.randint(100, 999)  # 3 dígitos en lugar de 4
            codigo = f"P{timestamp}{random_num}"  # Formato más corto
            
            # Verificar que el código no exista
            while Producto.objects.filter(codigo=codigo).exists():
                random_num = random.randint(100, 999)
                codigo = f"P{timestamp}{random_num}"

            producto = Producto.objects.create(
                nombre=request.POST['nombre'],
                categoria=categoria,
                codigo=codigo,
                precio=float(request.POST['precio']),
                stock=int(request.POST['stock']),
                stock_minimo=5,  # Valor por defecto
                descripcion=request.POST.get('descripcion', ''),
                imagen=imagen,
                activo=True
            )
            messages.success(request, 'Producto creado exitosamente')
            return redirect('panelAdmin')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
    return redirect('panelAdmin')

def crear_empleado(request):
    if request.method == 'POST':
        try:
            # Validar datos
            if not request.POST.get('nombre'):
                raise ValueError('El nombre del empleado es requerido')
            if not request.POST.get('email'):
                raise ValueError('El email es requerido')
            if not request.POST.get('telefono'):
                raise ValueError('El teléfono es requerido')
            if not request.POST.get('departamento'):
                raise ValueError('El departamento es requerido')
            if not request.POST.get('cargo'):
                raise ValueError('El cargo es requerido')

            # Validar email único
            email = request.POST['email']
            if User.objects.filter(email=email).exists():
                raise ValueError('El email ya está registrado')

            # Validar departamento
            departamento = request.POST['departamento']
            if departamento not in ['ventas', 'bodega']:
                raise ValueError('El departamento debe ser Ventas o Bodega')
            
            # Mapear departamento a grupo
            departamento_to_grupo = {
                'ventas': 'vendedores',
                'bodega': 'bodegueros'
            }
            grupo_nombre = departamento_to_grupo[departamento]
            
            try:
                grupo = Group.objects.get(name=grupo_nombre)
            except Group.DoesNotExist:
                raise ValueError(f'El departamento {departamento} no es válido')

            # Crear usuario
            username = email.split('@')[0]
            # Asegurar username único
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Generar contraseña temporal
            password = generar_password()
            
            # Crear usuario con contraseña temporal
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,  # Django hasheará la contraseña automáticamente
                first_name=request.POST['nombre'].split()[0],
                last_name=' '.join(request.POST['nombre'].split()[1:]),
                is_active=True
            )
            
            # Crear empleado
            empleado = Empleado.objects.create(
                usuario=user,
                departamento=departamento,
                cargo=request.POST['cargo'],
                telefono=request.POST['telefono'],
                activo=True,
                debe_cambiar_password=True  # Nuevo campo para forzar cambio de contraseña
            )
            
            # Asignar grupo
            user.groups.add(grupo)
            
            # Enviar credenciales por email
            if enviar_credenciales_email(email, username, password):
                messages.success(request, f'Empleado creado exitosamente. Las credenciales han sido enviadas al correo {email}')
            else:
                messages.warning(request, f'Empleado creado exitosamente. Usuario: {username}, Contraseña temporal: {password}. No se pudo enviar el correo electrónico.')
            
            return redirect('panelAdmin')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al crear el empleado: {str(e)}')
    return redirect('panelAdmin')

def obtener_empleado(request, id):
    try:
        empleado = get_object_or_404(Empleado, id=id)
        data = {
            'success': True,
            'empleado': {
                'id': empleado.id,
                'nombre': empleado.usuario.get_full_name(),
                'email': empleado.usuario.email,
                'departamento': empleado.departamento,
                'cargo': empleado.cargo,
                'telefono': empleado.telefono
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def editar_empleado(request, id):
    empleado = get_object_or_404(Empleado, id=id)
    if request.method == 'POST':
        try:
            # Validar datos
            if not request.POST.get('nombre'):
                raise ValueError('El nombre del empleado es requerido')
            if not request.POST.get('email'):
                raise ValueError('El email es requerido')
            if not request.POST.get('telefono'):
                raise ValueError('El teléfono es requerido')
            if not request.POST.get('departamento'):
                raise ValueError('El departamento es requerido')
            if not request.POST.get('cargo'):
                raise ValueError('El cargo es requerido')

            # Validar email único si cambió
            email = request.POST['email']
            if email != empleado.usuario.email and User.objects.filter(email=email).exists():
                raise ValueError('El email ya está registrado')

            # Validar departamento
            departamento = request.POST['departamento']
            if departamento not in ['ventas', 'bodega']:
                raise ValueError('El departamento debe ser Ventas o Bodega')
            
            # Mapear departamento a grupo
            departamento_to_grupo = {
                'ventas': 'vendedores',
                'bodega': 'bodegueros'
            }
            grupo_nombre = departamento_to_grupo[departamento]
            
            try:
                grupo_nuevo = Group.objects.get(name=grupo_nombre)
            except Group.DoesNotExist:
                raise ValueError(f'El departamento {departamento} no es válido')

            # Actualizar usuario
            empleado.usuario.first_name = request.POST['nombre'].split()[0]
            empleado.usuario.last_name = ' '.join(request.POST['nombre'].split()[1:])
            empleado.usuario.email = email
            
            # Actualizar empleado
            empleado.departamento = departamento
            empleado.cargo = request.POST['cargo']
            empleado.telefono = request.POST['telefono']
            
            # Actualizar grupo si cambió el departamento
            if empleado.departamento != departamento:
                grupo_anterior_nombre = departamento_to_grupo[empleado.departamento]
                grupo_anterior = Group.objects.get(name=grupo_anterior_nombre)
                empleado.usuario.groups.remove(grupo_anterior)
                empleado.usuario.groups.add(grupo_nuevo)
            
            empleado.usuario.save()
            empleado.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Empleado actualizado exitosamente'
                })
            else:
                messages.success(request, 'Empleado actualizado exitosamente')
                return redirect('panelAdmin')
        except ValueError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            else:
                messages.error(request, str(e))
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Error al actualizar el empleado: {str(e)}'
                }, status=400)
            else:
                messages.error(request, f'Error al actualizar el empleado: {str(e)}')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)
    
    return redirect('panelAdmin')

def eliminar_empleado(request, id):
    try:
        empleado = get_object_or_404(Empleado, id=id)
        nombre_empleado = empleado.usuario.get_full_name()
        usuario = empleado.usuario
        empleado.delete()
        usuario.delete()
        messages.success(request, f'Empleado "{nombre_empleado}" eliminado exitosamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar el empleado: {str(e)}')
    return redirect('panelAdmin')

# Vistas para Empleados
def lista_empleados(request):
    empleados = Empleado.objects.select_related('usuario').all()
    return render(request, 'core/panelAdmin.html', {
        'empleados': empleados,
        'seccion_activa': 'empleados'
    })

def obtener_producto(request, id):
    try:
        producto = get_object_or_404(Producto, id=id)
        data = {
            'success': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'categoria': producto.categoria.nombre,
                'precio': float(producto.precio),
                'precio_oferta': float(producto.precio_oferta) if producto.precio_oferta else None,
                'stock': producto.stock,
                'descripcion': producto.descripcion,
                'imagen': producto.imagen.url if producto.imagen else None
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        try:
            # Validar datos
            if not request.POST.get('nombre'):
                raise ValueError('El nombre del producto es requerido')
            if not request.POST.get('precio') or float(request.POST.get('precio')) <= 0:
                raise ValueError('El precio debe ser mayor a 0')
            if not request.POST.get('stock') or int(request.POST.get('stock')) < 0:
                raise ValueError('El stock no puede ser negativo')
            if not request.POST.get('categoria'):
                raise ValueError('La categoría es requerida')

            # Validar precio de oferta
            precio_oferta = request.POST.get('precio_oferta')
            if precio_oferta:
                precio_oferta = float(precio_oferta)
                if precio_oferta <= 0:
                    raise ValueError('El precio de oferta debe ser mayor a 0')
                if precio_oferta >= float(request.POST.get('precio')):
                    raise ValueError('El precio de oferta debe ser menor al precio normal')

            # Obtener categoría
            try:
                categoria = Categoria.objects.get(nombre=request.POST['categoria'])
            except Categoria.DoesNotExist:
                raise ValueError('La categoría seleccionada no existe')

            # Validar imagen si se proporciona
            imagen = request.FILES.get('imagen')
            if imagen:
                if not imagen.content_type.startswith('image/'):
                    raise ValueError('El archivo debe ser una imagen')
                producto.imagen = imagen

            producto.nombre = request.POST['nombre']
            producto.categoria = categoria
            producto.precio = float(request.POST['precio'])
            producto.precio_oferta = precio_oferta if precio_oferta else None
            producto.stock = int(request.POST['stock'])
            producto.descripcion = request.POST.get('descripcion', '')
            producto.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Producto actualizado exitosamente'
                })
            else:
                messages.success(request, 'Producto actualizado exitosamente')
                return redirect('panelAdmin')
        except ValueError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            else:
                messages.error(request, str(e))
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'Error al actualizar el producto: {str(e)}'
                }, status=400)
            else:
                messages.error(request, f'Error al actualizar el producto: {str(e)}')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)
    
    categorias = Categoria.objects.filter(activa=True).order_by('nombre')
    return render(request, 'core/editarProducto.html', {
        'producto': producto,
        'categorias': categorias
    })

def eliminar_producto(request, id):
    try:
        producto = get_object_or_404(Producto, id=id)
        nombre_producto = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar el producto: {str(e)}')
    return redirect('panelAdmin')

@login_required
def agregar_al_carrito(request, producto_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        producto = get_object_or_404(Producto, id=producto_id, activo=True)
        
        # Obtener la cantidad del body JSON
        data = json.loads(request.body)
        cantidad = int(data.get('cantidad', 1))
        
        # Validar cantidad
        if cantidad < 1:
            return JsonResponse({
                'success': False,
                'error': 'La cantidad debe ser mayor a 0'
            }, status=400)
        
        # Verificar stock
        if producto.stock < cantidad:
            return JsonResponse({
                'success': False,
                'error': 'No hay suficiente stock disponible'
            }, status=400)
        
        # Obtener o crear carrito del usuario
        carrito, created = Carrito.objects.get_or_create(usuario=request.user)
        
        # Obtener o crear item del carrito
        carrito_item, created = CarritoItem.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': cantidad}
        )
        
        # Si el item ya existe, actualizar cantidad
        if not created:
            # Verificar si hay suficiente stock con la nueva cantidad
            if carrito_item.cantidad + cantidad > producto.stock:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay suficiente stock disponible'
                }, status=400)
            carrito_item.cantidad += cantidad
            carrito_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto agregado al carrito exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al agregar el producto al carrito: {str(e)}'
        }, status=400)

@login_required
def actualizar_carrito(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el item del carrito
        item = CarritoItem.objects.get(id=item_id, carrito__usuario=request.user)
        
        # Obtener la nueva cantidad del body JSON
        data = json.loads(request.body)
        nueva_cantidad = int(data.get('cantidad', 1))
        
        # Validar cantidad
        if nueva_cantidad < 1:
            return JsonResponse({
                'success': False,
                'error': 'La cantidad debe ser mayor a 0'
            }, status=400)
        
        # Verificar stock
        if nueva_cantidad > item.producto.stock:
            return JsonResponse({
                'success': False,
                'error': 'No hay suficiente stock disponible'
            }, status=400)
        
        # Actualizar cantidad
        item.cantidad = nueva_cantidad
        item.save()
        
        # Calcular nuevos totales
        subtotal = item.producto.precio * item.cantidad
        total_carrito = CarritoItem.objects.filter(carrito=item.carrito).aggregate(
            total=Sum(F('producto__precio') * F('cantidad'))
        )['total'] or 0
        
        return JsonResponse({
            'success': True,
            'subtotal': subtotal,
            'total': total_carrito
        })
        
    except CarritoItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'El item no existe en el carrito'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar el carrito: {str(e)}'
        }, status=400)

@login_required
def eliminar_del_carrito(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener y eliminar el item del carrito
        item = CarritoItem.objects.get(id=item_id, carrito__usuario=request.user)
        carrito = item.carrito
        item.delete()
        
        # Calcular nuevo total
        total_carrito = CarritoItem.objects.filter(carrito=carrito).aggregate(
            total=Sum(F('producto__precio') * F('cantidad'))
        )['total'] or 0
        
        return JsonResponse({
            'success': True,
            'total': total_carrito
        })
        
    except CarritoItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'El item no existe en el carrito'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar el item del carrito: {str(e)}'
        }, status=400)

def obtener_productos_oferta(request):
    try:
        productos = Producto.objects.filter(
            precio_oferta__isnull=False,
            activo=True
        ).select_related('categoria').order_by('-fecha_actualizacion')
        
        data = {
            'success': True,
            'productos': [{
                'id': p.id,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'precio': float(p.precio),
                'precio_oferta': float(p.precio_oferta),
                'descuento': p.porcentaje_descuento(),
                'stock': p.stock,
                'imagen': p.imagen.url if p.imagen else None
            } for p in productos]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)






