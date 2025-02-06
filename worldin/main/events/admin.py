from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'title', 'location', 'start', 'end', 'price', 'dresscode')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'title', 'start')  # Campos para búsqueda.