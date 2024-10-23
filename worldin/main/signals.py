from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Hobby

@receiver(post_migrate)
def create_default_hobbies(sender, **kwargs):
    hobbies = ['Deportes', 'Cine', 'Fiesta', 'Cerveza', 'Salir con amigos', 'Gimnasio', 
               'Nutrición', 'Viajar', 'Coches', 'Motos', 'Perros', 'Gatos', 'Netflix & chill', 'Videojuegos',
               'Siesta', 'Tiempo en familia', 'Comer', 'Fútbol', 'Baloncesto', 'Tenis']
    
    for hobby_name in hobbies:
        Hobby.objects.get_or_create(name=hobby_name)
