from django.contrib import admin
from .models import *
from django.core.exceptions import ValidationError
from django import forms

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    search_fields = ('nombre',)
    list_filter = ('activa',)

class ProductoAdminForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'precio': forms.NumberInput(attrs={'min': '0', 'step': '1'}),
            'precio_anterior': forms.NumberInput(attrs={'min': '0', 'step': '1'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'min': '0'}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio < 0:
            raise ValidationError('El precio no puede ser negativo')
        return precio

    def clean_precio_anterior(self):
        precio_anterior = self.cleaned_data.get('precio_anterior')
        if precio_anterior is not None and precio_anterior < 0:
            raise ValidationError('El precio anterior no puede ser negativo')
        return precio_anterior

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock < 0:
            raise ValidationError('El stock no puede ser negativo')
        return stock

    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get('stock_minimo')
        if stock_minimo < 0:
            raise ValidationError('El stock mínimo no puede ser negativo')
        return stock_minimo

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoAdminForm
    list_display = ('nombre', 'categoria', 'precio', 'stock', 'stock_minimo', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'codigo', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    list_editable = ('precio', 'stock', 'activo')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['precio'].label = 'Precio ($)'
        form.base_fields['precio_anterior'].label = 'Precio Anterior ($)'
        return form

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'email', 'activo')
    search_fields = ('nombre', 'rut', 'email')
    list_filter = ('activo',)

@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descuento', 'fecha_inicio', 'fecha_fin', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)
    filter_horizontal = ('productos',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'total', 'estado', 'metodo_pago')
    list_filter = ('estado', 'metodo_pago', 'fecha')
    search_fields = ('cliente__username', 'id')
    readonly_fields = ('fecha',)

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'departamento', 'cargo', 'telefono', 'activo')
    list_filter = ('departamento', 'activo')
    search_fields = ('usuario__username', 'cargo')

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_inicio', 'fecha_fin', 'tipo')
    list_filter = ('tipo', 'fecha_inicio')
    search_fields = ('empleado__usuario__username',)

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'mensaje', 'leida', 'fecha')
    list_filter = ('tipo', 'leida', 'fecha')
    search_fields = ('usuario__username', 'mensaje')
