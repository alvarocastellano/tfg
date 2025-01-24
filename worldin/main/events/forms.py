from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start', 'end', 'price', 'dresscode', 'tickets_link', 'max_people']
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'location': 'Ubicación',
            'start': 'Fecha y hora de inicio',
            'end': 'Fecha y hora de fin',
            'price': 'Precio',
            'dresscode': 'Código de vestimenta',
            'tickets_link': 'Enlace de compra de entradas',
            'max_people': 'Límite de participantes',
        }
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
