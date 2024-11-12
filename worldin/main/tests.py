from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Hobby, FollowRequest, CustomUser
from worldin.forms import CustomUserCreationForm, CustomAuthenticationForm

User = get_user_model()

class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='testuser@example.com',
            is_active=False  # Usuario inactivo inicialmente
        )
        self.user_with_profile = User.objects.create_user(
            username='activeuser',
            password='testpassword',
            email='activeuser@example.com',
            birthday='2000-01-01',
            city='Test City',
            description='Test description',
            profile_picture='path/to/picture.jpg'
        )
        self.hobby1 = Hobby.objects.create(name='Hobby 1')
        self.hobby2 = Hobby.objects.create(name='Hobby 2')

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_contact_us_view(self):
        response = self.client.get(reverse('contact_us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact_us.html')

    def test_policy_view(self):
        response = self.client.get(reverse('policy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'policy.html')

    def test_usage_view(self):
        response = self.client.get(reverse('usage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usage.html')

    # def test_login_user_view_valid(self):
    #     self.client.post(reverse('register'), {
    #         'username': 'prueba',
    #         'password': 'dificillacontra598'
    #     })

    #     response = self.client.post(reverse('login'), {
    #         'username': 'prueba',
    #         'password': 'dificillacontra598'
    #     })
    #     self.assertEqual(response.status_code, 302)  # Redirección
    #     self.assertRedirects(response, reverse('world'))


    def test_login_user_view_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Debe permanecer en la página de inicio de sesión
        self.assertTemplateUsed(response, 'login.html')

    def test_register_view_valid(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'passdificil478',
            'password2': 'passdificil478'
        })
        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertRedirects(response, reverse('confirm_account'))

    def test_register_view_invalid(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassword',
            'password2': 'differentpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    # def test_confirm_account_view_success(self):
    #     # Crear un usuario y simular su registro
    #     user = CustomUser.objects.create_user(
    #         username='newuser',
    #         email='newuser@example.com',
    #         password='newpassword456'
    #     )
    #     user.is_active = False  # Asegurarse de que la cuenta esté desactivada inicialmente
    #     user.save()

    #     # Generar el código de confirmación y agregarlo a la sesión
    #     confirmation_code = '123456'
    #     self.client.session['confirmation_code'] = confirmation_code
    #     self.client.session['user_id'] = user.id
    #     self.client.session.save()  # Guarda la sesión después de haber añadido los valores

    #     # Realizar la confirmación de cuenta
    #     response = self.client.post(reverse('confirm_account'), {
    #         'code': confirmation_code
    #     })

    #     # Verificar que la respuesta sea una redirección
    #     self.assertEqual(response.status_code, 302)
    #     self.assertRedirects(response, reverse('world'))

        # Verificar que el usuario ahora está activo
        # user.refresh_from_db()
        # self.assertTrue(user.is_active)



    def test_confirm_account_view_failure(self):
        response = self.client.post(reverse('confirm_account'), {
            'code': 'wrongcode'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'confirm_account.html')

    def test_logout_view(self):
        self.client.login(username='activeuser', password='testpassword')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertRedirects(response, reverse('home'))

    def test_world_page_view_authenticated(self):
        self.client.login(username='activeuser', password='testpassword')
        response = self.client.get(reverse('world'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'world.html')

    def test_world_page_view_unauthenticated(self):
        response = self.client.get(reverse('world'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'world.html')

    def test_profile_view(self):
        self.client.login(username='activeuser', password='testpassword')
        response = self.client.get(reverse('my_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_profile.html')

    def test_edit_profile_view(self):
        self.client.login(username='activeuser', password='testpassword')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_profile.html')

    def test_profile_settings_view(self):
        self.client.login(username='activeuser', password='testpassword')
        response = self.client.get(reverse('profile_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_settings.html')

    def test_delete_account_view(self):
        self.client.login(username='activeuser', password='testpassword')
        response = self.client.get(reverse('delete_account'))
        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertRedirects(response, reverse('home'))

