from django.db.models import Sum
from .models import Carrito, CarritoItem

def carrito_context(request):
    context = {
        'total_items_carrito': 0,
        'total_carrito': 0
    }
    
    if request.user.is_authenticated:
        try:
            carrito = Carrito.objects.get(usuario=request.user)
            # Obtener el total de items usando agregación
            total_items = CarritoItem.objects.filter(carrito=carrito).aggregate(
                total=Sum('cantidad')
            )['total'] or 0
            
            # Obtener el total del carrito usando el método total del modelo Carrito
            total_carrito = carrito.total
            
            context.update({
                'total_items_carrito': total_items,
                'total_carrito': total_carrito
            })
        except Carrito.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error en carrito_context: {str(e)}")
    
    return context 