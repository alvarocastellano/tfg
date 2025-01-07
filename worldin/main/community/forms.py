from django import forms
from .models import GroupChat

class EditGroupForm(forms.ModelForm):
    class Meta:
        model = GroupChat
        fields = ['name', 'image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
