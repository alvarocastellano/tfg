from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from main.models import CustomUser
from django.contrib.auth import authenticate
from django.core.validators import EmailValidator, MinLengthValidator

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label='Email', validators=[EmailValidator('Invalid email format')])
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput, validators=[MinLengthValidator(8, 'La contraseña debe tener al menos 8 caracteres')])
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'birthday', 'city', 'description', 'profile_picture']


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        try:
            user = authenticate(self.request, username=username, password=password)
        except Exception as e:
            raise forms.ValidationError(
                str(e),
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

        if user is None:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

        return self.cleaned_data
    
class CityForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['selected_city']
    


