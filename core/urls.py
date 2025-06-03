from django.urls import path, include
from .views import (
    index, catalogo, carrito, detalleProducto, registrarse, registercliente,
    logincliente, login_view, loginadmin, loginTrabajador, panelAdmin,
    panelBodeguero, panelVendedor, procesoCompra, logout_view, crear_categoria,
    lista_productos, crear_producto, editar_producto, eliminar_producto,
    obtener_producto, lista_empleados, crear_empleado, editar_empleado,
    eliminar_empleado, obtener_empleado, agregar_al_carrito, actualizar_carrito,
    eliminar_del_carrito, obtener_productos_oferta
)
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', index, name='index'),
    path('catalogo/', catalogo, name='catalogo'),
    path('carrito/', carrito, name='carrito'),
    path('carrito/actualizar/<int:item_id>/', actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('producto/<int:id>/', detalleProducto, name='detalle_producto'),
    path('registrarse/', registrarse, name='registrarse'),
    path('registercliente/', registercliente, name='registercliente'),
    path('logincliente/', logincliente, name='logincliente'),
    path('login/', login_view, name='login'),
    path('loginAdmin/', loginadmin, name='loginAdmin'),
    path('loginTrabajador/', loginTrabajador, name='loginTrabajador'),
    path('panelAdmin/', panelAdmin, name='panelAdmin'),
    path('panelBodeguero/', panelBodeguero, name='panelBodeguero'),
    path('panelVendedor/', panelVendedor, name='panelVendedor'),
    path('procesoCompra/', procesoCompra, name='procesoCompra'),
    path('logout/', logout_view, name='logout'),
    path('panel/categorias/crear/', crear_categoria, name='crear_categoria'),
    path('panel/productos/', lista_productos, name='lista_productos'),
    path('panel/productos/crear/', crear_producto, name='crear_producto'),
    path('panel/productos/editar/<int:id>/', editar_producto, name='editar_producto'),
    path('panel/productos/eliminar/<int:id>/', eliminar_producto, name='eliminar_producto'),
    path('panel/productos/obtener/<int:id>/', obtener_producto, name='obtener_producto'),
    path('panel/productos/ofertas/', obtener_productos_oferta, name='obtener_productos_oferta'),
    path('panel/empleados/', lista_empleados, name='lista_empleados'),
    path('panel/empleados/crear/', crear_empleado, name='crear_empleado'),
    path('panel/empleados/editar/<int:id>/', editar_empleado, name='editar_empleado'),
    path('panel/empleados/eliminar/<int:id>/', eliminar_empleado, name='eliminar_empleado'),
    path('panel/empleados/obtener/<int:id>/', obtener_empleado, name='obtener_empleado'),
    path('carrito/agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_al_carrito'),
]       