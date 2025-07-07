from django.urls import path, include
from .views import (
    index, catalogo, carrito, detalleProducto, registrarse, registercliente,
    login_view, loginadmin, loginTrabajador, panelAdmin,
    panelBodeguero, panelVendedor, procesoCompra, logout_view, crear_categoria,
    crear_producto, editar_producto, eliminar_producto,
    obtener_producto, lista_empleados, crear_empleado, editar_empleado,
    eliminar_empleado, obtener_empleado, agregar_al_carrito, actualizar_carrito,
    eliminar_del_carrito, obtener_productos_oferta, crear_orden_paypal, ejecutar_pago_paypal,
    confirmacion_compra, guardar_info_entrega, actualizar_estado_pedido, obtener_detalle_pedido,
    historial_compras_cliente, api_buscar_ventas, aceptar_venta, rechazar_venta,
    api_sweet_alert, api_marcar_productos_preparados, actualizar_estado_pedido_admin,
    api_actualizar_stock, api_marcar_entregado,
)
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter
from core.views import VentaViewSet, api_reporte_ventas, api_top_productos, api_ventas_por_categoria

router = DefaultRouter()
router.register(r'api/ventas', VentaViewSet, basename='api-ventas')

urlpatterns = [
    path('', index, name='index'),
    path('catalogo/', catalogo, name='catalogo'),
    path('carrito/', carrito, name='carrito'),
    path('carrito/actualizar/<int:item_id>/', actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:item_id>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('producto/<int:id>/', detalleProducto, name='detalle_producto'),
    path('registrarse/', registrarse, name='registrarse'),
    path('registercliente/', registercliente, name='registercliente'),
    path('login/', login_view, name='login'),
    path('loginAdmin/', loginadmin, name='loginAdmin'),
    path('loginTrabajador/', loginTrabajador, name='loginTrabajador'),
    path('panelAdmin/', panelAdmin, name='panelAdmin'),
    path('panelBodeguero/', panelBodeguero, name='panelBodeguero'),
    path('panelVendedor/', panelVendedor, name='panelVendedor'),
    path('procesoCompra/', procesoCompra, name='procesoCompra'),
    path('logout/', logout_view, name='logout'),
    path('panel/categorias/crear/', crear_categoria, name='crear_categoria'),
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
    path('paypal/crear-orden/', crear_orden_paypal, name='paypal_create'),
    path('paypal/ejecutar/', ejecutar_pago_paypal, name='paypal_execute'),
    path('confirmacion-compra/', confirmacion_compra, name='confirmacion_compra'),
    path('guardar-info-entrega/', guardar_info_entrega, name='guardar_info_entrega'),
    path('actualizar-estado-pedido/<int:venta_id>/', actualizar_estado_pedido, name='actualizar_estado_pedido'),
    path('actualizar-estado-pedido-admin/<int:venta_id>/', actualizar_estado_pedido_admin, name='actualizar_estado_pedido_admin'),
    path('obtener-detalle-pedido/<int:venta_id>/', obtener_detalle_pedido, name='obtener_detalle_pedido'),
    path('historial-compras-cliente/<int:cliente_id>/', historial_compras_cliente, name='historial_compras_cliente'),
    path('api/buscar-ventas/', api_buscar_ventas, name='api_buscar_ventas'),
    path('aceptar-venta/<int:venta_id>/', aceptar_venta, name='aceptar_venta'),
    path('rechazar-venta/<int:venta_id>/', rechazar_venta, name='rechazar_venta'),
    path('api/ventas/reportes/', api_reporte_ventas, name='api_reporte_ventas'),
    path('api/ventas/top-productos/', api_top_productos, name='api_top_productos'),
    path('api/ventas/por-categoria/', api_ventas_por_categoria, name='api_ventas_por_categoria'),
    path('api/sweet-alert/', api_sweet_alert, name='api_sweet_alert'),
    path('api/marcar-productos-preparados/<int:venta_id>/', api_marcar_productos_preparados, name='api_marcar_productos_preparados'),
    path('api/actualizar-stock/<int:producto_id>/', api_actualizar_stock, name='api_actualizar_stock'),
    path('api/marcar-entregado/<int:venta_id>/', api_marcar_entregado, name='api_marcar_entregado'),
]

urlpatterns += router.urls       