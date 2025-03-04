import unittest
from urllib.parse import quote
from main.turism.views import city_conversor  # Asegúrate de importar correctamente tu función
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from main.models import CustomUser as User
from main.turism.views import city_map
from main.views import city_data  # Asegúrate de importar city_data si está en otro archivo

class CityConversorTests(unittest.TestCase):

    def test_city_conversions(self):
        """Test de ciudades con conversión específica"""
        cases = {
            "La Valeta": "Valletta",
            "Atenas": "Athens",
            "Luxemburgo": "Luxembourg",
            "Roterdam": "Rotterdam",
            "Viena": "Wien",
            "Varsovia": "Warsaw",
            "Oporto": "Porto",
            "Buenos Aires": "Buenos%20Aires",
            "Washington D.C.": "Washington",
            "Nueva Delhi": "New%20Delhi",
            "Sofia": quote("София"),
            "Copenhague": quote("København"),
            "Brasilia": quote("Brasília"),
            "Praga": "Praha",
            "Pekín": quote("北京"),
        }
        
        for city, expected in cases.items():
            with self.subTest(city=city):
                self.assertEqual(city_conversor(city), expected)

    def test_city_no_conversion(self):
        """Ciudades que no deberían cambiar"""
        cities = ["Madrid", "Lisboa", "Berlin", "Roma", "Toronto"]
        for city in cities:
            with self.subTest(city=city):
                self.assertEqual(city_conversor(city), city)

    def test_empty_string(self):
        """Prueba con un string vacío"""
        self.assertEqual(city_conversor(""), "")

    def test_numeric_input(self):
        """Prueba con valores numéricos convertidos a string"""
        self.assertEqual(city_conversor("123"), "123")

    def test_special_characters(self):
        """Prueba con caracteres especiales"""
        self.assertEqual(city_conversor("@#$%^&*"), "@#$%^&*")

if __name__ == "__main__":
    unittest.main()


class CityMapTests(TestCase):

    def setUp(self):
        """Crear un usuario y datos de prueba"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

        # Agregar datos de ciudad de prueba
        self.city_name = "Madrid"
        city_data[self.city_name] = {
            "lat": 40.4168,
            "lon": -3.7038,
            "country": "España",
            "flag": "spain_flag.png"
        }

    def test_login_required(self):
        """Verificar que se redirige a la página de login si el usuario no está autenticado"""
        response = self.client.get(reverse('turism:city_map', args=[self.city_name]))
        self.assertEqual(response.status_code, 302)  # Redirección a login

    def test_valid_city(self):
        """Verificar que una ciudad válida renderiza correctamente"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('turism:city_map', args=[self.city_name]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'turism/city_map.html')
        self.assertContains(response, self.city_name)
        self.assertContains(response, "España")
        self.assertContains(response, "spain_flag.png")

    def test_invalid_city(self):
        """Verificar que una ciudad inexistente renderiza invalid_city.html"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('turism:city_map', args=["FakeCity"]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invalid_city.html')

    @patch('requests.get')
    def test_overpass_api_mocked_response(self, mock_get):
        """Probar que la vista maneja correctamente la API Overpass"""
        self.client.login(username='testuser', password='12345')

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "elements": [
                {
                    "lat": 40.4168,
                    "lon": -3.7038,
                    "tags": {
                        "name": "Plaza Mayor",
                        "addr:street": "Calle Mayor",
                        "addr:housenumber": "1",
                        "addr:postcode": "28012",
                        "opening_hours": "24/7",
                        "fee": "Gratis",
                        "website": "https://plazamayor.com",
                        "phone": "+34 123456789"
                    }
                }
            ]
        }

        response = self.client.get(reverse('turism:city_map', args=[self.city_name]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'turism/city_map.html')
        self.assertContains(response, "Plaza Mayor")
        self.assertContains(response, "Calle Mayor 1 28012")
        self.assertContains(response, "24/7")
        self.assertContains(response, "Gratis")
        self.assertContains(response, "https://plazamayor.com")

if __name__ == "__main__":
    unittest.main()
