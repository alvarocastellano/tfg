from django.conf import settings
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
    selected_city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    erasmus = models.BooleanField(default=False)
    show_age = models.BooleanField(default=True) 
    profile_completed = models.BooleanField(default=False)
    account_visibility = models.CharField(max_length=10, choices=[('public', 'Pública'), ('private', 'Privada')], default='public')
    see_own_products = models.BooleanField(default=False)
    aficiones = models.ManyToManyField(Hobby, blank=True)
    is_city_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, verbose_name='groups', blank=True, related_name='customuser_set')
    user_permissions = models.ManyToManyField(Permission, verbose_name='user permissions', blank=True, related_name='customuser_set')

class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')  # Un usuario no puede seguir al mismo usuario más de una vez

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
class FollowRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_requests_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_requests_received', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pendiente'),
            ('accepted', 'Aceptada'),
            ('rejected', 'Rechazada')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username} solicita seguir a {self.receiver.username}"

    
