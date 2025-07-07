from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import F, Sum, Q, Count, Max
from django.utils import timezone
from django.http import JsonResponse
from .models import Producto, Empleado, Venta, Categoria, Carrito, CarritoItem, DetalleVenta, Notificacion
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
import time
from django.contrib.auth.decorators import login_required
import json
import paypalrestsdk
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
import logging
from django.contrib.auth.decorators import user_passes_test
import requests
from datetime import datetime
from rest_framework import viewsets, permissions, filters
from .serializers import VentaSerializer
from .models import Venta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
def index(request):
    # Obtener productos destacados (activos, incluyendo ofertas y normales)
    productos_destacados = Producto.objects.filter(
        activo=True
    ).order_by('-fecha_actualizacion')[:6]
    
    # Obtener productos en oferta para el carrusel
    productos_oferta = Producto.objects.filter(
        activo=True,
        precio_oferta__isnull=False
    ).order_by('-fecha_actualizacion')[:3]  # Máximo 3 productos en oferta para el carrusel
    
    # Obtener una categoría al azar para el carrusel
    from django.db.models import Count
    import random
    
    # Obtener todas las categorías activas que tengan productos
    categorias_con_productos = Categoria.objects.filter(
        activa=True
    ).annotate(
        num_productos=Count('producto')
    ).filter(
        num_productos__gt=0
    )
    
    # Si hay categorías con productos, elegir una al azar
    if categorias_con_productos.exists():
        categoria_herramientas = random.choice(list(categorias_con_productos))
    else:
        # Si no hay categorías con productos, tomar cualquier categoría activa
        categorias_activas = Categoria.objects.filter(activa=True)
        if categorias_activas.exists():
            categoria_herramientas = random.choice(list(categorias_activas))
        else:
            categoria_herramientas = None
    
    # Si el usuario está autenticado, verificar su grupo
    if request.user.is_authenticated:
        # Verificar si el usuario pertenece a algún grupo específico
        if request.user.groups.filter(name='clientes').exists():
            return render(request, 'core/index.html', {
                'productos_destacados': productos_destacados,
                'productos_oferta': productos_oferta,
                'categoria_herramientas': categoria_herramientas
            })
        elif request.user.groups.filter(name='vendedores').exists():
            return redirect('panelVendedor')
        elif request.user.groups.filter(name='bodegueros').exists():
            return redirect('panelBodeguero')
        elif request.user.groups.filter(name='administradores').exists():
            return redirect('panelAdmin')
        else:
            # Usuario autenticado pero sin grupo asignado
            print(f"Usuario {request.user.username} no tiene grupo asignado")
            messages.warning(request, 'Tu cuenta no tiene permisos asignados. Contacta al administrador.')
            logout(request)
            return render(request, 'core/index.html', {
                'productos_destacados': productos_destacados,
                'productos_oferta': productos_oferta,
                'categoria_herramientas': categoria_herramientas
            })
    
    # Si no está autenticado, mostrar la página normal
    return render(request, 'core/index.html', {
        'productos_destacados': productos_destacados,
        'productos_oferta': productos_oferta,
        'categoria_herramientas': categoria_herramientas
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
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        print(f"=== LOGIN CLIENTE ===")
        print(f"Email: {email}")
        
        # Primero intentamos obtener el usuario por email
        try:
            username = User.objects.get(email=email).username
            print(f"Username encontrado: {username}")
            user = authenticate(request, username=username, password=password)
            print(f"Usuario autenticado: {user is not None}")
        except User.DoesNotExist:
            print("Usuario no encontrado por email")
            user = None
        
        if user is not None:
            print(f"Grupos del usuario: {[g.name for g in user.groups.all()]}")
            
            if user.groups.filter(name='clientes').exists():
                print("Usuario es cliente - haciendo login y redirigiendo a index")
                login(request, user)
                from django.contrib import messages
                list(messages.get_messages(request))  # Limpia mensajes viejos
                return redirect('index')
            elif user.groups.filter(name='vendedores').exists():
                print("Usuario es vendedor - redirigiendo a loginTrabajador")
                messages.error(request, 'Los vendedores deben iniciar sesión en el panel de trabajadores.')
                return redirect('loginTrabajador')
            elif user.groups.filter(name='bodegueros').exists():
                print("Usuario es bodeguero - redirigiendo a loginTrabajador")
                messages.error(request, 'Los bodegueros deben iniciar sesión en el panel de trabajadores.')
                return redirect('loginTrabajador')
            elif user.groups.filter(name='administradores').exists():
                print("Usuario es administrador - redirigiendo a loginAdmin")
                messages.error(request, 'Los administradores deben iniciar sesión en el panel de administración.')
                return redirect('loginAdmin')
            else:
                print("Usuario no tiene grupo asignado")
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('index')
        else:
            print("Credenciales incorrectas")
            messages.error(request, 'Credenciales de inicio de sesión incorrectas.')
            return redirect('login')

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
                        # Usar redirect con el nombre de la URL
                        return redirect('panelAdmin')
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
    print("\n=== VISTA CARRITO ===")
    print(f"Usuario: {request.user.username}")
    print(f"Autenticado: {request.user.is_authenticated}")
    
    try:
        # Obtener el carrito del usuario
        carrito = Carrito.objects.get(usuario=request.user)
        print(f"Carrito encontrado: {carrito}")
        
        # Obtener los items del carrito con sus productos
        carrito_items = CarritoItem.objects.filter(carrito=carrito).select_related('producto')
        print(f"Items en carrito: {carrito_items.count()}")
        
        # Calcular el total del carrito
        total_carrito = sum(item.subtotal for item in carrito_items)
        print(f"Total carrito: ${total_carrito}")
        
        context = {
            'carrito_items': carrito_items,
            'total_carrito': total_carrito
        }
    except Carrito.DoesNotExist:
        print("No se encontró carrito para el usuario")
        context = {
            'carrito_items': [],
            'total_carrito': 0
        }
    except Exception as e:
        print(f"Error en vista carrito: {str(e)}")
        context = {
            'carrito_items': [],
            'total_carrito': 0
        }
    
    print("Contexto:", context)
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
    from django.contrib.auth import authenticate, login
    from django.contrib import messages
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.groups.filter(name='vendedores').exists():
                login(request, user)
                return redirect('panelVendedor')
            elif user.groups.filter(name='bodegueros').exists():
                login(request, user)
                return redirect('panelBodeguero')
            else:
                messages.error(request, 'No tienes permisos de trabajador (vendedor o bodeguero).')
        else:
            messages.error(request, 'Credenciales incorrectas.')
    return render(request, 'core/loginTrabajador.html')

@login_required
def panelAdmin(request):
    # Verificar que el usuario sea administrador
    if not request.user.groups.filter(name='administradores').exists():
        messages.error(request, 'No tienes permisos de administrador')
        return redirect('index')
    
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
        
        # Obtener ventas/pedidos para la sección de pedidos
        ventas = Venta.objects.select_related(
            'cliente', 
            'aceptada_por'
        ).prefetch_related(
            'detalles__producto',
            'detalles__preparado_por'
        ).order_by('-fecha')
        
        # Preparar datos de ventas para el template
        ventas_data = []
        for venta in ventas:
            # Calcular estadísticas de preparación
            total_productos = venta.detalles.count()
            productos_preparados = venta.detalles.filter(preparado=True).count()
            porcentaje_preparado = (productos_preparados / total_productos * 100) if total_productos > 0 else 0
            
            # Calcular tiempo en estado actual
            tiempo_en_estado = timezone.now() - venta.ultima_actualizacion
            horas_en_estado = tiempo_en_estado.total_seconds() / 3600
            
            # Obtener información del bodeguero (del primer detalle preparado)
            bodeguero_info = None
            fecha_preparacion = None
            if productos_preparados > 0:
                primer_detalle_preparado = venta.detalles.filter(preparado=True).first()
                if primer_detalle_preparado and primer_detalle_preparado.preparado_por:
                    bodeguero_info = primer_detalle_preparado.preparado_por.get_full_name()
                    fecha_preparacion = primer_detalle_preparado.fecha_preparacion.strftime('%d/%m/%Y %H:%M') if primer_detalle_preparado.fecha_preparacion else None
            
            ventas_data.append({
                'id': venta.id,
                'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
                'cliente': venta.cliente.get_full_name() or venta.cliente.username,
                'total': venta.total,
                'estado': venta.estado,
                'telefono': venta.telefono_contacto,
                'direccion': venta.direccion_entrega,
                'ciudad': venta.ciudad,
                'prioridad': venta.prioridad,
                'horas_en_estado': round(horas_en_estado, 1),
                'aceptada_por': venta.aceptada_por.get_full_name() if venta.aceptada_por else None,
                'fecha_aceptacion': venta.fecha_aceptacion.strftime('%d/%m/%Y %H:%M') if venta.fecha_aceptacion else None,
                'preparado_por': bodeguero_info,
                'fecha_preparacion': fecha_preparacion,
                'estadisticas_preparacion': {
                    'total_productos': total_productos,
                    'productos_preparados': productos_preparados,
                    'porcentaje_preparado': round(porcentaje_preparado, 1)
                }
            })

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
            'ventas': ventas_data,
            'seccion_activa': request.GET.get('seccion', 'dashboard')
        }
        return render(request, 'core/panelAdmin.html', context)
    except Exception as e:
        print(f"Error en panelAdmin: {str(e)}")
        messages.error(request, f'Error al cargar el panel de administración: {str(e)}')
        # En lugar de redirigir a index, renderizar el template con error
        return render(request, 'core/panelAdmin.html', {
            'error': str(e),
            'total_productos': 0,
            'productos_stock_bajo': 0,
            'productos_oferta': 0,
            'productos_activos': 0,
            'total_ventas': 0,
            'ventas_mes': 0,
            'empleados_activos': 0,
            'productos': [],
            'empleados': [],
            'categorias': [],
            'ventas': [],
            'seccion_activa': 'dashboard'
        })

def panelBodeguero(request):
    """Vista principal del panel de bodeguero."""
    try:
        # Obtener ventas pendientes (confirmadas y enviadas)
        ventas = Venta.objects.filter(
            estado__in=['confirmada', 'preparada']
        ).select_related(
            'cliente',
            'actualizado_por'
        ).prefetch_related(
            'detalles__producto',
            'detalles__producto__categoria'
        ).order_by('-prioridad', '-fecha')

        # Preparar los datos para el template
        ventas_data = []
        for venta in ventas:
            # Calcular estadísticas de preparación
            total_productos = venta.detalles.count()
            productos_preparados = venta.detalles.filter(preparado=True).count()
            porcentaje_preparado = (productos_preparados / total_productos * 100) if total_productos > 0 else 0

            # Calcular tiempo en estado actual
            tiempo_en_estado = timezone.now() - venta.ultima_actualizacion
            horas_en_estado = tiempo_en_estado.total_seconds() / 3600

            ventas_data.append({
                'id': venta.id,
                'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
                'cliente': venta.cliente.get_full_name() or venta.cliente.username,
                'total': venta.total,
                'estado': venta.estado,
                'telefono': venta.telefono_contacto,
                'direccion': venta.direccion_entrega,
                'ciudad': venta.ciudad,
                'prioridad': venta.prioridad,
                'horas_en_estado': round(horas_en_estado, 1),
                'estadisticas_preparacion': {
                    'total_productos': total_productos,
                    'productos_preparados': productos_preparados,
                    'porcentaje_preparado': round(porcentaje_preparado, 1)
                }
            })

        # Agregar productos activos al contexto
        productos = Producto.objects.filter(activo=True).select_related('categoria')

        context = {
            'ventas': ventas_data,
            'productos': productos
        }
        return render(request, 'core/panelBodeguero.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar el panel de bodeguero: {str(e)}')
        return redirect('index')

@login_required
def panelVendedor(request):
    from core.models import Venta, Producto, Categoria, DetalleVenta
    from django.contrib.auth.models import User
    from django.db.models import Q
    
    # Navegación de secciones
    seccion = request.GET.get('seccion', 'dashboard')
    # Filtros de búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    ventas_query = Venta.objects.select_related('cliente').prefetch_related('detalles__producto').filter(estado='pendiente')
    if busqueda:
        ventas_query = ventas_query.filter(
            Q(cliente__username__icontains=busqueda) |
            Q(cliente__first_name__icontains=busqueda) |
            Q(cliente__last_name__icontains=busqueda) |
            Q(direccion_entrega__icontains=busqueda) |
            Q(ciudad__icontains=busqueda) |
            Q(detalles__producto__nombre__icontains=busqueda) |
            Q(estado__icontains=busqueda)
        ).distinct()
    ventas_query = ventas_query.order_by('-fecha')

    conteos = {
        'pendientes': Venta.objects.filter(estado='pendiente').count(),
        'canceladas': Venta.objects.filter(estado='cancelada').count(),
        'confirmadas': Venta.objects.filter(estado='confirmada').count(),
        'enviadas': Venta.objects.filter(estado='enviada').count(),
    }
    productos = Producto.objects.filter(activo=True)
    categorias = Categoria.objects.all()

    return render(request, 'core/panelVendedor.html', {
        'ventas': ventas_query,
        'conteos': conteos,
        'productos': productos,
        'categorias': categorias,
        'busqueda': busqueda,
        'seccion': seccion
    })

@login_required
def procesoCompra(request):
    print("\n=== VISTA PROCESO COMPRA ===")
    print(f"Usuario: {request.user.username}")
    print(f"PAYPAL_CLIENT_ID configurado: {'Sí' if settings.PAYPAL_CLIENT_ID else 'No'}")
    print(f"PAYPAL_MODE: {settings.PAYPAL_MODE}")
    
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        carrito_items = CarritoItem.objects.filter(carrito=carrito).select_related('producto')
        total_carrito = sum(item.subtotal for item in carrito_items)
        
        if not carrito_items.exists():
            messages.warning(request, 'Tu carrito está vacío')
            return redirect('carrito')
            
        context = {
            'carrito': carrito_items,
            'total': total_carrito,
            'PAYPAL_CLIENT_ID': settings.PAYPAL_CLIENT_ID,
            'PAYPAL_MINIMUM_AMOUNT': settings.PAYPAL_MINIMUM_AMOUNT,
            'PAYPAL_CURRENCY': getattr(settings, 'PAYPAL_CURRENCY', 'USD'),
        }
        print(f"Total carrito: ${total_carrito}")
        print(f"Total en USD: ${total_carrito * 0.001:.2f}")
        
    except Carrito.DoesNotExist:
        messages.warning(request, 'No tienes un carrito activo')
        return redirect('carrito')
    except Exception as e:
        print(f"Error en procesoCompra: {str(e)}")
        messages.error(request, 'Error al procesar tu compra')
        return redirect('carrito')
        
    return render(request, 'core/procesoCompra.html', context)

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

            # Generar código único más corto
            timestamp = int(time.time()) % 1000000  # Usar solo los últimos 6 dígitos
            random_num = random.randint(100, 999)  # 3 dígitos
            codigo = f"P{timestamp}{random_num}"  # Formato: P123456789 (máximo 10 caracteres)
            
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
        
        # Calcular totales actualizados del carrito
        total_items = sum(item.cantidad for item in CarritoItem.objects.filter(carrito=carrito))
        total_carrito = sum(item.subtotal for item in CarritoItem.objects.filter(carrito=carrito))
        
        return JsonResponse({
            'success': True,
            'message': 'Producto agregado al carrito exitosamente',
            'total_items': total_items,
            'total_carrito': total_carrito
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
        print("\n=== ACTUALIZAR CARRITO ===")
        # Obtener el item del carrito
        item = CarritoItem.objects.get(id=item_id, carrito__usuario=request.user)
        print(f"Producto: {item.producto.nombre}")
        print(f"Precio normal: ${item.producto.precio}")
        print(f"Precio oferta: ${item.producto.precio_oferta if item.producto.precio_oferta else 'No tiene'}")
        print(f"Precio actual: ${item.producto.precio_actual()}")
        print(f"Cantidad actual: {item.cantidad}")
        
        # Obtener la nueva cantidad del body JSON
        data = json.loads(request.body)
        nueva_cantidad = int(data.get('cantidad', 1))
        print(f"Nueva cantidad solicitada: {nueva_cantidad}")
        
        # Validar cantidad
        if nueva_cantidad < 0:
            print("Error: cantidad menor a 0")
            return JsonResponse({
                'success': False,
                'error': 'La cantidad debe ser mayor o igual a 0'
            }, status=400)
        
        # Si la cantidad es 0, eliminar el item del carrito
        if nueva_cantidad == 0:
            print(f"Eliminando item {item_id} del carrito (cantidad = 0)")
            item.delete()
            
            # Calcular nuevo total
            total_carrito = sum(item.subtotal for item in CarritoItem.objects.filter(carrito=item.carrito))
            print(f"Nuevo total del carrito: ${total_carrito}")
            
            return JsonResponse({
                'success': True,
                'eliminado': True,
                'total': total_carrito,
                'message': 'Producto eliminado del carrito'
            })
        
        # Verificar stock
        if nueva_cantidad > item.producto.stock:
            print(f"Error: stock insuficiente. Stock disponible: {item.producto.stock}")
            return JsonResponse({
                'success': False,
                'error': 'No hay suficiente stock disponible'
            }, status=400)
        
        # Actualizar cantidad
        item.cantidad = nueva_cantidad
        item.save()
        print(f"Cantidad actualizada a: {item.cantidad}")
        
        # Calcular nuevos totales usando precio_actual
        subtotal = item.producto.precio_actual() * item.cantidad
        total_carrito = sum(item.subtotal for item in CarritoItem.objects.filter(carrito=item.carrito))
        print(f"Nuevo subtotal: ${subtotal}")
        print(f"Nuevo total carrito: ${total_carrito}")
        
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
    print(f"\n=== ELIMINAR DEL CARRITO ===")
    print(f"Usuario: {request.user.username}")
    print(f"Item ID: {item_id}")
    print(f"Método: {request.method}")
    
    if request.method != 'POST':
        print("Error: Método no permitido")
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener y eliminar el item del carrito
        print(f"Buscando item {item_id} para usuario {request.user.username}")
        item = CarritoItem.objects.get(id=item_id, carrito__usuario=request.user)
        print(f"Item encontrado: {item}")
        
        carrito = item.carrito
        print(f"Carrito: {carrito}")
        
        # Guardar información antes de eliminar
        item_id_deleted = item.id
        producto_nombre = item.producto.nombre
        
        item.delete()
        print(f"Item {item_id_deleted} eliminado exitosamente")
        
        # Calcular nuevo total usando el método subtotal
        total_carrito = sum(item.subtotal for item in CarritoItem.objects.filter(carrito=carrito))
        print(f"Nuevo total del carrito: ${total_carrito}")
        
        return JsonResponse({
            'success': True,
            'total': total_carrito,
            'message': f'Producto "{producto_nombre}" eliminado correctamente'
        })
        
    except CarritoItem.DoesNotExist:
        print(f"Error: Item {item_id} no existe para el usuario {request.user.username}")
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

def configurar_paypal():
    """Configura el SDK de PayPal con las credenciales de la aplicación."""
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,  # sandbox o live
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET
    })

def convertir_a_usd(monto_clp):
    """Convierte un monto en CLP a USD usando una tasa de cambio fija para sandbox."""
    # Tasa de cambio fija para pruebas (1 USD = 1000 CLP)
    TASA_CAMBIO = 1000
    return round(monto_clp / TASA_CAMBIO, 2)

@login_required
def ejecutar_pago_paypal(request):
    print("\n=== INICIO EJECUTAR PAGO PAYPAL ===")
    print(f"Usuario: {request.user.username}")
    print(f"Método de la petición: {request.method}")
    print(f"GET params: {request.GET}")
    print(f"Session data: {dict(request.session)}")

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        # Obtener datos del body
        data = json.loads(request.body)
        payer_id = data.get('payer_id')
        order_id = data.get('order_id')
        status = data.get('status')

        print(f"PayerID recibido en body: {payer_id}")
        print(f"Order ID recibido en body: {order_id}")
        print(f"Status recibido en body: {status}")

        # Validar que tenemos el order_id en la sesión
        session_order_id = request.session.get('paypal_payment_id')
        if not session_order_id or session_order_id != order_id:
            print(f"Error: Order ID en sesión ({session_order_id}) no coincide con el recibido ({order_id})")
            return JsonResponse({
                'success': False,
                'error': 'ID de orden inválido o expirado'
            }, status=400)

        # Verificar si la orden ya existe en la base de datos
        if Venta.objects.filter(paypal_payment_id=order_id).exists():
            print(f"Error: La orden {order_id} ya fue procesada anteriormente")
            return JsonResponse({
                'success': False,
                'error': 'Esta orden ya fue procesada anteriormente'
            }, status=400)

        # Validar que tenemos el total en la sesión
        total_clp = request.session.get('paypal_total_clp')
        if not total_clp:
            print("Error: No se encontró el total en la sesión")
            return JsonResponse({
                'success': False,
                'error': 'Error en la sesión: total no encontrado'
            }, status=400)

        # Validar información de entrega
        info_entrega = request.session.get('info_entrega', {})
        campos_requeridos = ['direccion', 'ciudad', 'telefono']
        campos_faltantes = [campo for campo in campos_requeridos if not info_entrega.get(campo)]
        
        if campos_faltantes:
            print(f"Error: Campos de entrega faltantes: {campos_faltantes}")
            return JsonResponse({
                'success': False,
                'error': f'Por favor, completa los siguientes campos: {", ".join(campos_faltantes)}'
            }, status=400)

        print("Configurando PayPal...")
        # Configurar PayPal usando la API directamente
        import requests
        from django.conf import settings

        # Obtener token de acceso
        auth_url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        auth_data = {
            "grant_type": "client_credentials"
        }
        auth_headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
        
        auth_response = requests.post(auth_url, data=auth_data, headers=auth_headers, auth=auth)
        if not auth_response.ok:
            print(f"Error al obtener token: {auth_response.text}")
            return JsonResponse({
                'success': False,
                'error': 'Error al autenticar con PayPal'
            }, status=500)
        
        access_token = auth_response.json()['access_token']

        # Primero verificar el estado de la orden
        check_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}"
        check_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        check_response = requests.get(check_url, headers=check_headers)
        if not check_response.ok:
            print(f"Error al verificar orden: {check_response.text}")
            return JsonResponse({
                'success': False,
                'error': 'Error al verificar el estado de la orden'
            }, status=500)

        order_data = check_response.json()
        order_status = order_data.get('status')
        
        # Si la orden ya está en nuestra base de datos, no permitir reprocesarla
        if Venta.objects.filter(paypal_payment_id=order_id).exists():
            print(f"Error: La orden {order_id} ya existe en nuestra base de datos")
            return JsonResponse({
                'success': False,
                'error': 'Esta orden ya fue procesada anteriormente'
            }, status=400)

        # Si la orden está completada en PayPal pero no en nuestra base de datos,
        # intentamos recuperar la información y crear la venta
        if order_status == 'COMPLETED':
            print(f"La orden {order_id} está completada en PayPal pero no en nuestra base de datos")
            print("Intentando recuperar la información de la orden...")
            
            # Verificar que tenemos toda la información necesaria
            if not all([
                request.session.get('paypal_total_clp'),
                request.session.get('info_entrega'),
                request.session.get('paypal_items')
            ]):
                print("Error: No hay suficiente información en la sesión para recuperar la orden")
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede recuperar la información de la orden. Por favor, intenta una nueva compra.'
                }, status=400)

            # Intentar crear la venta con la información disponible
            try:
                print("Creando venta con información recuperada...")
                venta = Venta.objects.create(
                    cliente=request.user,
                    total=request.session.get('paypal_total_clp'),
                    estado='pendiente',
                    direccion_entrega=info_entrega['direccion'],
                    ciudad=info_entrega['ciudad'],
                    telefono_contacto=info_entrega['telefono'],
                    notas=info_entrega.get('notas', ''),
                    metodo_pago='paypal',
                    paypal_payment_id=order_id,
                    paypal_payer_id=payer_id,
                    paypal_payment_status=status
                )

                # Crear los items de la venta
                carrito = Carrito.objects.get(usuario=request.user)
                items = carrito.items.all()
                
                for item in items:
                    try:
                        # Calcular precios antes de crear el detalle
                        precio_unitario = float(item.producto.precio_actual())
                        cantidad = int(item.cantidad)
                        subtotal = precio_unitario * cantidad
                        
                        print(f"Procesando item: {item.producto.nombre}")
                        print(f"Precio unitario: ${precio_unitario}")
                        print(f"Cantidad: {cantidad}")
                        print(f"Subtotal: ${subtotal}")
                        
                        # Crear el detalle de venta
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=item.producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            subtotal=subtotal
                        )
                        
                        # Actualizar stock
                        producto = item.producto
                        producto.stock -= cantidad
                        producto.save()
                        
                    except Exception as e:
                        print(f"Error al procesar item {item.producto.nombre}: {str(e)}")
                        # Si hay un error, intentamos hacer rollback de la venta
                        venta.delete()
                        raise Exception(f"Error al procesar el producto {item.producto.nombre}: {str(e)}")

                # Limpiar el carrito y la sesión
                carrito.items.all().delete()
                request.session.pop('paypal_payment_id', None)
                request.session.pop('paypal_total_clp', None)
                request.session.pop('paypal_items', None)
                request.session.pop('info_entrega', None)

                print(f"Venta creada exitosamente: {venta.id}")
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('confirmacion_compra')  # URL directa en lugar de usar reverse
                })
                
            except Exception as e:
                print(f"Error al crear la venta: {str(e)}")
                # Intentar limpiar la sesión en caso de error
                request.session.pop('paypal_payment_id', None)
                request.session.pop('paypal_total_clp', None)
                request.session.pop('paypal_items', None)
                request.session.pop('info_entrega', None)
                return JsonResponse({
                    'success': False,
                    'error': 'No se pudo procesar la orden. Por favor, intenta una nueva compra.'
                }, status=500)

        # Si la orden no está completada, proceder con la captura normal
        capture_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
        capture_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        capture_response = requests.post(capture_url, headers=capture_headers)
        if not capture_response.ok:
            error_data = capture_response.json()
            if error_data.get('name') == 'ORDER_ALREADY_CAPTURED':
                print(f"La orden {order_id} ya fue capturada")
                # Si la orden ya fue capturada pero no está en nuestra base de datos,
                # intentamos crear la venta de todos modos
                if not Venta.objects.filter(paypal_payment_id=order_id).exists():
                    print("Intentando crear la venta a pesar de que la orden ya fue capturada")
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Esta orden ya fue procesada anteriormente'
                    }, status=400)
            else:
                print(f"Error al capturar orden: {capture_response.text}")
                return JsonResponse({
                    'success': False,
                    'error': 'Error al procesar el pago con PayPal'
                }, status=500)

        capture_data = capture_response.json()
        print(f"Orden capturada: {capture_data}")

        # Verificar que la captura fue exitosa
        if capture_data.get('status') != 'COMPLETED':
            print(f"Error: Estado de la orden no es COMPLETED: {capture_data.get('status')}")
            return JsonResponse({
                'success': False,
                'error': 'El pago no se completó correctamente'
            }, status=400)

        print("Obteniendo carrito...")
        carrito = Carrito.objects.get(usuario=request.user)
        items = carrito.items.all()
        print(f"Items en carrito: {items.count()}")

        # Validar stock
        for item in items:
            print(f"Validando stock para {item.producto.nombre}:")
            print(f"Stock disponible: {item.producto.stock}")
            print(f"Cantidad solicitada: {item.cantidad}")
            if item.producto.stock < item.cantidad:
                print(f"Error: Stock insuficiente para {item.producto.nombre}")
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente para {item.producto.nombre}'
                }, status=400)

        # Crear la venta
        venta = Venta.objects.create(
            usuario=request.user,
            total=total_clp,
            estado='pendiente',
            direccion_entrega=info_entrega['direccion'],
            ciudad=info_entrega['ciudad'],
            telefono_contacto=info_entrega['telefono'],
            notas=info_entrega.get('notas', ''),
            metodo_pago='paypal',
            paypal_payment_id=order_id,
            paypal_payer_id=payer_id,
            paypal_payment_status=status
        )

        # Crear los items de la venta y actualizar stock
        for item in items:
            precio_unitario = item.producto.precio_actual()
            subtotal = precio_unitario * item.cantidad
            DetalleVenta.objects.create(
                venta=venta,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            # Actualizar stock
            item.producto.stock -= item.cantidad
            item.producto.save()

        # Limpiar el carrito y la sesión
        carrito.items.all().delete()
        request.session.pop('paypal_payment_id', None)
        request.session.pop('paypal_total_clp', None)
        request.session.pop('paypal_items', None)
        request.session.pop('info_entrega', None)

        print(f"Venta creada exitosamente: {venta.id}")
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('confirmacion_compra')  # URL directa en lugar de usar reverse
        })

    except json.JSONDecodeError:
        print("Error: No se pudo decodificar el JSON del body")
        return JsonResponse({
            'success': False,
            'error': 'Datos de pago inválidos'
        }, status=400)
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error al procesar el pago'
        }, status=500)

@login_required
def confirmacion_compra(request):
    """Muestra la página de confirmación de compra con boleta de la última compra."""
    # Obtener la última venta del usuario
    venta = None
    detalles = []
    if request.user.is_authenticated:
        from core.models import Venta, DetalleVenta
        venta = Venta.objects.filter(cliente=request.user).order_by('-fecha').first()
        if venta:
            detalles = DetalleVenta.objects.filter(venta=venta).select_related('producto')
    return render(request, 'core/confirmacionCompra.html', {
        'venta': venta,
        'detalles': detalles
    })

@login_required
@require_http_methods(["POST"])
def guardar_info_entrega(request):
    """Guarda la información de entrega y el payment_id en la sesión."""
    try:
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        form_data = data.get('form_data', {})
        
        if not payment_id:
            return JsonResponse({
                'success': False,
                'error': 'No se recibió el ID de la orden'
            }, status=400)
            
        # Guardar payment_id en la sesión
        request.session['paypal_payment_id'] = payment_id
        
        # Guardar información de entrega
        info_entrega = {
            'direccion': form_data.get('direccion', ''),
            'ciudad': form_data.get('ciudad', ''),
            'telefono': form_data.get('telefono', ''),
            'notas': form_data.get('instrucciones', '')
        }
        request.session['info_entrega'] = info_entrega
        
        print(f"\n=== INFO GUARDADA EN SESIÓN ===")
        print(f"Payment ID: {payment_id}")
        print(f"Info entrega: {info_entrega}")
        
        return JsonResponse({
            'success': True,
            'message': 'Información guardada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Error al procesar los datos'
        }, status=400)
    except Exception as e:
        print(f"Error al guardar info: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def obtener_detalle_pedido(request, venta_id):
    """Obtiene el detalle de un pedido."""
    try:
        # Obtener la venta con sus detalles
        venta = get_object_or_404(
            Venta.objects.select_related('cliente').prefetch_related('detalles__producto'),
            id=venta_id
        )
        
        # Preparar los datos
        detalles = [{
            'producto': {
                'id': detalle.producto.id,
                'nombre': detalle.producto.nombre,
                'codigo': detalle.producto.codigo,
                'stock': detalle.producto.stock,
                'imagen_url': detalle.producto.imagen.url if detalle.producto.imagen else None
            },
            'cantidad': detalle.cantidad,
            'precio_unitario': detalle.precio_unitario,
            'subtotal': detalle.subtotal,
            'preparado': detalle.preparado,
            'preparado_por': detalle.preparado_por.get_full_name() if hasattr(detalle, 'preparado_por') and detalle.preparado_por else None,
            'fecha_preparacion': detalle.fecha_preparacion.strftime('%d/%m/%Y %H:%M') if hasattr(detalle, 'fecha_preparacion') and detalle.fecha_preparacion else None,
            'notas_preparacion': detalle.notas_preparacion if hasattr(detalle, 'notas_preparacion') else None
        } for detalle in venta.detalles.all()]
        data = {
            'success': True,
            'venta': {
                'id': venta.id,
                'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
                'cliente': venta.cliente.get_full_name() or venta.cliente.username,
                'estado': venta.estado,
                'total': venta.total,
                'direccion_entrega': venta.direccion_entrega,
                'ciudad': venta.ciudad,
                'telefono_contacto': venta.telefono_contacto,
                'notas': venta.notas,
                'aceptada_por': venta.aceptada_por.get_full_name() if hasattr(venta, 'aceptada_por') and venta.aceptada_por else None,
                'fecha_aceptacion': venta.fecha_aceptacion.strftime('%d/%m/%Y %H:%M') if hasattr(venta, 'fecha_aceptacion') and venta.fecha_aceptacion else None,
                'fecha_preparacion': venta.fecha_preparacion.strftime('%d/%m/%Y %H:%M') if hasattr(venta, 'fecha_preparacion') and venta.fecha_preparacion else None,
                'detalles': detalles
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def api_pedidos_pendientes(request):
    """
    API para obtener las ventas que necesitan ser preparadas y enviadas.
    Retorna un JSON con la lista de ventas en estado 'confirmada' y 'enviada',
    incluyendo información detallada para la preparación del pedido.
    """
    try:
        # Obtener filtros
        estado = request.GET.get('estado')
        prioridad = request.GET.get('prioridad')
        busqueda = request.GET.get('busqueda')
        
        # Base query
        ventas = Venta.objects.filter(
            estado__in=['confirmada', 'enviada']
        ).select_related(
            'cliente',
            'actualizado_por'
        ).prefetch_related(
            'detalles__producto',
            'detalles__producto__categoria',
            'detalles__preparado_por'
        )
        
        # Aplicar filtros
        if estado:
            ventas = ventas.filter(estado=estado)
        if prioridad:
            ventas = ventas.filter(prioridad=prioridad)
        if busqueda:
            ventas = ventas.filter(
                Q(id__icontains=busqueda) |
                Q(cliente__username__icontains=busqueda) |
                Q(cliente__first_name__icontains=busqueda) |
                Q(cliente__last_name__icontains=busqueda)
            )
        
        # Ordenar por prioridad y fecha
        ventas = ventas.order_by('-prioridad', '-fecha')

        ventas_data = []
        for venta in ventas:
            # Calcular prioridad actual
            prioridad_actual = venta.calcular_prioridad()
            if prioridad_actual != venta.prioridad:
                venta.prioridad = prioridad_actual
                venta.save()
            
            # Obtener los detalles de los productos agrupados por categoría
            detalles_por_categoria = {}
            for detalle in venta.detalles.all():
                categoria = detalle.producto.categoria.nombre if detalle.producto.categoria else 'Sin categoría'
                if categoria not in detalles_por_categoria:
                    detalles_por_categoria[categoria] = []
                
                detalles_por_categoria[categoria].append({
                    'producto': {
                        'id': detalle.producto.id,
                        'nombre': detalle.producto.nombre,
                        'codigo': detalle.producto.codigo,
                        'stock': detalle.producto.stock,
                        'ubicacion': detalle.ubicacion_bodega or 'No especificada'
                    },
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.subtotal),
                    'preparado': detalle.preparado,
                    'fecha_preparacion': detalle.fecha_preparacion.strftime('%d/%m/%Y %H:%M') if detalle.fecha_preparacion else None,
                    'preparado_por': detalle.preparado_por.get_full_name() if detalle.preparado_por else None,
                    'notas_preparacion': detalle.notas_preparacion
                })

            # Calcular estadísticas de preparación
            total_productos = sum(len(detalles) for detalles in detalles_por_categoria.values())
            productos_preparados = sum(
                sum(1 for detalle in detalles if detalle['preparado'])
                for detalles in detalles_por_categoria.values()
            )
            porcentaje_preparado = (productos_preparados / total_productos * 100) if total_productos > 0 else 0

            # Calcular tiempo en estado actual
            tiempo_en_estado = timezone.now() - venta.ultima_actualizacion
            horas_en_estado = tiempo_en_estado.total_seconds() / 3600

            ventas_data.append({
                'id': venta.id,
                'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
                'cliente': venta.cliente.get_full_name() or venta.cliente.username,
                'total': float(venta.total),
                'estado': venta.estado,
                'telefono': venta.telefono_contacto,
                'direccion': venta.direccion_entrega,
                'ciudad': venta.ciudad,
                'metodo_pago': venta.metodo_pago,
                'notas': venta.notas,
                'prioridad': venta.prioridad,
                'fecha_limite_entrega': venta.fecha_limite_entrega.strftime('%d/%m/%Y %H:%M') if venta.fecha_limite_entrega else None,
                'horas_en_estado': round(horas_en_estado, 1),
                'ultima_actualizacion': venta.ultima_actualizacion.strftime('%d/%m/%Y %H:%M'),
                'actualizado_por': venta.actualizado_por.get_full_name() if venta.actualizado_por else None,
                'detalles_por_categoria': detalles_por_categoria,
                'estadisticas_preparacion': {
                    'total_productos': total_productos,
                    'productos_preparados': productos_preparados,
                    'porcentaje_preparado': round(porcentaje_preparado, 1)
                },
                'acciones_disponibles': {
                    'preparar': venta.estado == 'confirmada',
                    'entregar': venta.estado == 'enviada',
                    'cancelar': venta.estado in ['confirmada', 'enviada']
                }
            })

        return JsonResponse({
            'success': True,
            'ventas': ventas_data
        })

    except Exception as e:
        logger.error(f"Error en api_pedidos_pendientes: {str(e)}")
        return JsonResponse({'error': 'Error al obtener ventas'}, status=500)

def api_productos_stock_bajo(request):
    """
    API para obtener los productos que tienen stock bajo el mínimo.
    Retorna un JSON con la lista de productos que necesitan reposición.
    """
    try:
        productos = Producto.objects.filter(
            stock__lte=F('stock_minimo'),
            activo=True
        ).select_related('categoria').order_by('stock')
        
        data = {
            'success': True,
            'productos': [{
                'id': p.id,
                'nombre': p.nombre,
                'categoria': p.categoria.nombre,
                'codigo': p.codigo,
                'stock_actual': p.stock,
                'stock_minimo': p.stock_minimo,
                'diferencia': p.stock_minimo - p.stock,
                'precio': float(p.precio),
                'precio_oferta': float(p.precio_oferta) if p.precio_oferta else None,
                'imagen': p.imagen.url if p.imagen else None
            } for p in productos]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def api_marcar_producto_preparado(request, venta_id, producto_id):
    """
    API para marcar un producto como preparado en una venta.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        # Obtener la venta y el detalle
        venta = get_object_or_404(Venta, id=venta_id)
        detalle = get_object_or_404(DetalleVenta, venta=venta, producto_id=producto_id)
        
        # Obtener datos del body JSON
        data = json.loads(request.body)
        notas = data.get('notas', '')
        ubicacion = data.get('ubicacion', '')
        
        # Actualizar ubicación si se proporciona
        if ubicacion:
            detalle.ubicacion_bodega = ubicacion
        
        # Marcar como preparado
        todos_preparados = detalle.marcar_preparado(request.user, notas)
        
        return JsonResponse({
            'success': True,
            'todos_preparados': todos_preparados,
            'nuevo_estado': venta.estado if todos_preparados else None,
            'fecha_preparacion': detalle.fecha_preparacion.strftime('%d/%m/%Y %H:%M'),
            'preparado_por': request.user.get_full_name()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error en api_marcar_producto_preparado: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def api_actualizar_estado_pedido(request, venta_id):
    """
    API para actualizar el estado de un pedido.
    Maneja la preparación, envío y cancelación de pedidos.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        venta = get_object_or_404(Venta, id=venta_id)
        data = json.loads(request.body)
        accion = data.get('accion')
        notas = data.get('notas', '')

        if not accion:
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)

        # Validar la transición de estado
        estados_validos = {
            'preparar': ('confirmada', 'enviada'),
            'entregar': ('enviada', 'entregada'),
            'cancelar': ('confirmada', 'cancelada')
        }

        if accion not in estados_validos or venta.estado != estados_validos[accion][0]:
            return JsonResponse({
                'error': f'No se puede {accion} un pedido en estado {venta.estado}'
            }, status=400)

        # Actualizar el estado
        venta.estado = estados_validos[accion][1]
        venta.actualizado_por = request.user
        venta.save()

        # Si se cancela el pedido, restaurar el stock
        if accion == 'cancelar':
            for detalle in venta.detalles.all():
                producto = detalle.producto
                producto.stock += detalle.cantidad
                producto.save()
                
                # Registrar la cancelación en las notas del detalle
                detalle.notas_preparacion = f"Cancelado: {notas}" if notas else "Pedido cancelado"
                detalle.save()

        # Crear notificación para el cliente
        mensaje = {
            'preparar': 'Tu pedido está siendo preparado',
            'entregar': 'Tu pedido ha sido entregado',
            'cancelar': 'Tu pedido ha sido cancelado'
        }[accion]
        
        if notas:
            mensaje += f"\nNotas: {notas}"

        Notificacion.objects.create(
            usuario=venta.cliente,
            titulo=f'Actualización de Pedido #{venta.id}',
            mensaje=mensaje,
            tipo='pedido'
        )

        return JsonResponse({
            'success': True,
            'mensaje': f'Pedido {accion}do exitosamente',
            'nuevo_estado': venta.estado,
            'actualizado_por': request.user.get_full_name(),
            'fecha_actualizacion': venta.ultima_actualizacion.strftime('%d/%m/%Y %H:%M')
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos inválidos'}, status=400)
    except Venta.DoesNotExist:
        return JsonResponse({'error': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error en api_actualizar_estado_pedido: {str(e)}")
        return JsonResponse({'error': 'Error al actualizar el estado del pedido'}, status=500)

def pedidos_pendientes(request):
    """Vista para obtener los pedidos pendientes."""
    ventas = Venta.objects.filter(
        estado__in=['confirmada', 'enviada']
    ).order_by('-fecha_creacion')
    
    ventas_data = []
    for venta in ventas:
        detalles_por_categoria = {}
        productos_preparados = 0
        total_productos = 0
        
        for detalle in venta.detalleventa_set.all():
            categoria = detalle.producto.categoria.nombre
            if categoria not in detalles_por_categoria:
                detalles_por_categoria[categoria] = []
            
            preparado = detalle.preparado if hasattr(detalle, 'preparado') else False
            if preparado:
                productos_preparados += 1
            total_productos += 1
            
            detalles_por_categoria[categoria].append({
                'producto': {
                    'id': detalle.producto.id,
                    'nombre': detalle.producto.nombre,
                    'codigo': detalle.producto.codigo,
                    'ubicacion': detalle.producto.ubicacion
                },
                'cantidad': detalle.cantidad,
                'preparado': preparado
            })
        
        acciones_disponibles = {
            'preparar': venta.estado == 'confirmada',
            'entregar': venta.estado == 'enviada',
            'cancelar': venta.estado not in ['entregada', 'cancelada']
        }
        
        ventas_data.append({
            'id': venta.id,
            'cliente': venta.cliente.nombre,
            'telefono': venta.cliente.telefono,
            'direccion': venta.direccion_entrega,
            'ciudad': venta.ciudad,
            'fecha': venta.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'total': float(venta.total),
            'estado': venta.estado,
            'notas': venta.notas,
            'prioridad': 'alta' if venta.prioridad == 'alta' else 'normal',
            'detalles_por_categoria': detalles_por_categoria,
            'estadisticas_preparacion': {
                'productos_preparados': productos_preparados,
                'total_productos': total_productos,
                'porcentaje_preparado': int((productos_preparados / total_productos * 100) if total_productos > 0 else 0)
            },
            'acciones_disponibles': acciones_disponibles
        })
    
    return JsonResponse({'ventas': ventas_data})

def marcar_producto_preparado(request, venta_id, producto_id):
    """Vista para marcar un producto como preparado en un pedido."""
    if request.method == 'POST':
        try:
            detalle = DetalleVenta.objects.get(
                venta_id=venta_id,
                producto_id=producto_id
            )
            detalle.preparado = True
            detalle.save()
            
            venta = detalle.venta
            todos_preparados = not venta.detalleventa_set.filter(preparado=False).exists()
            
            if todos_preparados and venta.estado == 'confirmada':
                venta.estado = 'enviada'
                venta.save()
            
            return JsonResponse({
                'success': True,
                'todos_preparados': todos_preparados
            })
        except DetalleVenta.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Detalle de venta no encontrado'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

def actualizar_estado_pedido(request, venta_id):
    """Vista para actualizar el estado de un pedido."""
    if request.method == 'POST':
        try:
            venta = Venta.objects.get(id=venta_id)
            accion = request.POST.get('estado')
            
            if accion == 'preparar':
                if venta.estado != 'confirmada':
                    raise ValueError('El pedido debe estar confirmado para prepararlo')
                venta.estado = 'enviada'
                mensaje = 'Pedido marcado como enviado'
            
            elif accion == 'entregar':
                if venta.estado != 'enviada':
                    raise ValueError('El pedido debe estar enviado para marcarlo como entregado')
                venta.estado = 'entregada'
                mensaje = 'Pedido marcado como entregado'
            
            elif accion == 'cancelar':
                if venta.estado in ['entregada', 'cancelada']:
                    raise ValueError('No se puede cancelar un pedido entregado o ya cancelado')
                venta.estado = 'cancelada'
                mensaje = 'Pedido cancelado'
            
            else:
                raise ValueError('Acción no válida')
            
            venta.save()
            return JsonResponse({
                'success': True,
                'mensaje': mensaje
            })
            
        except Venta.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Venta no encontrada'
            }, status=404)
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    }, status=405)

@login_required
def crear_orden_paypal(request):
    """Prepara los datos para crear una orden de PayPal."""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Método no permitido'
        }, status=405)
    
    try:
        # 1. Obtener el carrito del usuario
        carrito = Carrito.objects.get(usuario=request.user)
        carrito_items = CarritoItem.objects.filter(carrito=carrito).select_related('producto')
        
        if not carrito_items.exists():
            return JsonResponse({
                'success': False,
                'error': 'El carrito está vacío'
            }, status=400)
        
        # 2. Validar stock
        for item in carrito_items:
            if item.producto.stock < item.cantidad:
                return JsonResponse({
                    'success': False,
                    'error': f'No hay suficiente stock de {item.producto.nombre}'
                }, status=400)
        
        # 3. Calcular totales
        total_carrito_clp = sum(item.subtotal for item in carrito_items)
        TASA_CAMBIO_CLP_USD = 0.001
        total_carrito_usd = round(total_carrito_clp * TASA_CAMBIO_CLP_USD, 2)
        
        # 4. Preparar items para PayPal
        items = []
        item_total = 0
        for item in carrito_items:
            precio_usd = round(item.producto.precio_actual() * TASA_CAMBIO_CLP_USD, 2)
            subtotal_item = round(precio_usd * item.cantidad, 2)
            item_total += subtotal_item
            
            items.append({
                "name": item.producto.nombre,
                "sku": item.producto.codigo,
                "unit_amount": {
                    "currency_code": "USD",
                    "value": str(precio_usd)
                },
                "quantity": str(item.cantidad),
                "description": f"Precio unitario: ${precio_usd} USD"
            })
        
        # 5. Preparar el desglose del monto
        amount_breakdown = {
            "item_total": {
                "currency_code": "USD",
                "value": str(round(item_total, 2))
            }
        }
        
        # 6. Guardar datos en sesión para uso posterior
        request.session['paypal_total_clp'] = total_carrito_clp
        request.session['paypal_items'] = items
        
        # 7. Devolver datos para crear la orden
        return JsonResponse({
            'success': True,
            'total_usd': str(total_carrito_usd),
            'items': items,
            'amount_breakdown': amount_breakdown
        })
        
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def es_vendedor(user):
    return user.is_authenticated and user.groups.filter(name='vendedores').exists()

@user_passes_test(es_vendedor)
def panel_vendedor_ventas(request):
    from core.models import Venta, DetalleVenta
    ventas_pendientes = Venta.objects.filter(estado='pendiente').order_by('-fecha').select_related('cliente')
    return render(request, 'core/panelVendedorVentas.html', {
        'ventas': ventas_pendientes
    })

@user_passes_test(es_vendedor)
def aceptar_venta(request, venta_id):
    from core.models import Venta
    from django.http import JsonResponse
    if request.method == 'POST':
        try:
            venta = Venta.objects.get(id=venta_id, estado='pendiente')
            venta.estado = 'confirmada'
            venta.save()
            return JsonResponse({'success': True, 'message': 'Venta aceptada'})
        except Venta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Venta no encontrada o ya gestionada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@user_passes_test(es_vendedor)
def rechazar_venta(request, venta_id):
    from core.models import Venta
    from django.http import JsonResponse
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        try:
            venta = Venta.objects.get(id=venta_id, estado='pendiente')
            venta.estado = 'rechazada'
            venta.notas = motivo
            venta.save()
            return JsonResponse({'success': True, 'message': 'Venta rechazada'})
        except Venta.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Venta no encontrada o ya gestionada'}, status=404)
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

from django.http import JsonResponse
@login_required
def historial_compras_cliente(request, cliente_id):
    from core.models import Venta, DetalleVenta
    from django.contrib.auth.models import User
    try:
        cliente = User.objects.get(id=cliente_id)
        ventas = Venta.objects.filter(cliente=cliente).order_by('-fecha').prefetch_related('detalles__producto')
        historial = []
        for venta in ventas:
            detalles = [
                {
                    'producto': d.producto.nombre,
                    'cantidad': d.cantidad,
                    'precio_unitario': float(d.precio_unitario),
                    'subtotal': float(d.subtotal)
                }
                for d in venta.detalles.all()
            ]
            historial.append({
                'id': venta.id,
                'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
                'total': float(venta.total),
                'estado': venta.estado,
                'detalles': detalles
            })
        return JsonResponse({
            'success': True,
            'cliente': cliente.get_full_name() or cliente.username,
            'historial': historial
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def api_buscar_ventas(request):
    from core.models import Venta
    from django.db.models import Q
    from datetime import datetime

    busqueda = request.GET.get('q', '').strip()
    fecha = request.GET.get('fecha')
    ventas_query = Venta.objects.select_related('cliente').prefetch_related('detalles__producto').all()
    if busqueda:
        ventas_query = ventas_query.filter(
            Q(id__icontains=busqueda) |
            Q(cliente__username__icontains=busqueda) |
            Q(cliente__first_name__icontains=busqueda) |
            Q(cliente__last_name__icontains=busqueda) |
            Q(direccion_entrega__icontains=busqueda) |
            Q(ciudad__icontains=busqueda) |
            Q(detalles__producto__nombre__icontains=busqueda) |
            Q(estado__icontains=busqueda)
        ).distinct()
    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
            ventas_query = ventas_query.filter(fecha__date=fecha_dt.date())
        except Exception:
            pass
    ventas_query = ventas_query.order_by('-fecha')[:50]

    data = []
    for venta in ventas_query:
        productos_html = ''.join([
            f"<div>- {d.producto.nombre} x{d.cantidad}</div>"
            for d in venta.detalles.all()
        ])
        data.append({
            'id': venta.id,
            'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
            'cliente': venta.cliente.get_full_name() or venta.cliente.username,
            'direccion': venta.direccion_entrega,
            'ciudad': venta.ciudad,
            'telefono': venta.telefono_contacto,
            'productos_html': productos_html,
            'total': venta.total,
            'estado': venta.estado.title(),
        })
    return JsonResponse({'ventas': data})

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all().select_related('cliente').prefetch_related('detalles__producto')
    serializer_class = VentaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['fecha', 'estado', 'cliente', 'ciudad']
    search_fields = ['id', 'cliente__username', 'cliente__first_name', 'cliente__last_name', 'direccion_entrega', 'ciudad', 'detalles__producto__nombre', 'estado']
    ordering_fields = ['fecha', 'total', 'estado']
    ordering = ['-fecha']

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user)

@require_GET
def api_reporte_ventas(request):
    tipo = request.GET.get('tipo', 'mensual')
    anio = int(request.GET.get('anio', datetime.now().year))
    mes = int(request.GET.get('mes', 0))

    if tipo == 'mensual':
        # Ventas por mes del año
        data = []
        for m in range(1, 13):
            total = Venta.objects.filter(
                fecha__year=anio,
                fecha__month=m
            ).aggregate(total=Sum('total'))['total'] or 0
            data.append({'mes': m, 'total': total})
        return JsonResponse({'tipo': 'mensual', 'anio': anio, 'data': data})

    elif tipo == 'diario' and mes:
        # Ventas por día del mes
        from calendar import monthrange
        dias = monthrange(anio, mes)[1]
        data = []
        for d in range(1, dias+1):
            total = Venta.objects.filter(
                fecha__year=anio,
                fecha__month=mes,
                fecha__day=d
            ).aggregate(total=Sum('total'))['total'] or 0
            data.append({'dia': d, 'total': total})
        return JsonResponse({'tipo': 'diario', 'anio': anio, 'mes': mes, 'data': data})

    elif tipo == 'por_cliente':
        # Ventas por cliente
        clientes = Venta.objects.filter(fecha__year=anio).values('cliente__username').annotate(total=Sum('total')).order_by('-total')
        data = list(clientes)
        return JsonResponse({'tipo': 'por_cliente', 'anio': anio, 'data': data})

    else:
        return JsonResponse({'error': 'Tipo de reporte no soportado'}, status=400)

@require_GET
def api_top_productos(request):
    limite = int(request.GET.get('limite', 10))
    productos = DetalleVenta.objects.values('producto__nombre').annotate(
        cantidad=Sum('cantidad')
    ).order_by('-cantidad')[:limite]
    data = list(productos)
    return JsonResponse({'top_productos': data})

@require_GET
def api_ventas_por_categoria(request):
    anio = int(request.GET.get('anio', datetime.now().year))
    mes = int(request.GET.get('mes', 0))
    detalles = DetalleVenta.objects.select_related('producto__categoria', 'venta')
    if anio:
        detalles = detalles.filter(venta__fecha__year=anio)
    if mes:
        detalles = detalles.filter(venta__fecha__month=mes)
    categorias = detalles.values('producto__categoria__nombre').annotate(
        total=Sum('subtotal')
    ).order_by('-total')
    data = list(categorias)
    return JsonResponse({'ventas_por_categoria': data})

# ===== API UNIFICADA SWEETALERT2 =====

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_sweet_alert(request):
    """
    API unificada para SweetAlert2
    Recibe cualquier parámetro que quieras usar en SweetAlert2
    Ejemplo de uso: POST /api/sweet-alert/
    """
    config = dict(request.data)
    return Response({'success': True, 'sweetAlert': config})

@require_POST
def api_marcar_productos_preparados(request, venta_id):
    """Marca productos como preparados en una venta."""
    import json
    try:
        data = json.loads(request.body)
        preparados = data.get('preparados', [])  # lista de IDs de productos preparados
        from core.models import DetalleVenta, Venta
        venta = Venta.objects.get(id=venta_id)
        detalles = venta.detalles.all()
        for detalle in detalles:
            detalle.preparado = detalle.producto.id in preparados
            detalle.save()
        return JsonResponse({'success': True, 'message': 'Estado de preparación actualizado.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'trace': traceback.format_exc()}, status=500)

@login_required
@require_POST
def actualizar_estado_pedido_admin(request, venta_id):
    """Vista para que el administrador actualice el estado de un pedido"""
    try:
        # Verificar que el usuario sea administrador
        if not request.user.groups.filter(name='administradores').exists():
            return JsonResponse({
                'success': False,
                'message': 'No tienes permisos de administrador'
            }, status=403)
        
        venta = get_object_or_404(Venta, id=venta_id)
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
        
        if not nuevo_estado:
            return JsonResponse({
                'success': False,
                'message': 'Estado no especificado'
            }, status=400)
        
        # Validar transiciones de estado permitidas
        estados_permitidos = {
            'pendiente': ['confirmada', 'cancelada'],
            'confirmada': ['enviada', 'cancelada'],
            'enviada': ['entregada'],
            'entregada': [],  # Estado final
            'cancelada': []   # Estado final
        }
        
        if venta.estado in estados_permitidos and nuevo_estado not in estados_permitidos[venta.estado]:
            return JsonResponse({
                'success': False,
                'message': f'No se puede cambiar de "{venta.estado}" a "{nuevo_estado}"'
            }, status=400)
        
        # Actualizar estado
        estado_anterior = venta.estado
        venta.estado = nuevo_estado
        venta.ultima_actualizacion = timezone.now()
        
        # Asignar usuario que actualizó el estado
        if nuevo_estado == 'confirmada' and not venta.aceptada_por:
            venta.aceptada_por = request.user
            venta.fecha_aceptacion = timezone.now()
        
        venta.save()
        
        # Si el estado es 'enviada', marcar todos los productos como preparados
        if nuevo_estado == 'enviada':
            for detalle in venta.detalles.all():
                if not detalle.preparado:
                    detalle.marcar_preparado(request.user, 'Preparado automáticamente por administrador')
        
        # Crear notificación para el cliente
        Notificacion.objects.create(
            usuario=venta.cliente,
            tipo='sistema',
            mensaje=f'Tu pedido #{venta.id} ha cambiado de estado de "{estado_anterior}" a "{nuevo_estado}"'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Estado actualizado correctamente de "{estado_anterior}" a "{nuevo_estado}"',
            'nuevo_estado': nuevo_estado
        })
        
    except Venta.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pedido no encontrado'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        print(f"Error al actualizar estado del pedido: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }, status=500)

def es_bodeguero(user):
    return user.groups.filter(name='bodegueros').exists() or user.is_superuser

@login_required
@user_passes_test(es_bodeguero)
@require_POST
def api_actualizar_stock(request, producto_id):
    import json
    try:
        data = json.loads(request.body)
        nuevo_stock = int(data.get('stock', -1))
        if nuevo_stock < 0:
            return JsonResponse({'success': False, 'error': 'Stock inválido'}, status=400)
        from core.models import Producto
        producto = Producto.objects.get(id=producto_id)
        producto.stock = nuevo_stock
        producto.save()
        return JsonResponse({'success': True})
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Producto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(es_bodeguero)
@require_POST
def api_marcar_entregado(request, venta_id):
    from core.models import Venta
    try:
        venta = Venta.objects.get(id=venta_id)
        if venta.estado != 'confirmada':
            return JsonResponse({'success': False, 'error': 'Solo se pueden entregar pedidos confirmados.'}, status=400)
        # Verificar que todos los productos estén preparados
        total = venta.detalles.count()
        preparados = venta.detalles.filter(preparado=True).count()
        if total == 0 or preparados < total:
            return JsonResponse({'success': False, 'error': 'No todos los productos están preparados.'}, status=400)
        venta.estado = 'preparada'
        venta.save()
        return JsonResponse({'success': True})
    except Venta.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pedido no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

   