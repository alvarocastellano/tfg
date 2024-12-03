import json
from django.test import TestCase
from django.urls import reverse
from .models import Follow, FollowRequest, Hobby, CustomUser
from main.market.models import Product, Rental
from datetime import date, datetime, timedelta



class TestUsuarioRegistro(TestCase):
    def setUp(self):
        self.register_url = reverse('register')

    def test_registro_usuario(self):
        data = {
            'username': 'usuario1',
            'first_name': 'Pedro',
            'last_name': 'Ramos',
            'email': 'usuario1@example.com',
            'password': 'password123',
            'password2': 'password123',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)

    def test_registro_cliente_datos_invalidos(self):
        data = {
            'username': 'usuario2',
            'first_name': 'Ana',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200) 
        self.assertFalse(CustomUser.objects.filter(username='usuario2').exists())

        # passwords no coinciden
        data = {
            'username': 'usuario2',
            'first_name': 'Ana',
            'last_name': 'Alonso',
            'email': 'usuario2@example.com',
            'password': 'password123',
            'password2': 'password456',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='usuario2').exists())

class AccountConfirmationTestCase(TestCase):
    def setUp(self):
        # Crear un usuario desactivado
        self.usuario = CustomUser.objects.create_user(
            username='usuario',
            email='usuario@example.com',
            password='testpassword123',
            is_active=False,  # El usuario debe estar inactivo al registrarse
        )
        self.confirmation_code = '123456'

        # Configurar sesión en el cliente de pruebas
        session = self.client.session
        session['confirmation_code'] = self.confirmation_code
        session['user_id'] = self.usuario.id
        session.save()

    def test_account_activation(self):
        # Hacer una solicitud POST con el código correcto
        response = self.client.post(reverse('confirm_account'), {'code': self.confirmation_code})
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)  # Debe redirigir a 'world'

        # Verificar que el usuario está activo
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_active)

        # Verificar que el código de confirmación se eliminó de la sesión
        session = self.client.session
        self.assertNotIn('confirmation_code', session)
        self.assertNotIn('user_id', session)


class TestUsuarioLogin(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='usuario1', email='usuario1@example.com', password='password123')
        self.login_url = reverse('login')

    def test_login_cliente(self):
        data = {
            'username': 'usuario1',
            'email': 'usuario1@example.com',
            'password': 'password123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)

    def test_redirect_login_required(self):
        response = self.client.get(reverse('world'))
        self.assertEqual(response.status_code, 200)

class StaticTemplatesViewTests(TestCase):
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

    def test_password_reset_view(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'password_reset.html')

    def test_my_market_ratings_view(self):
        response = self.client.get(reverse('market:my_market_ratings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_market_ratings.html')

class WorldPageViewTests(TestCase):
    def setUp(self):

        self.hobby1 = Hobby.objects.create(name='Hobby1')
        self.hobby2 = Hobby.objects.create(name='Hobby2')

        self.user = CustomUser.objects.create_user(
            username='usuario1',
            first_name = 'usuario de',
            last_name = 'prueba',
            email='usuario1@example.com',
            password='password123',
            city='Madrid',
            description = 'test description',
            birthday = date(2001,7,26),
            profile_picture = "profile_pictures/imagen_de_contacto.jpg",
        )

        self.user.aficiones.set([self.hobby1, self.hobby2])
        

        self.url = reverse('world')

    def test_world_page_anonymous_user(self):
        # Probar la vista con un usuario anónimo
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'world.html')
        self.assertIsNone(response.context['user_city'])
        self.assertEqual(response.context['total_alerts'], 0)

    def test_world_page_authenticated_user_complete_profile(self):
        # Probar la vista con un usuario autenticado con perfil completo
        self.client.login(username='usuario1', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'world.html')
        self.assertEqual(response.context['user_city'], 'Madrid')
        self.assertEqual(response.context['total_alerts'], 0)  # No alertas

    def test_world_page_authenticated_user_incomplete_profile(self):
        # Probar la vista con un usuario autenticado con perfil incompleto
        self.user.city = ''
        self.user.save()
        self.client.login(username='usuario1', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'world.html')
        self.assertIsNone(response.context['user_city'])
        self.assertEqual(response.context['total_alerts'], 1)

class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='usuario1', email='usuario1@example.com', password='password123')
        
    def test_my_profile_detail_view(self):
        is_logged = self.client.login(username='usuario1', password='password123')
        self.assertTrue(is_logged)
        
        response = self.client.get(reverse('my_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_profile.html')
        self.assertEqual(response.context['user'], self.user)
    
    def tearDown(self):
        self.user.delete()

class EditProfileViewTestCase(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        # Crear hobbies disponibles
        self.hobby1 = Hobby.objects.create(name='Hobby1')
        self.hobby2 = Hobby.objects.create(name='Hobby2')
        self.hobby3 = Hobby.objects.create(name='Hobby3')
        self.hobby4 = Hobby.objects.create(name='Hobby4')
        self.hobby5 = Hobby.objects.create(name='Hobby5')
        self.hobby6 = Hobby.objects.create(name='Hobby6')
        self.hobby7 = Hobby.objects.create(name='Hobby7')
        self.hobby8 = Hobby.objects.create(name='Hobby8')

        self.user.save()

    def test_edit_profile_view_access(self):
        # Verificar acceso a la vista
        self.client.login(username='usuario1', password='password123')
        response = self.client.get(reverse('edit_profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_profile.html')


    def test_edit_profile_invalid_birthday_future(self):
        # Intentar establecer una fecha de nacimiento futura
        original_birthday = self.user.birthday
        future_birthday = (datetime.today() + timedelta(days=1)).date()
        self.client.login(username='usuario1', password='password123')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'usuario_actualizado',
            'birthday': future_birthday,
        })

        # Verificar que se muestra el mensaje de error
        self.assertEqual(response.status_code, 200)  # Renderiza de nuevo la página
        self.assertEqual(self.user.birthday, original_birthday)

    def test_edit_profile_invalid_birthday_under_14(self):
        original_birthday = self.user.birthday
        birthday_under_14 = (datetime.today() - timedelta(days=365 * 13)).date()
        self.client.login(username='usuario1', password='password123')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'usuario_actualizado',
            'birthday': birthday_under_14,
        })

        # Verificar que se muestra el mensaje de error
        self.assertEqual(response.status_code, 200)  # Renderiza de nuevo la página
        self.assertEqual(self.user.birthday, original_birthday)

    def test_edit_profile_invalid_birthday_over_100(self):
        original_birthday = self.user.birthday
        birthday_over_100 = (datetime.today() - timedelta(days=365 * 101)).date()
        self.client.login(username='usuario1', password='password123')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'usuario_actualizado',
            'birthday': birthday_over_100,
        })

        # Verificar que se muestra el mensaje de error
        self.assertEqual(response.status_code, 200)  # Renderiza de nuevo la página
        self.assertEqual(self.user.birthday, original_birthday)

    def test_edit_profile_invalid_birthday_format(self):
        # Intentar establecer una fecha con formato inválido
        self.client.login(username='usuario1', password='password123')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'usuario_actualizado',
            'birthday': '31-12-2000',  # Formato incorrecto
        })

        # Verificar que se muestra el mensaje de error
        self.assertEqual(response.status_code, 200)  # Renderiza de nuevo la página

    def test_edit_profile_successful_update(self):
        # Cambiar datos del perfil exitosamente
        self.client.login(username='usuario1', password='password123')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'usuario_actualizado',
            'email': 'nuevo_correo@example.com',
            'name': 'Nombre',
            'surname': 'Apellido',
            'birthday': '2000-01-01',
            'city': 'Nueva Ciudad',
            'description': 'Nueva descripción',
            'hobbies': [self.hobby1.id, self.hobby2.id],  # Seleccionar aficiones
        })

        self.assertEqual(response.status_code, 302)  # Redirige a 'my_profile'
        self.user.refresh_from_db()  # Recargar el usuario desde la base de datos

        # Verificar que los datos se actualizaron correctamente
        self.assertEqual(self.user.username, 'usuario_actualizado')
        self.assertEqual(self.user.email, 'nuevo_correo@example.com')
        self.assertEqual(self.user.first_name, 'Nombre')
        self.assertEqual(self.user.last_name, 'Apellido')
        self.assertEqual(self.user.city, 'Nueva Ciudad')
        self.assertEqual(self.user.description, 'Nueva descripción')
        self.assertEqual(self.user.birthday, datetime(2000, 1, 1).date())
        self.assertEqual(list(self.user.aficiones.all()), [self.hobby1, self.hobby2])

    def test_edit_profile_exceed_hobbies_limit(self):
        # Intentar seleccionar más de 7 hobbies
        self.client.login(username='usuario1', password='password123')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'usuario_actualizado',
            'hobbies': [self.hobby1.id, self.hobby2.id, self.hobby3.id, self.hobby4.id, self.hobby5.id, self.hobby6.id, self.hobby7.id, self.hobby8.id],
        })

        # Verificar que aparece el mensaje de error
        self.assertEqual(response.status_code, 200)  # Renderiza de nuevo la página
        self.assertContains(response, 'No puedes seleccionar más de 7 aficiones.')

    def test_edit_profile_duplicate_username(self):
        # Intentar cambiar a un nombre de usuario ya existente
        otro_usuario = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'usuario2',  # Nombre de usuario duplicado
        })

        # Verificar que aparece el mensaje de error
        self.assertEqual(response.status_code, 200)  # Renderiza de nuevo la página
        self.assertContains(response, 'El nombre de usuario ya está en uso.')

    def tearDown(self):
        # Eliminar datos creados durante los tests
        self.user.delete()
        Hobby.objects.all().delete()


class ProfileSettingsTestCase(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
            account_visibility = 'private',
        )
        self.client.login(username='usuario1', password='password123')
        self.url = reverse('profile_settings')

    def test_get_profile_settings(self):
        # Probar la carga inicial de la página de ajustes
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_settings.html')
        self.assertContains(response, 'CONFIGURACIÓN')  # Comprueba texto del template
        self.assertIn('has_pending_requests', response.context)
        self.assertFalse(response.context['has_pending_requests'])  # No debería haber solicitudes al inicio

    def test_post_profile_settings_update_visibility(self):
        # Probar cambio de visibilidad cuando no hay solicitudes pendientes
        response = self.client.post(self.url, {
            'account_visibility': 'public',
            'show_age': 'on',
            'see_own_products': 'on',
        })
        self.assertRedirects(response, reverse('my_profile'))

        # Comprobar que los cambios se guardaron en la base de datos
        self.user.refresh_from_db()
        self.assertEqual(self.user.account_visibility, 'public')
        self.assertTrue(self.user.show_age)
        self.assertTrue(self.user.see_own_products)

    def test_post_profile_settings_with_pending_requests(self):
        # Crear una solicitud de seguimiento pendiente
        requester = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )
        FollowRequest.objects.create(sender=requester, receiver=self.user, status='pending')

        # Probar cambio de visibilidad a pública con solicitudes pendientes
        response = self.client.post(self.url, {
            'account_visibility': 'public',
        })
        self.assertEqual(response.status_code, 200)  # La página debería recargarse con errores
        self.assertTemplateUsed(response, 'profile_settings.html')
        self.assertIn('error_messages', response.context)
        self.assertIn(
            "Para hacer tu cuenta pública, primero debes aceptar o rechazar todas las solicitudes de seguimiento pendientes.",
            response.context['error_messages']
        )

        # Comprobar que los ajustes no se cambiaron
        self.user.refresh_from_db()
        self.assertEqual(self.user.account_visibility, 'private')

    def test_post_profile_settings_toggle_options(self):
        # Probar cambios individuales en las opciones
        response = self.client.post(self.url, {
            'account_visibility': 'private',  # Sin cambios
            'show_age': '',  # Apagado
            'see_own_products': 'on',  # Encendido
        })
        self.assertRedirects(response, reverse('my_profile'))

        # Verificar cambios
        self.user.refresh_from_db()
        self.assertFalse(self.user.show_age)
        self.assertTrue(self.user.see_own_products)

    def test_borrar_cuenta(self):
        response = self.client.post(reverse('delete_account'))

        # Comprobar redirección a 'home'
        self.assertRedirects(response, reverse('home'))

        # Verificar que el usuario fue eliminado de la base de datos
        with self.assertRaises(CustomUser.DoesNotExist):
            CustomUser.objects.get(username='usuario1')

class SearchUsersTestCase(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )

        self.usuario3 = CustomUser.objects.create_user(
            username='usuario3',
            email='usuario3@example.com',
            password='password123',
        )

    def test_buscar_usuario_con_coincidencias(self):
        # Enviar solicitud de búsqueda con coincidencias
        response = self.client.get(reverse('search_users'), {'q': 'usuario2'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_users.html')

        # Comprobar que el usuario buscado aparece en los resultados
        self.assertIn(self.usuario2, response.context['users'])

    def test_buscar_usuario_sin_coincidencias(self):
        # Enviar solicitud de búsqueda sin coincidencias
        response = self.client.get(reverse('search_users'), {'q': 'noexiste'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_users.html')

        # Comprobar que no hay usuarios en los resultados
        self.assertEqual(list(response.context['users']), [])

    def test_usuario_no_se_incluye_en_resultados(self):
        # Enviar solicitud de búsqueda sin filtro específico
        response = self.client.get(reverse('search_users'))
        self.assertEqual(response.status_code, 200)

        # Comprobar que el usuario que busca no aparece en los resultados
        self.assertNotIn(self.user, response.context['users'])

    def test_busqueda_case_insensitive(self):
        # Buscar con mayúsculas y minúsculas mezcladas
        response = self.client.get(reverse('search_users'), {'q': 'UsUaRiO2'})
        self.assertEqual(response.status_code, 200)

        # Comprobar que encuentra al usuario independientemente del caso
        self.assertIn(self.usuario2, response.context['users'])

class FollowerCountTest(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )
        self.usuario3 = CustomUser.objects.create_user(
            username='usuario3',
            email='usuario3@example.com',
            password='password123',
            account_visibility='private',  # Cuenta privada
        )

    def test_follow_public_user(self):
        # Probar seguir a un usuario con cuenta pública
        url = reverse('followers_count', args=['usuario2'])
        response = self.client.post(url, {'value': 'follow'})

        # Verificar que el seguimiento se haya creado
        self.assertEqual(Follow.objects.filter(follower=self.user, following=self.usuario2).count(), 1)
        self.assertRedirects(response, reverse('other_user_profile', args=['usuario2']))

    def test_follow_private_user_and_create_request(self):
        # Probar seguir a un usuario con cuenta privada (crea una solicitud)
        url = reverse('followers_count', args=['usuario3'])
        response = self.client.post(url, {'value': 'follow'})

        # Verificar que la solicitud de seguimiento se haya creado
        self.assertEqual(FollowRequest.objects.filter(sender=self.user, receiver=self.usuario3).count(), 1)
        self.assertRedirects(response, reverse('other_user_profile', args=['usuario3']))

    def test_unfollow_user(self):
        # Seguir al usuario
        Follow.objects.create(follower=self.user, following=self.usuario2)

        # Verificar que el seguimiento existe
        self.assertEqual(Follow.objects.filter(follower=self.user, following=self.usuario2).count(), 1)

        # Probar dejar de seguir
        url = reverse('followers_count', args=['usuario2'])
        response = self.client.post(url, {'value': 'unfollow'})

        # Verificar que el seguimiento se ha eliminado
        self.assertEqual(Follow.objects.filter(follower=self.user, following=self.usuario2).count(), 0)
        self.assertRedirects(response, reverse('other_user_profile', args=['usuario2']))

    def test_user_not_found(self):
        # Probar que se maneja el caso cuando el usuario no existe
        url = reverse('followers_count', args=['usuario_inexistente'])
        response = self.client.post(url, {'value': 'follow'})

        # Verificar que se renderiza el template de usuario no encontrado
        self.assertTemplateUsed(response, 'user_not_found.html')

class OtherUserProfileTest(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )
        self.usuario3 = CustomUser.objects.create_user(
            username='usuario3',
            email='usuario3@example.com',
            password='password123',
            account_visibility='private',  # Cuenta privada
        )

        # Crear productos y alquileres para los usuarios
        self.product = Product.objects.create(
            owner=self.usuario2,
            title="Producto 1",
            description="Descripción del producto 1",
            price = 2,
        )
        self.rental = Rental.objects.create(
            owner=self.usuario2,
            title="Alquiler 1",
            description="Descripción del alquiler 1",
            location = "test location",
            square_meters = 30,
            max_people = 5,
            rooms = 3,
            price = 222,
        )

    def test_access_own_profile(self):
        # Probar que se redirige al perfil propio
        url = reverse('other_user_profile', args=['usuario1'])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('my_profile'))

    def test_access_existing_user_profile(self):
        # Probar acceder al perfil de otro usuario
        url = reverse('other_user_profile', args=['usuario2'])
        response = self.client.get(url)

        # Verificar que se obtiene el perfil del usuario
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Producto 1')
        self.assertContains(response, 'usuario2')

    def test_access_non_existing_user_profile(self):
        # Probar acceder al perfil de un usuario que no existe
        url = reverse('other_user_profile', args=['usuario_inexistente'])
        response = self.client.get(url)

        # Verificar que se redirige a la página de usuario no encontrado
        self.assertTemplateUsed(response, 'user_not_found.html')

    def test_follow_user(self):
        # Seguir a un usuario
        url = reverse('followers_count', args=['usuario2'])
        response = self.client.post(url, {'value': 'follow'})

        # Verificar que el seguimiento se ha creado
        self.assertEqual(Follow.objects.filter(follower=self.user, following=self.usuario2).count(), 1)
        self.assertRedirects(response, reverse('other_user_profile', args=['usuario2']))

    def test_unfollow_user(self):
        # Seguir al usuario antes de hacer unfollow
        Follow.objects.create(follower=self.user, following=self.usuario2)

        # Verificar que el seguimiento existe
        self.assertEqual(Follow.objects.filter(follower=self.user, following=self.usuario2).count(), 1)

        # Dejar de seguir
        url = reverse('followers_count', args=['usuario2'])
        response = self.client.post(url, {'value': 'unfollow'})

        # Verificar que el seguimiento se ha eliminado
        self.assertEqual(Follow.objects.filter(follower=self.user, following=self.usuario2).count(), 0)
        self.assertRedirects(response, reverse('other_user_profile', args=['usuario2']))

    def test_filter_products_only(self):
        # Filtrar para ver solo los productos
        url = reverse('other_user_profile', args=['usuario2']) + '?filter=articulos'
        response = self.client.get(url)

        # Verificar que solo se muestran productos y no alquileres
        self.assertContains(response, 'Producto 1')
        self.assertNotContains(response, 'Alquiler 1')

    def test_filter_rentals_only(self):
        # Filtrar para ver solo los alquileres
        url = reverse('other_user_profile', args=['usuario2']) + '?filter=alquileres'
        response = self.client.get(url)

        # Verificar que solo se muestran alquileres y no productos
        self.assertContains(response, 'Alquiler 1')
        self.assertNotContains(response, 'Producto 1')

    def test_no_filter_shows_both(self):
        # Sin filtro, se deben mostrar por defecto los productos
        url = reverse('other_user_profile', args=['usuario2'])
        response = self.client.get(url)

        # Verificar que se muestran productos por defecto
        self.assertContains(response, 'Producto 1')

class UserFollowListTest(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )
        self.usuario3 = CustomUser.objects.create_user(
            username='usuario3',
            email='usuario3@example.com',
            password='password123',
        )

        Follow.objects.create(follower=self.user, following=self.usuario2)
        Follow.objects.create(follower=self.user, following=self.usuario3)

    def test_followers_and_following_view(self):
        # Probar la vista de seguidores y seguidos para un usuario
        response = self.client.get(reverse('followers_and_following', args=['usuario1']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'usuario1')  # Verificar que el nombre de usuario aparece
        self.assertContains(response, 'usuario2')  # Verificar que el usuario seguido aparece

    def test_search_functionality(self):
        # Probar la funcionalidad de búsqueda (buscando por 'usu')
        response = self.client.get(reverse('followers_and_following', args=['usuario1']) + '?search=usu')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'usuario2')
        self.assertContains(response, 'usuario3')

    def test_no_results_in_search(self):
        # Probar búsqueda sin resultados
        response = self.client.get(reverse('followers_and_following', args=['usuario1']) + '?search=nonexistent')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No')  # Asegúrate de que este mensaje existe en tu template

    def test_sorting_functionality(self):
        # Probar ordenación por más recientes (newest)
        response = self.client.get(reverse('followers_and_following', args=['usuario1']) + '?sort_order=newest')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
        [following.following.username for following in response.context['following']][0],  # Usar lista por comprensión
        'usuario3'  # Esperado en el test
    )

    def test_sorting_oldest(self):
        # Probar ordenación por más antiguos (oldest)
        response = self.client.get(reverse('followers_and_following', args=['usuario1']) + '?sort_order=oldest')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
        [following.following.username for following in response.context['following']][0],  # Usar lista por comprensión
        'usuario2'  # Esperado en el test
    )
        
class RemoveFollowerTest(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )

        # Crear relación de seguir
        self.follow = Follow.objects.create(follower=self.usuario2, following=self.user)

    def test_remove_follower(self):
        # Probar eliminar un seguidor
        response = self.client.post(reverse('remove_follower', args=[self.usuario2.id]))
        
        # Verificar que la relación de seguir ha sido eliminada
        self.assertEqual(Follow.objects.filter(follower=self.usuario2, following=self.user).count(), 0)
        self.assertRedirects(response, reverse('followers_and_following', args=[self.user.username]))

class UnfollowUserTest(TestCase):
    def setUp(self):
        # Crear usuario inicial
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )

        # Crear relación de seguir
        self.follow = Follow.objects.create(follower=self.user, following=self.usuario2)

    def test_unfollow_user(self):
        # Probar dejar de seguir a un usuario
        response = self.client.post(reverse('unfollow_user', args=[self.usuario2.id]))

        # Verificar que la relación de seguir ha sido eliminada
        self.assertEqual(Follow.objects.filter(follower=self.user, following=self.usuario2).count(), 0)
        self.assertRedirects(response, reverse('followers_and_following', args=[self.user.username]))

class FollowRequestsTest(TestCase):
    def setUp(self):
        # Crear usuarios
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
            account_visibility='private',  # Cuenta privada
        )
        self.client.login(username='usuario1', password='password123')

        self.usuario2 = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )

        # Crear solicitud de seguimiento pendiente
        self.follow_request = FollowRequest.objects.create(
            sender=self.usuario2,
            receiver=self.user,
            status='pending'
        )

    def test_accept_follow_request(self):
        # Probar aceptar solicitud de seguimiento
        response = self.client.post(reverse('accept_follow_request', args=[self.follow_request.id]))

        # Verificar que la relación de seguimiento se haya creado
        self.assertTrue(Follow.objects.filter(follower=self.usuario2, following=self.user).exists())
        
        # Verificar que la solicitud de seguimiento se ha eliminado
        self.assertFalse(FollowRequest.objects.filter(id=self.follow_request.id).exists())

        # Verificar que redirige correctamente
        self.assertRedirects(response, reverse('follow_requests'))

    def test_reject_follow_request(self):
        # Probar rechazar solicitud de seguimiento
        response = self.client.post(reverse('reject_follow_request', args=[self.follow_request.id]))

        # Verificar que la solicitud de seguimiento se ha eliminado
        self.assertFalse(FollowRequest.objects.filter(id=self.follow_request.id).exists())

        # Verificar que redirige correctamente
        self.assertRedirects(response, reverse('follow_requests'))
    
    def test_follow_requests_for_public_account(self):
        # Cambiar la visibilidad de la cuenta a pública
        self.user.account_visibility = 'public'
        self.user.save()

        # Probar que se muestra el mensaje de visibilidad pública
        response = self.client.get(reverse('follow_requests'))

        # Verificar que redirige a la página de visibilidad pública
        self.assertTemplateUsed(response, 'your_vissibility_is_public.html')

class SidebarViewTestCase(TestCase):
    pass

class UpdateCityTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        # Ciudad válida para probar
        self.valid_city = 'Madrid'
        self.invalid_city = 'CiudadFalsa'

        # Definir ciudades válidas para la prueba (esto depende de tu lógica de negocio)
        self.valid_cities = ['Madrid', 'Barcelona', 'Sevilla']

    def test_update_city_valid(self):
        # Hacer una solicitud POST con una ciudad válida
        response = self.client.post(reverse('update_city'), 
                                    json.dumps({'selected_city': self.valid_city}),
                                    content_type='application/json')
        
        # Verificar la respuesta
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, 'utf8'), {'success': True, 'new_city': self.valid_city})
        
        # Verificar que la ciudad del usuario se ha actualizado
        self.user.refresh_from_db()
        self.assertEqual(self.user.selected_city, self.valid_city)

    def test_update_city_invalid(self):
        # Hacer una solicitud POST con una ciudad no válida
        response = self.client.post(reverse('update_city'), 
                                    json.dumps({'selected_city': self.invalid_city}),
                                    content_type='application/json')

        # Verificar que la respuesta es un error 400
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(str(response.content, 'utf8'), {'success': False, 'message': 'Ciudad no válida'})

    def test_update_city_not_authenticated(self):
        # Cerrar sesión del usuario
        self.client.logout()

        # Hacer una solicitud POST sin estar autenticado
        response = self.client.post(reverse('update_city'), 
                                    json.dumps({'selected_city': self.valid_city}),
                                    content_type='application/json')

        # Verificar que la respuesta es un error 401
        self.assertEqual(response.status_code, 401)
        self.assertJSONEqual(str(response.content, 'utf8'), {'success': False, 'message': 'Para acceder a todas las funcionalidades deberás '})

    def test_update_city_method_not_allowed(self):
        # Hacer una solicitud GET (método no permitido)
        response = self.client.get(reverse('update_city'))

        # Verificar que la respuesta es un error 405
        self.assertEqual(response.status_code, 405)
        self.assertJSONEqual(str(response.content, 'utf8'), {'success': False, 'message': 'Método no permitido'})