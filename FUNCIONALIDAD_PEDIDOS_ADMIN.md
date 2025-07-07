# Funcionalidad de Pedidos - Panel de Administrador

## 🎯 Características Implementadas

### 📊 **Vista General de Pedidos**
- **Tabla completa** con todos los pedidos del sistema
- **Información detallada** de cada pedido:
  - ID del pedido y prioridad
  - Fecha de creación
  - Cliente y datos de contacto
  - Total de la venta
  - Estado actual del pedido
  - Vendedor que aceptó el pedido
  - Bodeguero que preparó el pedido
  - Progreso de preparación
  - Tiempo en estado actual

### 🔍 **Filtros y Búsqueda**
- **Filtro por estado**: Pendiente, Confirmada, Enviada, Entregada, Cancelada
- **Búsqueda por cliente**: Búsqueda en tiempo real
- **Ordenamiento**: Por fecha, total, prioridad
- **Contadores dinámicos**: Muestra estadísticas en tiempo real

### 📈 **Estadísticas Rápidas**
- **Tarjetas de resumen** con contadores por estado
- **Actualización automática** al aplicar filtros
- **Indicadores visuales** con colores diferenciados

### ⚡ **Acciones Disponibles**
- **Ver detalle completo** del pedido
- **Ver ubicación** en Google Maps
- **Cambiar estado** del pedido:
  - Pendiente → Confirmada
  - Confirmada → Enviada
  - Enviada → Entregada
- **Notificaciones automáticas** al cliente

## 🚀 Cómo Usar

### 1. **Acceder a la Sección de Pedidos**
1. Inicia sesión como administrador
2. Ve al panel de administrador (`/panelAdmin/`)
3. Haz clic en "📑 Pedidos" en el menú lateral

### 2. **Filtrar y Buscar Pedidos**
- **Filtro por estado**: Selecciona el estado deseado en el dropdown
- **Búsqueda**: Escribe el nombre del cliente en el campo de búsqueda
- **Ordenamiento**: Selecciona el criterio de ordenamiento

### 3. **Ver Detalles de un Pedido**
1. Haz clic en el botón 👁️ (Ver detalle) en la fila del pedido
2. Se abrirá un modal con información completa:
   - Datos del cliente
   - Información de la venta
   - Lista de productos con estados
   - Historial de cambios

### 4. **Cambiar Estado de un Pedido**
1. Haz clic en el botón correspondiente según el estado actual:
   - ✅ **Confirmar** (para pedidos pendientes)
   - 🚚 **Marcar como enviada** (para pedidos confirmados)
   - 📦 **Marcar como entregada** (para pedidos enviados)
2. Confirma la acción en el diálogo
3. El estado se actualizará automáticamente

### 5. **Ver Ubicación del Cliente**
- Haz clic en el botón 📍 (Ver ubicación)
- Se abrirá Google Maps con la dirección del cliente

## 📋 Información Mostrada

### **Columnas de la Tabla**
1. **ID**: Número del pedido con indicador de prioridad
2. **Fecha**: Fecha y hora de creación
3. **Cliente**: Nombre y teléfono
4. **Total**: Monto total de la venta
5. **Estado**: Badge con color según el estado
6. **Prioridad**: Indicador de prioridad (Alta/Media/Normal)
7. **Vendedor**: Quien aceptó el pedido y cuándo
8. **Bodeguero**: Quien preparó el pedido y cuándo
9. **Preparación**: Barra de progreso con porcentaje
10. **Tiempo**: Horas en el estado actual
11. **Acciones**: Botones para interactuar

### **Estados de Pedidos**
- 🟡 **Pendiente**: Pedido recién creado
- 🔵 **Confirmada**: Pedido aceptado por vendedor
- 🟦 **Enviada**: Pedido preparado y enviado
- 🟢 **Entregada**: Pedido entregado al cliente
- 🔴 **Cancelada**: Pedido cancelado

### **Indicadores de Tiempo**
- 🟢 **Verde**: Menos de 12 horas
- 🟡 **Amarillo**: Entre 12 y 24 horas
- 🔴 **Rojo**: Más de 24 horas

## 🔧 Funcionalidades Técnicas

### **Validaciones de Estado**
- Solo se permiten transiciones válidas entre estados
- Se registra automáticamente quién realizó cada cambio
- Se crean notificaciones para el cliente

### **Optimizaciones**
- **Carga eficiente** de datos con `select_related` y `prefetch_related`
- **Filtrado en tiempo real** sin recargar la página
- **Contadores dinámicos** que se actualizan automáticamente

### **Seguridad**
- **Verificación de permisos** de administrador
- **Validación de datos** en el servidor
- **Manejo de errores** robusto

## 📱 Responsive Design
- **Tabla responsive** que se adapta a diferentes tamaños de pantalla
- **Botones táctiles** optimizados para dispositivos móviles
- **Modal adaptable** para ver detalles en pantallas pequeñas

## 🔄 Actualizaciones en Tiempo Real
- **Botón de actualizar** para recargar datos
- **Contadores automáticos** que se actualizan con filtros
- **Notificaciones** que informan sobre cambios de estado

## 🎨 Personalización Visual
- **Colores diferenciados** por estado y prioridad
- **Iconos intuitivos** para cada acción
- **Barras de progreso** para mostrar preparación
- **Badges informativos** para estados y prioridades

## 📊 Reportes y Analytics
- **Estadísticas por estado** en tiempo real
- **Tiempo promedio** en cada estado
- **Productos más vendidos** (en sección de reportes)
- **Ventas por categoría** (en sección de reportes)

Esta funcionalidad proporciona una vista completa y gestionable de todos los pedidos del sistema, permitiendo al administrador tener control total sobre el flujo de trabajo de ventas. 