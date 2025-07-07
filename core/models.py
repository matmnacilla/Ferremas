from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, unique=True)
    precio = models.IntegerField(
        validators=[MinValueValidator(0, message='El precio no puede ser negativo')]
    )
    precio_oferta = models.IntegerField(null=True, blank=True)
    stock = models.IntegerField(
        validators=[MinValueValidator(0, message='El stock no puede ser negativo')]
    )
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def en_oferta(self):
        return self.precio_oferta is not None and self.precio_oferta < self.precio
    
    def precio_actual(self):
        return self.precio_oferta if self.en_oferta() else self.precio
    
    def porcentaje_descuento(self):
        if self.en_oferta():
            return int(((self.precio - self.precio_oferta) / self.precio) * 100)
        return 0

    def clean(self):
        if self.precio < 0:
            raise ValidationError({'precio': 'El precio no puede ser negativo'})
        if self.stock < 0:
            raise ValidationError({'stock': 'El stock no puede ser negativo'})
        if self.precio_oferta is not None:
            if self.precio_oferta < 0:
                raise ValidationError({'precio_oferta': 'El precio de oferta no puede ser negativo'})
            if self.precio_oferta >= self.precio:
                raise ValidationError({'precio_oferta': 'El precio de oferta debe ser menor al precio normal'})
        
    def save(self, *args, **kwargs):
        self.full_clean()  # Validar antes de guardar
        super().save(*args, **kwargs)

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=15)
    email = models.EmailField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
    
    def __str__(self):
        return self.nombre

class Promocion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    descuento = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    productos = models.ManyToManyField(Producto, related_name='promociones')
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
    
    def __str__(self):
        return self.nombre
    
    def esta_activa(self):
        ahora = timezone.now()
        return self.activa and self.fecha_inicio <= ahora <= self.fecha_fin

class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'
    
    def __str__(self):
        return f"Carrito de {self.usuario.username}"
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Item del Carrito'
        verbose_name_plural = 'Items del Carrito'
        unique_together = ['carrito', 'producto']
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    @property
    def subtotal(self):
        return self.producto.precio_actual() * self.cantidad

class Venta(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('preparada', 'Preparada'),
        ('enviada', 'Enviada'),
        ('entregada', 'Entregada'),
        ('cancelada', 'Cancelada'),
    ]
    
    METODOS_PAGO = [
        ('paypal', 'PayPal'),
    ]
    
    PRIORIDADES = [
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    cliente = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='paypal')
    direccion_entrega = models.TextField()
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    telefono_contacto = models.CharField(max_length=15, null=True, blank=True)
    total = models.IntegerField()
    notas = models.TextField(blank=True)
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='normal')
    fecha_limite_entrega = models.DateTimeField(null=True, blank=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_actualizadas'
    )
    aceptada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_aceptadas'
    )
    fecha_aceptacion = models.DateTimeField(null=True, blank=True)
    
    # Campos para PayPal
    paypal_payment_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_payer_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paypal_payment_status = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-prioridad', '-fecha']
    
    def __str__(self):
        return f"Venta #{self.id} - {self.cliente.username}"
    
    def actualizar_estado_paypal(self, payment_id, payer_id, transaction_id, status):
        """Actualiza la información de PayPal en la venta"""
        self.paypal_payment_id = payment_id
        self.paypal_payer_id = payer_id
        self.paypal_transaction_id = transaction_id
        self.paypal_payment_status = status
        if status == 'completed':
            self.estado = 'confirmada'
        self.save()
    
    def calcular_prioridad(self):
        """Calcula la prioridad del pedido basado en diferentes factores"""
        if self.estado == 'cancelada':
            return 'normal'
            
        # Si tiene fecha límite y está cerca
        if self.fecha_limite_entrega:
            tiempo_restante = self.fecha_limite_entrega - timezone.now()
            if tiempo_restante.total_seconds() < 3600:  # Menos de 1 hora
                return 'urgente'
            elif tiempo_restante.total_seconds() < 86400:  # Menos de 24 horas
                return 'alta'
        
        # Si lleva más de 24 horas en el mismo estado
        tiempo_en_estado = timezone.now() - self.ultima_actualizacion
        if tiempo_en_estado.total_seconds() > 86400:  # Más de 24 horas
            return 'alta'
            
        return 'normal'

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.IntegerField()
    subtotal = models.IntegerField()
    
    # Campos para el proceso de preparación
    preparado = models.BooleanField(default=False)
    fecha_preparacion = models.DateTimeField(null=True, blank=True)
    preparado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos_preparados'
    )
    ubicacion_bodega = models.CharField(max_length=100, null=True, blank=True)
    notas_preparacion = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
    
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad} - Venta #{self.venta.id}"
    
    def marcar_preparado(self, usuario, notas=''):
        """Marca el producto como preparado y registra la información"""
        self.preparado = True
        self.fecha_preparacion = timezone.now()
        self.preparado_por = usuario
        self.notas_preparacion = notas
        self.save()
        
        # Verificar si todos los productos están preparados
        todos_preparados = not DetalleVenta.objects.filter(
            venta=self.venta,
            preparado=False
        ).exists()
        
        if todos_preparados and self.venta.estado == 'confirmada':
            self.venta.estado = 'enviada'
            self.venta.actualizado_por = usuario
            self.venta.save()
            
            # Crear notificación
            Notificacion.objects.create(
                usuario=self.venta.cliente,
                tipo='pedido',
                mensaje=f'Tu pedido #{self.venta.id} ha sido preparado y está listo para envío'
            )
        
        return todos_preparados

class Empleado(models.Model):
    DEPARTAMENTOS = [
        ('ventas', 'Ventas'),
        ('bodega', 'Bodega'),
        ('administracion', 'Administración'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    departamento = models.CharField(max_length=20, choices=DEPARTAMENTOS)
    cargo = models.CharField(max_length=50)
    telefono = models.CharField(max_length=15)
    fecha_contratacion = models.DateField(auto_now_add=True)
    fecha_termino = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    comision = models.IntegerField(default=0)
    debe_cambiar_password = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.cargo}"
    
    @property
    def ventas_mes(self):
        mes_actual = timezone.now().month
        return Venta.objects.filter(
            fecha__month=mes_actual,
            estado='entregada'
        ).count()

class Turno(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    tipo = models.CharField(max_length=20, choices=[
        ('mañana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('noche', 'Noche'),
    ])
    
    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
    
    def __str__(self):
        return f"Turno de {self.empleado} - {self.fecha_inicio.date()}"

class Notificacion(models.Model):
    TIPOS = [
        ('stock', 'Stock Bajo'),
        ('venta', 'Nueva Venta'),
        ('promocion', 'Promoción'),
        ('sistema', 'Sistema'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.tipo} - {self.usuario.username}"
