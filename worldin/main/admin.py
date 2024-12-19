from django.contrib import admin
from .models import CustomUser, Follow

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'email')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'username')  # Campos para búsqueda.


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'username')  # Campos para búsqueda.