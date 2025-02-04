from django.test import TestCase, Client 
from django.urls import reverse 
from django.contrib.auth import get_user_model 
from django.utils.timezone import make_aware 
from datetime import datetime 
from main.events.models import Event 
from main.models import FollowRequest
from main.community.models import ChatRequest
User = get_user_model() 

class EventCalendarViewTests(TestCase): 
    def setUp(self): 
        """Configuración inicial antes de cada test""" 
        self.client = Client() 
        self.user = User.objects.create_user(username="testuser", password="password") 
        self.client.login(username="testuser", password="password") 

        # Ciudad de prueba 
        self.selected_city = "Madrid" 
        self.valid_cities = ["Madrid", "Barcelona", "Sevilla"] 
 
        # Evento de un solo día 
        self.event_single_day = Event.objects.create( 
            title="Evento Único", 
            city=self.selected_city, 
            start=make_aware(datetime(2024, 2, 10, 10, 0)), 
            end=make_aware(datetime(2024, 2, 10, 12, 0)), 
            price=10, 
            creator=self.user 
        ) 

        # Evento de varios días 
        self.event_multiple_days = Event.objects.create( 
            title="Evento Largo", 
            city=self.selected_city, 
            start=make_aware(datetime(2024, 2, 8, 10, 0)), 
            end=make_aware(datetime(2024, 2, 12, 12, 0)), 
            price=0, 
            creator=self.user 
        ) 
 
        self.user.selected_city = self.selected_city 
        self.user.save() 
 
        # Solicitud de seguimiento pendiente 
        FollowRequest.objects.create(receiver=self.user, sender=self.user, status="pending") 
 
        # Solicitud de chat pendiente 
        ChatRequest.objects.create(receiver=self.user, sender=self.user, status="pending") 
 
    def test_view_loads_correctly(self): 
        """Prueba que la vista carga correctamente con usuario autenticado""" 
        response = self.client.get(reverse("events:event_calendar", args=[self.selected_city])) 
        self.assertEqual(response.status_code, 200) 
        self.assertTemplateUsed(response, "calendar.html") 
        self.assertIn("events", response.context) 
        self.assertIn("selected_city", response.context) 
 
    def test_invalid_city(self): 
        """Prueba que muestra la plantilla de ciudad inválida si la ciudad no es válida""" 
        response = self.client.get(reverse("events:event_calendar", args=["CiudadFalsa"])) 
        self.assertTemplateUsed(response, "market/invalid_city.html") 
 
    def test_no_city_selected(self): 
        """Prueba que muestra la plantilla de selección de ciudad si el usuario no tiene una""" 
        self.user.selected_city = "" 
        self.user.save() 
        response = self.client.get(reverse("events:event_calendar", args=[self.selected_city])) 
        self.assertTemplateUsed(response, "market/select_city_before_searching.html") 
 
    def test_events_displayed_correctly(self): 
        """Prueba que los eventos del mes se muestran correctamente""" 
        response = self.client.get(reverse("events:event_calendar", args=[self.selected_city]), {"year": 2024, "month": 2}) 
        events = response.context["events"] 
        self.assertIn(self.event_single_day, events) 
        self.assertIn(self.event_multiple_days, events) 
 
    def test_events_filtered_by_day(self): 
        """Prueba que al seleccionar un día solo se muestran los eventos de ese día""" 
        response = self.client.get(reverse("events:event_calendar", args=[self.selected_city]), {"year": 2024, "month": 2, "day": 10}) 
        events_for_day = response.context["events_for_day"] 
        self.assertIn(self.event_single_day, events_for_day) 
        self.assertIn(self.event_multiple_days, events_for_day) 
 
    def test_month_navigation(self): 
        """Prueba que la navegación de meses calcula correctamente el mes anterior y siguiente""" 
        response = self.client.get(reverse("events:event_calendar", args=[self.selected_city]), {"year": 2024, "month": 3}) 
        self.assertEqual(response.context["previous_month"], 2) 
        self.assertEqual(response.context["previous_year"], 2024) 
        self.assertEqual(response.context["next_month"], 4) 
        self.assertEqual(response.context["next_year"], 2024) 
 
    def test_alerts_and_counts(self): 
        """Prueba que las alertas y notificaciones se pasan correctamente al contexto""" 
        response = self.client.get(reverse("events:event_calendar", args=[self.selected_city])) 
        self.assertEqual(response.context["pending_requests_count"], 1) 
        self.assertEqual(response.context["pending_chat_requests_count"], 1)