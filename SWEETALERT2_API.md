# SweetAlert2 API - Ferremas

## 📋 Descripción

Este documento describe la API unificada de SweetAlert2 implementada en el sistema Ferremas para mostrar alertas y notificaciones interactivas.

## 🎯 API Unificada

### Endpoint Principal

**`POST /api/sweet-alert/`**

Esta es la única API de SweetAlert2 disponible. Recibe cualquier configuración de SweetAlert2 y la devuelve para ser mostrada en el frontend.

### Parámetros

La API acepta cualquier parámetro válido de SweetAlert2:

```json
{
  "title": "Título del mensaje",
  "text": "Texto del mensaje",
  "icon": "success|error|warning|info|question",
  "showCancelButton": true,
  "confirmButtonText": "Aceptar",
  "cancelButtonText": "Cancelar",
  "timer": 3000,
  "timerProgressBar": true,
  "showConfirmButton": false
}
```

### Respuesta

```json
{
  "success": true,
  "sweetAlert": {
    // Configuración de SweetAlert2
  }
}
```

## 🔧 Uso en el Frontend

### Método Directo (Recomendado)

Para la mayoría de casos, es mejor usar SweetAlert2 directamente:

```javascript
// Mensaje de éxito
Swal.fire({
  title: '¡Éxito!',
  text: 'Operación completada correctamente',
  icon: 'success',
  timer: 1500,
  timerProgressBar: true,
  showConfirmButton: false
});

// Confirmación
Swal.fire({
  title: '¿Estás seguro?',
  text: 'Esta acción no se puede deshacer',
  icon: 'question',
  showCancelButton: true,
  confirmButtonText: 'Sí, continuar',
  cancelButtonText: 'Cancelar',
  confirmButtonColor: '#dc3545',
  cancelButtonColor: '#6c757d'
}).then((result) => {
  if (result.isConfirmed) {
    // Acción confirmada
  }
});
```

### Método con API (Para casos complejos)

Para casos que requieren lógica del servidor:

```javascript
// Función helper para usar la API unificada
async function showSweetAlertFromAPI(config) {
  try {
    const response = await fetch('/api/sweet-alert/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      },
      body: JSON.stringify(config)
    });
    
    const data = await response.json();
    
    if (data.success && data.sweetAlert) {
      return Swal.fire(data.sweetAlert);
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

// Ejemplo de uso
showSweetAlertFromAPI({
  title: 'Mensaje Personalizado',
  text: 'Este mensaje viene del servidor',
  icon: 'info',
  timer: 2000
});
```

## 📝 Ejemplos Comunes

### 1. Mensaje de Éxito
```javascript
Swal.fire({
  title: '¡Éxito!',
  text: 'Operación completada correctamente',
  icon: 'success',
  timer: 1500,
  timerProgressBar: true,
  showConfirmButton: false
});
```

### 2. Confirmación de Eliminación
```javascript
Swal.fire({
  title: '¿Eliminar?',
  text: '¿Estás seguro de que deseas eliminar este elemento?',
  icon: 'question',
  showCancelButton: true,
  confirmButtonText: 'Sí, eliminar',
  cancelButtonText: 'Cancelar',
  confirmButtonColor: '#dc3545',
  cancelButtonColor: '#6c757d'
}).then((result) => {
  if (result.isConfirmed) {
    // Proceder con la eliminación
  }
});
```

### 3. Mensaje de Error
```javascript
Swal.fire({
  title: 'Error',
  text: 'Ocurrió un error durante la operación',
  icon: 'error',
  confirmButtonText: 'Entendido'
});
```

### 4. Notificación Toast
```javascript
Swal.fire({
  toast: true,
  position: 'top-end',
  title: 'Notificación',
  text: 'Mensaje de notificación',
  icon: 'success',
  showConfirmButton: false,
  timer: 3000,
  timerProgressBar: true
});
```

## 🚀 Migración

### Antes (APIs específicas eliminadas)
```javascript
// ❌ Ya no funciona
showSweetAlertFromAPI('/api/sweet-alert/success/', 'POST');
showSweetAlertFromAPI('/api/sweet-alert/question/', 'POST');
```

### Después (Método directo)
```javascript
// ✅ Funciona correctamente
Swal.fire({
  title: '¡Éxito!',
  text: 'Operación completada',
  icon: 'success',
  timer: 1500
});
```

## 📚 Referencias

- [SweetAlert2 Documentation](https://sweetalert2.github.io/)
- [SweetAlert2 Options](https://sweetalert2.github.io/#configuration)
- [SweetAlert2 Examples](https://sweetalert2.github.io/#examples)

## 🔄 Historial de Cambios

- **v2.0**: Eliminadas todas las APIs específicas, solo queda la API unificada
- **v1.0**: Implementación inicial con múltiples APIs específicas 