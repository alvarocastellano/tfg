from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from main.community.models import Chat, GroupChat, ChatRequest, ChatMember, Message
from main.models import FollowRequest, Follow
from itertools import chain
from django.db.models import Q

CustomUser = get_user_model()

class AllChatsViewTest(TestCase):

    def setUp(self):
        # Crear usuarios de prueba
        self.user = CustomUser.objects.create_user(username='user1', password='password1', city='TestCity', email="user1@example.com")
        self.user2 = CustomUser.objects.create_user(username='user2', password='password2', city='OtherCity', email="user2@example.com")
        self.user3 = CustomUser.objects.create_user(username='user3', password='password3', city='TestCity', email="user3@example.com")

        

        # Iniciar sesión
        self.client = Client()
        self.client.login(username='user1', password='password1')

        # Crear chats privados
        self.chat1 = Chat.objects.create(user1=self.user, user2=self.user2)
        self.chat2 = Chat.objects.create(user1=self.user2, user2=self.user)

        # Crear chats grupales
        self.group_chat1 = GroupChat.objects.create(name='Test Group', created_at='2025-01-01')
        self.chat_member1 = ChatMember.objects.create(user=self.user, group_chat=self.group_chat1)
        self.group_chat1.members.add(self.chat_member1)

        self.group_chat2 = GroupChat.objects.create(name='Other Group', created_at='2025-01-02')
        self.chat_member2 = ChatMember.objects.create(user=self.user2, group_chat=self.group_chat2)
        self.group_chat2.members.add(self.chat_member2)

        # Crear solicitudes de seguimiento
        FollowRequest.objects.create(sender=self.user2, receiver=self.user, status='pending')

        # Crear solicitudes de chat
        ChatRequest.objects.create(sender=self.user3, receiver=self.user, status='pending')

    def test_all_chats_view_status_code(self):
        response = self.client.get(reverse('community:all_chats'))
        self.assertEqual(response.status_code, 200)

    def test_all_chats_context_data(self):
        response = self.client.get(reverse('community:all_chats'))
        self.assertIn('complete_profile_alerts', response.context)
        self.assertIn('pending_requests_count', response.context)
        self.assertIn('private_chats', response.context)
        self.assertIn('all_my_chats', response.context)
        self.assertIn('country', response.context)
        self.assertIn('flag_image', response.context)
        self.assertIn('pending_chat_requests_count', response.context)
        self.assertIn('total_unread_count', response.context)
        self.assertIn('total_unread_count_only_chats', response.context)

    def test_pending_requests_count(self):
        response = self.client.get(reverse('community:all_chats'))
        self.assertEqual(response.context['pending_requests_count'], 1)

    def test_pending_chat_requests_count(self):
        response = self.client.get(reverse('community:all_chats'))
        self.assertEqual(response.context['pending_chat_requests_count'], 1)

    def test_private_chats(self):
        response = self.client.get(reverse('community:all_chats'))
        private_chats = response.context['private_chats']
        self.assertEqual(private_chats.count(), 2)
        self.assertIn(self.chat1, private_chats)
        self.assertIn(self.chat2, private_chats)

    def test_group_chats(self):
        response = self.client.get(reverse('community:all_chats'))
        all_my_chats = response.context['all_my_chats']

        # Comprobar que los chats grupales están presentes
        group_chats = list(chain(
            GroupChat.objects.filter(members__user=self.user)
        ))
        for group_chat in group_chats:
            self.assertIn(group_chat, all_my_chats)

    def test_total_unread_count(self):
        # Marcar mensajes no leídos
        self.chat1.messages.create(sender=self.user2, content="Unread message", is_read=False)
        self.group_chat1.group_messages.create(sender=self.user3, content="Group unread message", is_read=False)

        response = self.client.get(reverse('community:all_chats'))
        self.assertEqual(response.context['total_unread_count'], 3)
        self.assertEqual(response.context['total_unread_count_only_chats'], 2)

    def test_country_and_flag_image(self):
        response = self.client.get(reverse('community:all_chats'))
        self.assertEqual(response.context['country'], 'Desconocido')
        self.assertEqual(response.context['flag_image'], '')


class CreatePrivateChatViewTests(TestCase):

    def setUp(self):
        # Crear usuarios de prueba
        self.user = CustomUser.objects.create_user(username='user1', password='password1', city='TestCity', email="user1@example.com")
        self.user2 = CustomUser.objects.create_user(username='user2', password='password2', city='OtherCity', email="user2@example.com")
        self.user3 = CustomUser.objects.create_user(username='user3', password='password3', city='TestCity', email="user3@example.com")

        # Iniciar sesión
        self.client = Client()
        self.client.login(username='user1', password='password1')

        # Crear relación de follow
        Follow.objects.create(follower=self.user, following=self.user2)
        Follow.objects.create(follower=self.user2, following=self.user)

        # Crear solicitud de chat existente
        ChatRequest.objects.create(sender=self.user, receiver=self.user3, initial_message="Hola", status="pending")

    def test_access_create_private_chat_page(self):
        response = self.client.get(reverse('community:create_private_chat'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/create_chat.html')

    def test_create_chat_without_selecting_user(self):
        response = self.client.post(reverse('community:create_private_chat'), {
            'initial_message': 'Hola, ¿quieres chatear?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selecciona a un usuario para poder iniciar un chat')

    def test_create_chat_without_initial_message(self):
        response = self.client.post(reverse('community:create_private_chat'), {
            'selected_user': self.user2.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Escribe un mensaje inicial para la solicitud de chat')

    def test_create_chat_with_existing_chat(self):
        Chat.objects.create(user1=self.user, user2=self.user2)
        response = self.client.post(reverse('community:create_private_chat'), {
            'selected_user': self.user2.id,
            'initial_message': 'Hola, ¿cómo estás?'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ya existe un chat activo con este usuario.')

    def test_create_chat_with_follow_mutual(self):
        response = self.client.post(reverse('community:create_private_chat'), {
            'selected_user': self.user2.id,
            'initial_message': '¡Hola!'
        })
        self.assertRedirects(response, reverse('community:all_chats'))
        self.assertTrue(Chat.objects.filter(Q(user1=self.user, user2=self.user2) | Q(user1=self.user2, user2=self.user)).exists())

    def test_create_chat_request_with_existing_pending_request(self):
        response = self.client.post(reverse('community:create_private_chat'), {
            'selected_user': self.user3.id,
            'initial_message': 'Hola de nuevo'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ya existe una solicitud pendiente o aceptada entre estos usuarios.')

    def test_create_new_chat_request_after_rejected(self):
        ChatRequest.objects.filter(sender=self.user, receiver=self.user3).update(status='rejected')
        response = self.client.post(reverse('community:create_private_chat'), {
            'selected_user': self.user3.id,
            'initial_message': 'Intentémoslo otra vez'
        })
        self.assertRedirects(response, reverse('community:all_chats'))
        self.assertTrue(ChatRequest.objects.filter(sender=self.user, receiver=self.user3, initial_message='Intentémoslo otra vez').exists())


class ChatRequestTests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.user = CustomUser.objects.create_user(username='user1', password='password1', email="user1@example.com")
        self.user2 = CustomUser.objects.create_user(username='user2', password='password2', email="user2@example.com")
        self.user3 = CustomUser.objects.create_user(username='user3', password='password3', email="user3@example.com")

        # Iniciar sesión
        self.client = Client()
        self.client.login(username='user1', password='password1')

        # Crear una solicitud de chat
        self.chat_request = ChatRequest.objects.create(
            sender=self.user2,
            receiver=self.user,
            status='pending',
            initial_message="Hola, ¿podemos hablar sobre el producto?",
        )

    def test_accept_chat_request_with_product(self):
        """Test para aceptar una solicitud de chat con un producto."""
        response = self.client.post(reverse('community:accept_chat_request', args=[self.chat_request.id]))
        self.chat_request.refresh_from_db()
        
        # Verificar cambios en el estado de la solicitud
        self.assertEqual(self.chat_request.status, 'accepted')
        
        # Verificar que se haya creado un chat y un mensaje inicial
        chat = Chat.objects.filter(user1=self.user2, user2=self.user).first()
        self.assertIsNotNone(chat)
        self.assertEqual(chat.initial_message, "Hola, ¿podemos hablar sobre el producto?")
        

    def test_accept_chat_request_with_group_chat(self):
        """Test para aceptar una solicitud de chat grupal."""
        group_chat = GroupChat.objects.create(name='Group Test')
        self.chat_request.group_chat = group_chat
        self.chat_request.save()

        response = self.client.post(reverse('community:accept_chat_request', args=[self.chat_request.id]))
        self.chat_request.refresh_from_db()
        
        # Verificar que el usuario fue agregado al grupo
        chat_member = ChatMember.objects.filter(group_chat=group_chat, user=self.user).first()
        self.assertIsNotNone(chat_member)
        self.assertEqual(chat_member.user_type, 'normal')
        
        # Verificar mensaje del sistema
        message = Message.objects.filter(group_chat=group_chat, is_system_message=True).first()
        self.assertIsNotNone(message)
        self.assertIn(f'El usuario @{self.user} se ha unido al grupo.', message.content)

    def test_accept_chat_request_with_deletion(self):
        """Test para aceptar una solicitud de eliminación de chat."""
        chat = Chat.objects.create(user1=self.user2, user2=self.user)
        self.chat_request.is_delete_request = True
        self.chat_request.save()

        response = self.client.post(reverse('community:accept_chat_request', args=[self.chat_request.id]))
        self.chat_request.refresh_from_db()
        
        # Verificar que el chat fue eliminado
        self.assertFalse(Chat.objects.filter(id=chat.id).exists())
        
        # Verificar cambios en el estado de la solicitud
        self.assertEqual(self.chat_request.status, 'accepted')

    def test_reject_chat_request(self):
        """Test para rechazar una solicitud de chat."""
        response = self.client.post(reverse('community:reject_chat_request', args=[self.chat_request.id]))
        self.chat_request.refresh_from_db()
        
        # Verificar cambios en el estado de la solicitud
        self.assertEqual(self.chat_request.status, 'rejected')

    def test_invalid_chat_request(self):
        """Test para manejar una solicitud no válida o ya procesada."""
        self.chat_request.status = 'accepted'
        self.chat_request.save()

        response = self.client.post(reverse('community:accept_chat_request', args=[self.chat_request.id]))
        self.chat_request.refresh_from_db()
        
        # Verificar que el estado no cambió
        self.assertEqual(self.chat_request.status, 'accepted')

        # Verificar redirección
        self.assertRedirects(response, reverse('community:chat_requests'))

class ChatRequestsViewTests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.user = CustomUser.objects.create_user(username='user1', password='password1', email="user1@example.com")
        self.user2 = CustomUser.objects.create_user(username='user2', password='password2', email="user2@example.com")

        # Iniciar sesión
        self.client = Client()
        self.client.login(username='user1', password='password1')

        # Crear solicitudes de chat
        self.chat_request_received = ChatRequest.objects.create(
            sender=self.user2,
            receiver=self.user,
            status='pending',
            initial_message="Hola, ¿podemos hablar?"
        )

        self.chat_request_sent = ChatRequest.objects.create(
            sender=self.user,
            receiver=self.user2,
            status='pending',
            initial_message="Hola, me gustaría hablar contigo."
        )

    def test_chat_requests_render(self):
        """Test para verificar el renderizado de la vista chat_requests."""
        response = self.client.get(reverse('community:chat_requests'))
        
        # Verificar que la respuesta es 200
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se usó el template correcto
        self.assertTemplateUsed(response, 'community/chat_requests.html')
        
        # Verificar que las solicitudes pendientes y enviadas están en el contexto
        self.assertIn('pending_requests', response.context)
        self.assertIn('my_requests', response.context)
        self.assertIn('pending_requests_count', response.context)
        self.assertIn('complete_profile_alerts', response.context)
        
        # Verificar conteo de solicitudes pendientes
        pending_requests_count = response.context['pending_requests_count']
        self.assertEqual(pending_requests_count, 1)

        # Verificar solicitudes pendientes y enviadas
        pending_requests = response.context['pending_requests']
        my_requests = response.context['my_requests']
        self.assertIn(self.chat_request_received, pending_requests)
        self.assertIn(self.chat_request_sent, my_requests)

        # Verificar alertas de completar perfil
        self.assertEqual(response.context['complete_profile_alerts'], 5)


class ChatDetailViewTests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.user1 = CustomUser.objects.create_user(username="user1", password="password1", email="user1@example.com")
        self.user2 = CustomUser.objects.create_user(username="user2", password="password2", email="user2@example.com")
        self.user3 = CustomUser.objects.create_user(username="user3", password="password3", email="user3@example.com", city="Madrid")

        # Iniciar sesión como user1
        self.client = Client()
        self.client.login(username="user1", password="password1")

        # Crear un chat entre user1 y user2
        self.chat = Chat.objects.create(user1=self.user1, user2=self.user2)

        # Crear mensajes en el chat
        Message.objects.create(chat=self.chat, sender=self.user2, content="Hola user1", is_read=False)
        Message.objects.create(chat=self.chat, sender=self.user1, content="Hola user2", is_read=True)

        # Crear un chat grupal para user1
        self.group_chat = GroupChat.objects.create(name="Grupo 1")
        self.chat_member1 = ChatMember.objects.create(user=self.user1, group_chat=self.group_chat)
        self.group_chat.members.add(self.chat_member1)

    def test_chat_detail_renders_correctly(self):
        """Probar que la vista de detalles del chat se renderiza correctamente."""
        response = self.client.get(reverse("community:chat_detail", kwargs={"username": self.user2.username}))
        
        # Verificar código de respuesta
        self.assertEqual(response.status_code, 200)
        
        # Verificar template utilizado
        self.assertTemplateUsed(response, "community/chat_detail.html")
        
        # Verificar que las variables de contexto necesarias están presentes
        self.assertIn("complete_profile_alerts", response.context)
        self.assertIn("pending_requests_count", response.context)
        self.assertIn("current_chat", response.context)
        self.assertIn("chat_user", response.context)
        self.assertIn("private_chats", response.context)
        self.assertIn("messages", response.context)
        self.assertIn("all_my_chats", response.context)
        self.assertIn("country", response.context)
        self.assertIn("flag_image", response.context)
        self.assertIn("pending_chat_requests_count", response.context)
        self.assertIn("total_unread_count", response.context)

        # Verificar que las variables tienen datos esperados
        self.assertEqual(response.context["current_chat"], self.chat)
        self.assertEqual(response.context["chat_user"], self.user2)
        self.assertEqual(response.context["total_unread_count"], 0)

    def test_chat_detail_user_not_found(self):
        """Probar que la vista maneja usuarios no encontrados."""
        response = self.client.get(reverse("community:chat_detail", kwargs={"username": "nonexistent_user"}))
        
        # Verificar código de respuesta
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se utiliza el template correcto
        self.assertTemplateUsed(response, "user_not_found.html")

    def test_chat_detail_mark_messages_as_read(self):
        """Probar que los mensajes no leídos se marcan como leídos."""
        # Verificar que el mensaje inicial no está leído
        unread_message = Message.objects.filter(chat=self.chat, sender=self.user2, is_read=False).count()
        self.assertEqual(unread_message, 1)

        # Acceder a la vista de detalles del chat
        self.client.get(reverse("community:chat_detail", kwargs={"username": self.user2.username}))

        # Verificar que los mensajes ahora están marcados como leídos
        unread_message = Message.objects.filter(chat=self.chat, sender=self.user2, is_read=False).count()
        self.assertEqual(unread_message, 0)

    def test_chat_detail_send_message(self):
        """Probar que los mensajes se envían correctamente."""
        # Enviar un mensaje
        response = self.client.post(
            reverse("community:chat_detail", kwargs={"username": self.user2.username}),
            {"content": "¿Qué tal?"}
        )

        # Verificar redirección después de enviar
        self.assertEqual(response.status_code, 200)

        # Verificar que el mensaje fue creado
        new_message = Message.objects.filter(chat=self.chat, sender=self.user1, content="¿Qué tal?").count()
        self.assertEqual(new_message, 1)

    def test_group_chat_rendered_correctly(self):
        """Probar que los chats grupales se incluyen en el contexto."""
        response = self.client.get(reverse("community:chat_detail", kwargs={"username": self.user2.username}))

        # Verificar que el chat grupal está en el contexto
        self.assertIn(self.group_chat, response.context["all_my_chats"])


class CityGroupChatTests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.user1 = CustomUser.objects.create_user(username="user1", password="password1", email="user1@example.com", city="Madrid")
        self.user2 = CustomUser.objects.create_user(username="user2", password="password2", email="user2@example.com", city="Madrid")
        self.user3 = CustomUser.objects.create_user(username="user3", password="password3", email="user3@example.com", city="Barcelona")

        # Cliente para el usuario 1
        self.client = Client()
        self.client.login(username="user1", password="password1")

        # Crear un chat grupal de ciudad para Madrid
        self.group_chat_madrid = GroupChat.objects.create(name="Madrid", description="Grupo de chat para Madrid")
        self.chat_member1 = ChatMember.objects.create(user=self.user1, group_chat=self.group_chat_madrid)
        self.chat_member2 = ChatMember.objects.create(user=self.user2, group_chat=self.group_chat_madrid)
        self.group_chat_madrid.members.add(self.chat_member1, self.chat_member2)

        # Crear mensajes en el grupo
        Message.objects.create(group_chat=self.group_chat_madrid, sender=self.user2, content="Bienvenido al grupo", is_read=False)

    def test_group_chat_view_status_code(self):
        """Verifica que el endpoint de la vista devuelva un código 200."""
        response = self.client.get(reverse('community:city_group_chat', args=["Madrid"]))
        self.assertEqual(response.status_code, 200)

    def test_group_chat_creation(self):
        """Verifica que se crea el grupo correctamente si no existe."""
        response = self.client.get(reverse('community:city_group_chat', args=["Barcelona"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GroupChat.objects.filter(name="Barcelona").exists())

    def test_user_added_to_group_chat(self):
        """Verifica que el usuario se añade al grupo si no es miembro."""
        response = self.client.get(reverse('community:city_group_chat', args=["Barcelona"]))
        self.assertEqual(response.status_code, 200)
        group_chat = GroupChat.objects.get(name="Barcelona")
        self.assertTrue(ChatMember.objects.filter(user=self.user1, group_chat=group_chat).exists())

    def test_unread_messages_marked_as_read(self):
        """Verifica que los mensajes no leídos se marcan como leídos al acceder al chat."""
        response = self.client.get(reverse('community:city_group_chat', args=["Madrid"]))
        unread_messages = self.group_chat_madrid.group_messages.filter(is_read=False)
        self.assertFalse(unread_messages.exists())

    def test_messages_displayed_in_order(self):
        """Verifica que los mensajes del grupo se muestran en orden de timestamp."""
        Message.objects.create(group_chat=self.group_chat_madrid, sender=self.user1, content="Hola a todos", is_read=False)
        response = self.client.get(reverse('community:city_group_chat', args=["Madrid"]))
        messages = response.context['messages']
        timestamps = [msg.timestamp for msg in messages]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_post_message_to_group_chat(self):
        """Verifica que un usuario puede enviar un mensaje al chat grupal."""
        response = self.client.post(reverse('community:city_group_chat', args=["Madrid"]), {'content': "Este es un mensaje de prueba"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Message.objects.filter(group_chat=self.group_chat_madrid, sender=self.user1, content="Este es un mensaje de prueba").exists())

    def test_context_data_correctness(self):
        """Verifica que los datos relevantes se pasan al contexto."""
        response = self.client.get(reverse('community:city_group_chat', args=["Madrid"]))
        self.assertIn('complete_profile_alerts', response.context)
        self.assertIn('pending_requests_count', response.context)
        self.assertIn('all_my_chats', response.context)
        self.assertIn('group_chat', response.context)
        self.assertIn('messages', response.context)


class CreateGroupChatTests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.user1 = CustomUser.objects.create_user(username="user1", password="password1", email="user1@example.com")
        self.user2 = CustomUser.objects.create_user(username="user2", password="password2", email="user2@example.com")
        self.user3 = CustomUser.objects.create_user(username="user3", password="password3", email="user3@example.com")

        # Cliente de prueba
        self.client = Client()
        self.client.login(username="user1", password="password1")

        self.url = reverse('community:create_group_chat')

    def test_create_group_chat_success(self):
        # Datos válidos para crear un grupo
        data = {
            'group_name': 'Grupo de prueba',
            'group_description': 'Descripción del grupo',
            'initial_message': 'Hola a todos',
            'selected_users': f'{self.user2.id},{self.user3.id}',
        }
        response = self.client.post(self.url, data)

        # Verificar que el grupo se creó
        self.assertEqual(GroupChat.objects.count(), 1)
        group_chat = GroupChat.objects.first()
        self.assertEqual(group_chat.name, 'Grupo de prueba')
        self.assertEqual(group_chat.description, 'Descripción del grupo')

        # Verificar que los miembros del grupo se crearon correctamente
        self.assertEqual(ChatMember.objects.filter(group_chat=group_chat).count(), 1)  # Admin incluido
        self.assertEqual(ChatRequest.objects.filter(group_chat=group_chat).count(), 2)  # Para user2 y user3

        # Verificar que se creó el mensaje inicial
        self.assertEqual(Message.objects.filter(group_chat=group_chat).count(), 1)
        self.assertEqual(Message.objects.first().content, 'Hola a todos')

        # Verificar redirección
        self.assertRedirects(response, reverse('community:all_chats'))

    def test_missing_group_name(self):
        data = {
            'group_description': 'Descripción del grupo',
            'initial_message': 'Hola a todos',
            'selected_users': f'{self.user2.id},{self.user3.id}',
        }
        response = self.client.post(self.url, data)
        self.assertContains(response, 'Escribe un nombre para el grupo')
        self.assertEqual(GroupChat.objects.count(), 0)

    def test_missing_initial_message(self):
        data = {
            'group_name': 'Grupo de prueba',
            'group_description': 'Descripción del grupo',
            'selected_users': f'{self.user2.id},{self.user3.id}',
        }
        response = self.client.post(self.url, data)
        self.assertContains(response, 'Escribe un mensaje inicial para el grupo')
        self.assertEqual(GroupChat.objects.count(), 0)

    def test_invalid_user_id(self):
        data = {
            'group_name': 'Grupo de prueba',
            'group_description': 'Descripción del grupo',
            'initial_message': 'Hola a todos',
            'selected_users': '999999',  # Usuario inexistente
        }
        response = self.client.post(self.url, data)
        self.assertTemplateUsed(response, 'user_not_found.html')
        self.assertEqual(GroupChat.objects.count(), 1)


class GroupChatDetailsTests(TestCase):
    def setUp(self):
        # Crear usuarios
        self.user1 = CustomUser.objects.create_user(username="user1", password="password1", email="user1@example.com", city="Madrid")
        self.user2 = CustomUser.objects.create_user(username="user2", password="password2", email="user2@example.com", city="Barcelona")
        self.user3 = CustomUser.objects.create_user(username="user3", password="password3", email="user3@example.com", city="Madrid")
        
        # Crear grupo
        self.group_chat = GroupChat.objects.create(name="Grupo de prueba", description="Descripción del grupo")
        
        # Agregar miembros al grupo
        ChatMember.objects.create(group_chat=self.group_chat, user=self.user1, user_type="admin")
        ChatMember.objects.create(group_chat=self.group_chat, user=self.user2)
        
        # Crear cliente y loguear
        self.client = Client()
        self.client.login(username="user1", password="password1")

        # Ruta de la vista
        self.url = reverse('community:group_chat_details', kwargs={'name': self.group_chat.name})

    def test_load_group_chat_details(self):
        # Acceder a la vista
        response = self.client.get(self.url)
        
        # Verificar que carga correctamente
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/group_chat.html')
        
        # Verificar que el grupo está en el contexto
        self.assertEqual(response.context['group_chat'], self.group_chat)
        
        # Verificar que los mensajes se incluyen
        self.assertIn('messages', response.context)
        self.assertEqual(response.context['messages'].count(), 0)

    def test_unread_messages_marked_as_read(self):
        # Crear mensajes no leídos
        Message.objects.create(group_chat=self.group_chat, sender=self.user2, content="Mensaje 1", is_read=False)
        Message.objects.create(group_chat=self.group_chat, sender=self.user2, content="Mensaje 2", is_read=False)

        # Acceder a la vista
        self.client.get(self.url)

        # Verificar que los mensajes no leídos ahora están marcados como leídos
        unread_messages = Message.objects.filter(group_chat=self.group_chat, is_read=False)
        self.assertEqual(unread_messages.count(), 0)

    def test_send_message(self):
        # Enviar un mensaje usando POST
        data = {'content': 'Nuevo mensaje'}
        response = self.client.post(self.url, data)

        # Verificar que el mensaje se ha creado
        self.assertEqual(Message.objects.filter(group_chat=self.group_chat).count(), 1)
        message = Message.objects.first()
        self.assertEqual(message.content, 'Nuevo mensaje')
        self.assertEqual(message.sender, self.user1)

        # Verificar redirección o respuesta correcta
        self.assertEqual(response.status_code, 200)

    def test_no_group_found(self):
        # Intentar acceder a un grupo inexistente
        invalid_url = reverse('community:group_chat_details', kwargs={'name': 'GrupoInexistente'})
        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, 200)

    def test_country_and_flag_in_context(self):
        # Mock de datos de ciudades
        city_data_mock = {
            'Madrid': {'country': 'España', 'flag': 'spain.png'},
            'Barcelona': {'country': 'España', 'flag': 'spain.png'},
        }
        
        with patch('main.views.city_data', city_data_mock):
            response = self.client.get(self.url)

        # Verificar que la bandera y el país están en el contexto
        self.assertEqual(response.context['country'], 'España')
        self.assertEqual(response.context['flag_image'], 'spain.png')
