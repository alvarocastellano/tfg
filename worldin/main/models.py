from django.db import models
from django.contrib.auth.models import AbstractUser,Group, Permission

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    birthday = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    erasmus = models.BooleanField(default=False)
    
    # Agrega el argumento related_name para evitar conflictos con los atributos inversos
    groups = models.ManyToManyField(Group, verbose_name='groups', blank=True, related_name='customuser_set')
    user_permissions = models.ManyToManyField(Permission, verbose_name='user permissions', blank=True, related_name='customuser_set')
