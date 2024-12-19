from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'email')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'username')  # Campos para búsqueda.

