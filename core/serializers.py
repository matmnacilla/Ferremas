from rest_framework import serializers
from .models import Venta, DetalleVenta, Producto
from django.contrib.auth.models import User

class ProductoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'codigo']

class DetalleVentaSerializer(serializers.ModelSerializer):
    producto = ProductoSimpleSerializer()
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']

class VentaSerializer(serializers.ModelSerializer):
    cliente = serializers.SerializerMethodField()
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = [
            'id', 'fecha', 'cliente', 'direccion_entrega', 'ciudad', 'telefono_contacto',
            'total', 'estado', 'metodo_pago', 'notas', 'detalles'
        ]

    def get_cliente(self, obj):
        return obj.cliente.get_full_name() or obj.cliente.username