from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from main.community.models import Chat, GroupChat, ChatRequest, ChatMember
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
