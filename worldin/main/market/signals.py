from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import RentalFeature

@receiver(post_migrate)
def create_default_features(sender, **kwargs):
    features = ['Cocina equipada', 'Cuarto de baño completo', 'Aseo', 'Armarios empotrados', 'Terraza', 'Salón', 
               'TV', 'Comedor', 'Balcón', 'Solarium', 'Cerca de supermercados', 'Cerca de centro de salud', 
               'Bien comunicado con transporte público', 'Buenos vecinos', 'Con ascensor', 'Con bañera', 'Buena iluminación', 
                'Admite mascotas', 'Se puede fumar', 'Piscina comunitaria', 'Zona de aparcamiento', 'Zona de juegos infantiles']
    
    for feature_name in features:
        RentalFeature.objects.get_or_create(feature=feature_name)