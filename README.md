# Ferremas - Sistema de Gestión para Ferretería

Sistema web desarrollado en Django para la gestión de una ferretería, incluyendo catálogo de productos, sistema de ofertas, carrito de compras y panel de administración.

## Características Principales

- 🛍️ Catálogo de productos con filtros por categoría y precio
- 🏷️ Sistema de ofertas y descuentos
- 🛒 Carrito de compras
- 👥 Gestión de usuarios (clientes, vendedores, bodegueros)
- 📊 Panel de administración
- 📦 Control de inventario
- 💰 Gestión de ventas

## Requisitos

- Python 3.8 o superior
- Django 5.2
- Bootstrap 5
- PostgreSQL (recomendado para producción)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/ferremas.git
cd ferremas
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar la base de datos:
```bash
python manage.py migrate
```

5. Crear superusuario:
```bash
python manage.py createsuperuser
```

6. Iniciar el servidor de desarrollo:
```bash
python manage.py runserver
```

## Estructura del Proyecto

```
ferremas/
├── core/               # Aplicación principal
│   ├── models.py      # Modelos de datos
│   ├── views.py       # Vistas y lógica de negocio
│   └── templates/     # Plantillas HTML
├── static/            # Archivos estáticos (CSS, JS, imágenes)
├── media/             # Archivos subidos por usuarios
└── manage.py          # Script de administración de Django
```

## Roles de Usuario

- **Cliente**: Puede ver el catálogo, agregar productos al carrito y realizar compras
- **Vendedor**: Gestiona ventas y atiende clientes
- **Bodeguero**: Administra el inventario y stock
- **Administrador**: Acceso completo al sistema

## Contribuir

1. Haz un Fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tutwitter](https://twitter.com/tutwitter) - email@ejemplo.com

Link del Proyecto: [https://github.com/tu-usuario/ferremas](https://github.com/tu-usuario/ferremas) 