from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# Modelo para representar una afición
class Hobby(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    birthday = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    erasmus = models.BooleanField(default=False)
    show_age = models.BooleanField(default=True)  # Nuevo campo para mostrar edad
    account_visibility = models.CharField(
        max_length=10,
        choices=[
            ('public', 'Pública'),
            ('private', 'Privada')
        ],
        default='public'
    )  # Nuevo campo para visibilidad de la cuenta

    # Relación Many-to-Many con el modelo Hobby
    aficiones = models.ManyToManyField(Hobby, blank=True)

    # Agrega el argumento related_name para evitar conflictos con los atributos inversos
    groups = models.ManyToManyField(Group, verbose_name='groups', blank=True, related_name='customuser_set')
    user_permissions = models.ManyToManyField(Permission, verbose_name='user permissions', blank=True, related_name='customuser_set')


# Modelo para gestionar la relación de seguimiento entre usuarios
class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('follower', 'following')  # Asegura que un usuario no pueda seguir a otro más de una vez

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"