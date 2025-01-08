from django import forms
from .models import GroupChat

class EditGroupForm(forms.ModelForm):
    class Meta:
        model = GroupChat
        fields = ['name', 'image', 'description']
        labels = {
            'name': 'Nombre del grupo',
            'image': 'Imagen del grupo',
            'description': 'Descripción del grupo',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

