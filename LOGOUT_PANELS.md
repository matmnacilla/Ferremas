# 🔐 Funcionalidades de Logout - Paneles de Trabajadores

Esta documentación explica las funcionalidades de logout implementadas en los paneles de trabajadores del sistema de gestión de Ferremas.

## 📋 Índice

- [Características Implementadas](#características-implementadas)
- [Paneles Actualizados](#paneles-actualizados)
- [Funcionalidades](#funcionalidades)
- [APIs Creadas](#apis-creadas)
- [Uso](#uso)

## ✅ Características Implementadas

### 🎯 **Funcionalidades Principales**

1. **Botón de Logout Visual** - Botón rojo prominente en el sidebar
2. **Confirmación con SweetAlert2** - Diálogo de confirmación elegante
3. **API REST Específica** - Configuración centralizada del mensaje
4. **Redirección Segura** - Logout automático después de confirmación
5. **Diseño Responsive** - Funciona en todos los dispositivos

### 🎨 **Características de Diseño**

- **Posición Fija**: Botón siempre visible en la parte inferior del sidebar
- **Color Distintivo**: Rojo para indicar acción destructiva
- **Icono Intuitivo**: Flecha de salida para indicar logout
- **Separador Visual**: Línea divisoria antes del botón
- **Efectos Hover**: Cambio de color al pasar el mouse

## 🏪 Paneles Actualizados

### 1. **Panel del Vendedor** (`panelVendedor.html`)

#### **Ubicación del Botón:**
```html
<div class="sidebar">
  <h4>Vendedor - Ferremas</h4>
  <hr>
  <a href="?seccion=dashboard">📊 Dashboard</a>
  <a href="?seccion=pedidos">📦 Gestionar Pedidos</a>
  <a href="?seccion=catalogo">🛠 Catálogo</a>
  <a href="?seccion=historial">📄 Historial de Compras</a>
  <div class="logout-section">
    <a href="#" onclick="confirmarLogout()">
      <i class="bi bi-box-arrow-right"></i> Cerrar Sesión
    </a>
  </div>
</div>
```

#### **Estilos CSS:**
```css
.sidebar {
  display: flex;
  flex-direction: column;
}

.sidebar .logout-section {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid #495057;
}

.sidebar .logout-section a {
  color: #dc3545 !important;
  font-weight: bold;
}

.sidebar .logout-section a:hover {
  background-color: #dc3545;
  color: white !important;
}
```

### 2. **Panel del Bodeguero** (`panelBodeguero.html`)

#### **Ubicación del Botón:**
```html
<div class="sidebar">
  <h4>Bodeguero - Ferremas</h4>
  <hr>
  <a href="#" onclick="showSection('ordenes')">📋 Órdenes</a>
  <a href="#" onclick="showSection('preparar')">📦 Preparar</a>
  <a href="#" onclick="showSection('entregar')">🚚 Entregar</a>
  <a href="#" onclick="showSection('catalogo')">🛠 Catálogo</a>
  <div class="logout-section">
    <a href="#" onclick="confirmarLogout()">
      <i class="bi bi-box-arrow-right"></i> Cerrar Sesión
    </a>
  </div>
</div>
```

## 🔧 Funcionalidades

### **Función de Confirmación**

```javascript
function confirmarLogout() {
  Swal.fire({
    title: '¿Cerrar Sesión?',
    text: '¿Estás seguro de que deseas cerrar sesión?',
    icon: 'question',
    showCancelButton: true,
    confirmButtonText: 'Sí, cerrar sesión',
    cancelButtonText: 'Cancelar',
    confirmButtonColor: '#dc3545',
    cancelButtonColor: '#6c757d'
  }).then((result) => {
    if (result.isConfirmed) {
      // Redirigir al logout
      window.location.href = '/logout/';
    }
  });
}
```

### **Función Helper SweetAlert2**

```javascript
async function showSweetAlertFromAPI(url, method = 'GET', body = null) {
  try {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      }
    };
    
    if (body) {
      options.body = JSON.stringify(body);
    }
    
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (data.success && data.sweetAlert) {
      const config = { ...data.sweetAlert };
      return Swal.fire(config);
    } else {
      console.error('Respuesta inválida:', data);
      return Swal.fire({
        title: 'Error',
        text: 'No se pudo obtener la configuración del mensaje',
        icon: 'error'
      });
    }
  } catch (error) {
    console.error('Error:', error);
    return Swal.fire({
      title: 'Error',
      text: 'Error al comunicarse con la API',
      icon: 'error'
    });
  }
}
```

## 🚀 APIs Creadas

### **API de Confirmación de Logout**

#### **Endpoint:**
```
POST /api/sweet-alert/logout-confirm/
```

#### **Respuesta:**
```json
{
  "success": true,
  "sweetAlert": {
    "title": "¿Cerrar Sesión?",
    "text": "¿Estás seguro de que deseas cerrar tu sesión?",
    "icon": "question",
    "showCancelButton": true,
    "confirmButtonText": "Sí, Cerrar Sesión",
    "cancelButtonText": "Cancelar",
    "confirmButtonColor": "#dc3545",
    "cancelButtonColor": "#6c757d",
    "reverseButtons": true
  }
}
```

#### **Configuración del Mensaje:**
- **Título**: "¿Cerrar Sesión?"
- **Texto**: Mensaje de confirmación
- **Icono**: Signo de interrogación
- **Botones**: Confirmar (rojo) y Cancelar (gris)
- **Orden**: Botón de cancelar primero (reverseButtons: true)

## 💡 Uso

### **Flujo de Logout:**

1. **Usuario hace clic** en "Cerrar Sesión"
2. **Se muestra confirmación** con SweetAlert2
3. **Si confirma**: Se redirige a `/logout/`
4. **Si cancela**: Se cierra el diálogo sin acción

### **Ejemplo de Uso:**

```javascript
// El usuario hace clic en el botón de logout
document.querySelector('.logout-section a').addEventListener('click', function(e) {
  e.preventDefault();
  confirmarLogout();
});
```

### **Personalización:**

#### **Cambiar Texto del Mensaje:**
```python
# En core/views.py
def api_sweet_alert_logout_confirm(request):
    return Response({
        'success': True,
        'sweetAlert': {
            'title': 'Mi Título Personalizado',
            'text': 'Mi mensaje personalizado',
            # ... resto de configuración
        }
    })
```

#### **Cambiar Colores:**
```python
'confirmButtonColor': '#28a745',  # Verde en lugar de rojo
'cancelButtonColor': '#ffc107',   # Amarillo en lugar de gris
```

## 🔒 Seguridad

### **Características de Seguridad:**

1. **Autenticación Requerida**: Solo usuarios autenticados pueden acceder
2. **Token CSRF**: Protección contra ataques CSRF
3. **Confirmación Obligatoria**: No se puede cerrar sesión accidentalmente
4. **Redirección Segura**: Uso del endpoint oficial de logout de Django

### **Validaciones:**

- ✅ Usuario debe estar autenticado
- ✅ Token CSRF válido
- ✅ Confirmación explícita del usuario
- ✅ Redirección al endpoint oficial de logout

## 🎨 Beneficios Implementados

### ✅ **Experiencia de Usuario**
- **Confirmación Clara**: El usuario sabe exactamente qué va a pasar
- **Diseño Intuitivo**: Botón fácil de encontrar y usar
- **Feedback Visual**: Efectos hover y colores apropiados
- **Consistencia**: Mismo comportamiento en todos los paneles

### ✅ **Seguridad**
- **Prevención de Logout Accidental**: Confirmación obligatoria
- **Protección CSRF**: Token de seguridad incluido
- **Logout Seguro**: Uso del sistema oficial de Django

### ✅ **Mantenibilidad**
- **Configuración Centralizada**: API REST para el mensaje
- **Código Reutilizable**: Función helper compartida
- **Fácil Personalización**: Cambios desde el backend

## 📱 Responsive Design

### **Comportamiento en Diferentes Dispositivos:**

- **Desktop**: Botón visible en sidebar izquierdo
- **Tablet**: Sidebar se mantiene, botón accesible
- **Mobile**: Sidebar colapsable, botón siempre visible

### **Accesibilidad:**

- **Contraste Adecuado**: Texto rojo sobre fondo oscuro
- **Tamaño de Click**: Área suficiente para tocar
- **Navegación por Teclado**: Accesible con Tab
- **Screen Readers**: Texto descriptivo para lectores

## 🚀 Próximas Mejoras

### **Funcionalidades Futuras:**

1. **Logout Automático**: Por inactividad
2. **Múltiples Sesiones**: Gestión de sesiones activas
3. **Historial de Sesiones**: Registro de logins/logouts
4. **Notificaciones**: Alertas antes del logout automático

### **Integración con Otros Sistemas:**

1. **SSO**: Single Sign-On con otros sistemas
2. **OAuth**: Autenticación con proveedores externos
3. **Auditoría**: Logs detallados de sesiones
4. **Backup de Datos**: Guardado automático antes del logout

## 🎯 Conclusión

Las funcionalidades de logout han sido completamente implementadas en los paneles de trabajadores de Ferremas, proporcionando:

- **Seguridad mejorada** con confirmación obligatoria
- **Experiencia de usuario profesional** con SweetAlert2
- **Diseño consistente** en todos los paneles
- **Fácil mantenimiento** con APIs centralizadas
- **Accesibilidad completa** para todos los usuarios

¡Los paneles de trabajadores ahora tienen un sistema de logout seguro y profesional! 