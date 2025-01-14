from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from main.models import FollowRequest, CustomUser, Follow
from .models import Product, Rental, ProductImage
from .views import moneda_oficial, currency
from unittest.mock import patch

class MonedaOficialYCurrencyTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')
    
    def test_moneda_oficial(self):
        # Probar varias ciudades y verificar la moneda oficial
        test_cases = [
            ('Sofia', 'лв'),  # Bulgaria
            ('Praga', 'Kč'),  # República Checa
            ('Copenhague', 'kr'),  # Dinamarca
            ('Budapest', 'Ft'),  # Hungría
            ('Varsovia', 'zł'),  # Polonia
            ('Buenos Aires', '$'),  # Peso argentino
            ('Canberra', '$'),  # Dólar australiano
            ('Brasilia', 'R$'),  # Real brasileño
            ('Ottawa', '$'),  # Dólar canadiense
            ('Santiago', '$'),  # Peso chileno
            ('Pekín', '¥'),  # Yuan renminbi chino
            ('Washington D.C.', '$'),  # Dólar estadounidense
            ('Nueva Delhi', '₹'),  # Rupia india
            ('Tokio', '¥'),  # Yen japonés
            ('Montevideo', '$'),  # Peso uruguayo
            ('Madrid', '€')  # Zona euro
        ]

        for city, expected_money in test_cases:
            with self.subTest(city=city):
                self.user.city = city
                self.user.save()

                # Crear un objeto request manualmente
                request = HttpRequest()
                request.user = self.user  # Asignar el usuario autenticado al request
                
                # Llamar a la función con el request correcto
                response = moneda_oficial(request)
                
                # Comprobar si la respuesta coincide con la moneda esperada
                self.assertEqual(response, expected_money)

    def test_currency(self):
        # Probar varias ciudades y verificar la moneda en formato de código
        test_cases = [
            ('Sofia', 'BGN'),  # Lev búlgaro
            ('Praga', 'CZK'),  # Corona checa
            ('Copenhague', 'DKK'),  # Corona danesa
            ('Budapest', 'HUF'),  # Florín húngaro
            ('Varsovia', 'PLN'),  # Zloty polaco
            ('Buenos Aires', 'ARS'),  # Peso argentino
            ('Canberra', 'AUD'),  # Dólar australiano
            ('Brasilia', 'BRL'),  # Real brasileño
            ('Ottawa', 'CAD'),  # Dólar canadiense
            ('Santiago', 'CLP'),  # Peso chileno
            ('Pekín', 'CNY'),  # Yuan renminbi chino
            ('Washington D.C.', 'USD'),  # Dólar estadounidense
            ('Nueva Delhi', 'INR'),  # Rupia india
            ('Tokio', 'JPY'),  # Yen japonés
            ('Montevideo', 'UYU'),  # Peso uruguayo
            ('Madrid', 'EUR')  # Euro para la zona euro
        ]

        for city, expected_currency in test_cases:
            with self.subTest(city=city):
                self.user.city = city
                self.user.save()

                # Crear un objeto request manualmente
                request = HttpRequest()
                request.user = self.user  # Asignar el usuario autenticado al request
                
                # Llamar a la función con el request correcto
                response = currency(request)
                
                # Comprobar si la respuesta coincide con la moneda esperada
                self.assertEqual(response, expected_currency)

class MyMarketProfileTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        # Crear productos y alquileres para el usuario
        self.product1 = Product.objects.create(owner=self.user, price=20, highlighted=True)
        self.product2 = Product.objects.create(owner=self.user, price=20, highlighted=False)
        self.rental1 = Rental.objects.create(
            owner=self.user,
            title="Alquiler 1",
            description="Descripción del alquiler 1",
            location = "test location",
            square_meters = 30,
            max_people = 5,
            rooms = 3,
            price = 222,
            highlighted = True
        )
        self.rental2 = Rental.objects.create(
            owner=self.user,
            title="Alquiler 2",
            description="Descripción del alquiler 2",
            location = "test location 2",
            square_meters = 30,
            max_people = 5,
            rooms = 3,
            price = 222,
            highlighted = False
        )
        
        # Crear solicitudes de seguimiento pendientes
        self.other_user = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )
        FollowRequest.objects.create(sender=self.other_user, receiver=self.user, status='pending')
        
        # Actualizar campos del perfil para alertas
        self.user.birthday = None
        self.user.city = ""
        self.user.description = ""
        self.user.profile_picture = ""
        self.user.save()

    def test_my_market_profile_default_filter(self):
        # Hacer una solicitud GET a la vista
        response = self.client.get(reverse('market:my_market_profile'))
        
        # Comprobar que la respuesta es 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verificar el contexto de la plantilla
        self.assertIn('user_products', response.context)
        self.assertIn('user_rentings', response.context)
        self.assertIn('announce_count', response.context)
        self.assertIn('rating_count', response.context)
        self.assertIn('average_rating', response.context)
        self.assertIn('complete_profile_alerts', response.context)
        self.assertIn('total_alerts', response.context)
        
        # Comprobar los valores del contexto
        self.assertEqual(len(response.context['user_products']), 2)  # Dos productos
        self.assertEqual(len(response.context['user_rentings']), 0)  # Dos alquileres
        self.assertEqual(response.context['announce_count'], 4)  # Suma de productos y alquileres
        self.assertEqual(response.context['complete_profile_alerts'], 5)  # Alertas de perfil incompleto
        self.assertEqual(response.context['total_alerts'], 6)  # 5 alertas + 1 solicitud pendiente

    def test_my_market_profile_filter_products(self):
        # Filtrar solo productos
        response = self.client.get(reverse('market:my_market_profile') + '?filter=articulos')
        self.assertEqual(len(response.context['user_products']), 2)
        self.assertEqual(len(response.context['user_rentings']), 0)

    def test_my_market_profile_filter_rentings(self):
        # Filtrar solo alquileres
        response = self.client.get(reverse('market:my_market_profile') + '?filter=alquileres')
        self.assertEqual(len(response.context['user_products']), 0)
        self.assertEqual(len(response.context['user_rentings']), 2)

class ProductDetailsTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

       # Crear productos
        self.product1 = Product.objects.create(
            owner=self.user, 
            price=20, 
            highlighted=True, 
            title="Producto 1", 
            description="Descripción del producto 1"
        )
        self.product2 = Product.objects.create(
            owner=self.user, 
            price=30, 
            highlighted=True, 
            title="Producto 2", 
            description="Descripción del producto 2"
        )

    def test_product_details_existing_product(self):
        # Test cuando el producto existe
        response = self.client.get(reverse('market:product_details', kwargs={'product_id': self.product1.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Producto 1')
        self.assertContains(response, 'Descripción del producto 1')

    def test_product_details_non_existing_product(self):
        # Test cuando el producto no existe
        response = self.client.get(reverse('market:product_details', kwargs={'product_id': 999}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invalid_id.html')

    @patch('main.models.FollowRequest.objects.filter')
    def test_product_details_with_pending_follow_requests(self, mock_filter):
        # Test con solicitudes de seguimiento pendientes
        mock_filter.return_value.count.return_value = 3
        
        response = self.client.get(reverse('market:product_details', kwargs={'product_id': self.product1.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Producto 1')
        self.assertEqual(response.context['pending_requests_count'], 3)

    @patch('main.views.alertas_completar_perfil')
    def test_product_details_with_profile_alert(self, mock_alert):
        # Test con alerta de completar perfil
        mock_alert.return_value.count.return_value = 5
        
        response = self.client.get(reverse('market:product_details', kwargs={'product_id': self.product1.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Producto 1')
        self.assertEqual(response.context['complete_profile_alerts'], 5)

class DeleteProductTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        # Crear productos
        self.product1 = Product.objects.create(
            owner=self.user, 
            price=20, 
            highlighted=True, 
            title="Producto 1", 
            description="Descripción del producto 1"
        )
        self.product2 = Product.objects.create(
            owner=self.user, 
            price=30, 
            highlighted=True, 
            title="Producto 2", 
            description="Descripción del producto 2"
        )

        # Crear otro usuario
        self.other_user = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123'
        )

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_product_owner(self, mock_filter):
        # Test cuando el usuario es el propietario del producto
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación
        response = self.client.post(reverse('market:delete_product', kwargs={'product_id': self.product1.id}))
        
        # Verificar que el producto se ha eliminado
        self.assertEqual(response.status_code, 302)  # Redirige a 'my_market_profile'
        self.assertFalse(Product.objects.filter(id=self.product1.id).exists())  # El producto ya no existe

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_product_not_owner(self, mock_filter):
        # Test cuando el usuario no es el propietario del producto
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación como otro usuario
        self.client.login(username='usuario2', password='password123')
        response = self.client.post(reverse('market:delete_product', kwargs={'product_id': self.product1.id}))
        
        # Verificar que se redirige a la página de error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_your_ads_only.html')

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_product_non_existent(self, mock_filter):
        # Test cuando el producto no existe
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación de un producto inexistente
        response = self.client.post(reverse('market:delete_product', kwargs={'product_id': 999}))
        
        # Verificar que se redirige a la página de error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invalid_id.html')

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_product_redirects_after_deletion(self, mock_filter):
        # Test que asegura que el redireccionamiento ocurre después de la eliminación
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación
        response = self.client.post(reverse('market:delete_product', kwargs={'product_id': self.product2.id}))
        
        # Verificar que el producto se ha eliminado y se redirige correctamente
        self.assertEqual(response.status_code, 302)  # Redirige a 'my_market_profile'
        self.assertFalse(Product.objects.filter(id=self.product2.id).exists())

class EditProductTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        # Crear producto
        self.product = Product.objects.create(
            owner=self.user, 
            price=20, 
            highlighted=True, 
            title="Producto Original", 
            description="Descripción original del producto"
        )
        # Crear una imagen para el producto
        self.product_image = ProductImage.objects.create(
            product=self.product,
            image='path/to/image.jpg'
        )


    def test_delete_product_image(self):
        # Eliminar imagen del producto
        image_to_delete = self.product.images.first()
        response = self.client.post(reverse('market:delete_product_image', kwargs={
            'product_id': self.product.id,
            'image_id': image_to_delete.id
        }))
        self.assertEqual(response.status_code, 302)  # Redirige después de eliminar la imagen
        self.assertFalse(ProductImage.objects.filter(id=image_to_delete.id).exists())  # La imagen fue eliminada

class RentingDetailsTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        # Crear un alquiler
        self.rental = Rental.objects.create(
            owner=self.user,
            price=100,
            title="Alquiler 1",
            description="Descripción del alquiler 1",
            square_meters = 200,
            max_people = 4,
            rooms = 4
        )

    def test_renting_details_existing_rental(self):
        # Test cuando el alquiler existe
        response = self.client.get(reverse('market:renting_details', kwargs={'renting_id': self.rental.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alquiler 1')
        self.assertContains(response, 'Descripción del alquiler 1')

    def test_renting_details_non_existing_rental(self):
        # Test cuando el alquiler no existe
        response = self.client.get(reverse('market:renting_details', kwargs={'renting_id': 999}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invalid_id.html')

    @patch('main.models.FollowRequest.objects.filter')
    def test_renting_details_with_pending_follow_requests(self, mock_filter):
        # Test con solicitudes de seguimiento pendientes
        mock_filter.return_value.count.return_value = 3
        
        response = self.client.get(reverse('market:renting_details', kwargs={'renting_id': self.rental.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alquiler 1')
        self.assertEqual(response.context['pending_requests_count'], 3)

    @patch('main.views.alertas_completar_perfil')
    def test_renting_details_with_profile_alert(self, mock_alert):
        # Test con alerta de completar perfil
        mock_alert.return_value.count.return_value = 5
        
        response = self.client.get(reverse('market:renting_details', kwargs={'renting_id': self.rental.id}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alquiler 1')
        self.assertEqual(response.context['complete_profile_alerts'], 5)

class DeleteRentingTestCase(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        # Crear alquiler
        self.rental1 = Rental.objects.create(
            owner=self.user,
            price=100,
            title="Alquiler 1",
            description="Descripción del alquiler 1",
            square_meters = 200,
            max_people = 4,
            rooms = 4
        )
        self.rental2 = Rental.objects.create(
            owner=self.user,
            price=150,
            title="Alquiler 2",
            description="Descripción del alquiler 2",
            square_meters = 200,
            max_people = 4,
            rooms = 4
        )

        # Crear otro usuario
        self.other_user = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123'
        )

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_renting_owner(self, mock_filter):
        # Test cuando el usuario es el propietario del alquiler
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación
        response = self.client.post(reverse('market:delete_renting', kwargs={'renting_id': self.rental1.id}))
        
        # Verificar que el alquiler se ha eliminado
        self.assertEqual(response.status_code, 302)  # Redirige a 'my_market_profile'
        self.assertFalse(Rental.objects.filter(id=self.rental1.id).exists())  # El alquiler ya no existe

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_renting_not_owner(self, mock_filter):
        # Test cuando el usuario no es el propietario del alquiler
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación como otro usuario
        self.client.login(username='usuario2', password='password123')
        response = self.client.post(reverse('market:delete_renting', kwargs={'renting_id': self.rental1.id}))
        
        # Verificar que se redirige a la página de error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_your_ads_only.html')

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_renting_non_existent(self, mock_filter):
        # Test cuando el alquiler no existe
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación de un alquiler inexistente
        response = self.client.post(reverse('market:delete_renting', kwargs={'renting_id': 999}))
        
        # Verificar que se redirige a la página de error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invalid_id.html')

    @patch('main.models.FollowRequest.objects.filter')
    def test_delete_renting_redirects_after_deletion(self, mock_filter):
        # Test que asegura que el redireccionamiento ocurre después de la eliminación
        mock_filter.return_value.count.return_value = 0  # No hay solicitudes pendientes
        
        # Hacer la solicitud de eliminación
        response = self.client.post(reverse('market:delete_renting', kwargs={'renting_id': self.rental2.id}))
        
        # Verificar que el alquiler se ha eliminado y se redirige correctamente
        self.assertEqual(response.status_code, 302)  # Redirige a 'my_market_profile'
        self.assertFalse(Rental.objects.filter(id=self.rental2.id).exists())  # El alquiler ya no existe


class MarketProfileOtherUserTestCase(TestCase):

    def setUp(self):
        # Crear usuarios de prueba
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )
        self.client.login(username='usuario1', password='password123')

        self.other_user = CustomUser.objects.create_user(
            username='usuario2',
            email='usuario2@example.com',
            password='password123',
        )

        # Crear productos y alquileres para el otro usuario
        self.product1 = Product.objects.create(owner=self.other_user, price=20, highlighted=True)
        self.product2 = Product.objects.create(owner=self.other_user, price=30, highlighted=False)
        self.rental1 = Rental.objects.create(
            owner=self.other_user,
            title="Alquiler 1",
            description="Descripción del alquiler 1",
            location="test location",
            square_meters=30,
            max_people=5,
            rooms=3,
            price=222,
            highlighted=True
        )
        self.rental2 = Rental.objects.create(
            owner=self.other_user,
            title="Alquiler 2",
            description="Descripción del alquiler 2",
            location="test location 2",
            square_meters=30,
            max_people=5,
            rooms=3,
            price=222,
            highlighted=False
        )

        # Crear solicitudes de seguimiento pendientes
        FollowRequest.objects.create(sender=self.user, receiver=self.other_user, status='pending')

    def test_market_profile_other_user(self):
        # Hacer una solicitud GET a la vista
        response = self.client.get(reverse('market:market_profile_other_user', args=['usuario2']))

        # Comprobar que la respuesta es 200 OK
        self.assertEqual(response.status_code, 200)

        # Verificar el contexto de la plantilla
        self.assertIn('profile_user', response.context)
        self.assertIn('user_products', response.context)
        self.assertIn('user_rentings', response.context)
        self.assertIn('announce_count', response.context)
        self.assertIn('follow_button_value', response.context)
        self.assertIn('pending_follow_request', response.context)

        # Comprobar los valores del contexto
        self.assertEqual(response.context['profile_user'].username, 'usuario2')  # El usuario mostrado es el correcto
        self.assertEqual(len(response.context['user_products']), 2)  # Dos productos
        self.assertEqual(len(response.context['user_rentings']), 0)  # Cero alquileres visibles
        self.assertEqual(response.context['announce_count'], 4)  # Suma de productos y alquileres
        self.assertEqual(response.context['follow_button_value'], 'follow')  # Botón de seguimiento

    def test_market_profile_other_user_following(self):
        # Crear un seguimiento entre los usuarios
        Follow.objects.create(follower=self.user, following=self.other_user)

        # Hacer una solicitud GET a la vista
        response = self.client.get(reverse('market:market_profile_other_user', args=['usuario2']))

        # Comprobar que el botón de seguimiento es 'unfollow'
        self.assertEqual(response.context['follow_button_value'], 'unfollow')  # El botón debe cambiar a 'unfollow'

    def test_market_profile_other_user_not_found(self):
        # Hacer una solicitud GET con un usuario que no existe
        response = self.client.get(reverse('market:market_profile_other_user', args=['usuario_inexistente']))

        # Comprobar que la respuesta es 200 OK
        self.assertEqual(response.status_code, 200)

        # Verificar el contexto de la plantilla
        self.assertIn('pending_requests_count', response.context)
        self.assertIn('complete_profile_alerts', response.context)

        # Verificar que se muestra la página de error
        self.assertTemplateUsed(response, 'user_not_found.html')

    def test_market_profile_other_user_filter_products(self):
        # Filtrar solo productos
        response = self.client.get(reverse('market:market_profile_other_user', args=['usuario2']) + '?filter=articulos')

        # Comprobar que solo se muestran productos
        self.assertEqual(len(response.context['user_products']), 2)
        self.assertEqual(len(response.context['user_rentings']), 0)

    def test_market_profile_other_user_filter_rentings(self):
        # Filtrar solo alquileres
        response = self.client.get(reverse('market:market_profile_other_user', args=['usuario2']) + '?filter=alquileres')

        # Comprobar que solo se muestran alquileres
        self.assertEqual(len(response.context['user_products']), 0)
        self.assertEqual(len(response.context['user_rentings']), 2)


class MainMarketProductsTests(TestCase):
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='usuario1',
            email='usuario1@example.com',
            password='password123',
        )

        self.client.login(username='usuario1', password='password123')

        self.product1 = Product.objects.create(
            title='Product 1',
            price=100,
            city_associated='city1',
            owner=self.user,
            highlighted=True
        )
        self.product2 = Product.objects.create(
            title='Product 2',
            price=200,
            city_associated='city1',
            owner=self.user
        )

    def test_main_market_products_valid_city(self):
        response = self.client.get(reverse('market:main_market_products', args=['city1']))
        self.assertEqual(response.status_code, 200)

    def test_main_market_products_invalid_city(self):
        response = self.client.get(reverse('market:main_market_products', args=['invalid_city']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'market/invalid_city.html')

    def test_no_search_results(self):
        response = self.client.get(reverse('market:main_market_products', args=['city1']), {'q': 'Nonexistent product'})
        self.assertEqual(response.status_code, 200)
        
    def test_pagination(self):
        for i in range(25):  # Create 25 products
            Product.objects.create(
                title=f'Product {i+3}',
                price=100,
                city_associated='city1',
                owner=self.user,
                highlighted=False
            )
        response = self.client.get(reverse('market:main_market_products', args=['city1']))
        self.assertEqual(response.status_code, 200)
