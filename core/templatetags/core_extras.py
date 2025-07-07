from django import template
from decimal import Decimal
import decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Multiplica el valor por el argumento.
    Útil para convertir CLP a USD en las plantillas.
    
    Ejemplo de uso:
    {{ precio_clp|multiply:0.001 }}  # Convierte CLP a USD
    """
    try:
        # Convertir a Decimal para mayor precisión en cálculos monetarios
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return ''

@register.filter
def format_currency(value, currency='CLP'):
    """
    Formatea un valor numérico como moneda.
    
    Ejemplo de uso:
    {{ precio|format_currency }}  # Muestra como CLP
    {{ precio|format_currency:'USD' }}  # Muestra como USD
    """
    try:
        value = Decimal(str(value))
        if currency == 'USD':
            return f"${value:.2f} USD"
        else:
            return f"${value:,.0f} CLP"
    except (ValueError, TypeError, decimal.InvalidOperation):
        return ''
