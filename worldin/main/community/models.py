from django.conf import settings
from django.db import models
from main.market.models import Product, Rental
from main.models import CustomUser

# Modelo para el Chat
class Chat(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chats_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chats_user2', on_delete=models.CASCADE)
    initial_message = models.TextField(blank=True)
    products = models.ManyToManyField(Product, blank=True, related_name='associated_chats')
    rentings = models.ManyToManyField(Rental, blank=True, related_name='rentings_associated_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    is_group = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user1', 'user2')  # Un chat único entre dos usuarios

    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"

class GroupChat(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    image = models.ImageField(upload_to='group_chat_pictures/', blank=True, null=True)
    initial_message = models.TextField(blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_group = models.BooleanField(default=True)
    is_friends_group = models.BooleanField(default=False)

    def __str__(self):
        return f"Group Chat: {self.name}"
    
class ChatMember(models.Model):
    USER_TYPE_CHOICES = [
        ('admin', 'Administrador'),
        ('normal', 'Normal'),
        ('external', 'Externo'),
    ]

    group_chat = models.ForeignKey('GroupChat', on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='normal')

    def __str__(self):
        return f"{self.user.username} in {self.group_chat.name} ({self.get_user_type_display()})"

    

# Modelo para la solicitud de chat
class ChatRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_requests_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_requests_received', on_delete=models.CASCADE)
    initial_message = models.TextField(blank=False)
    group_chat = models.ForeignKey(GroupChat, null=True, blank=True, on_delete=models.CASCADE, related_name='group_requests')
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='chatrequests')
    renting = models.ForeignKey(Rental, null=True, blank=True, on_delete=models.SET_NULL, related_name='rentings_chatrequests')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pendiente'),
            ('accepted', 'Aceptada'),
            ('rejected', 'Rechazada')
        ],
        default='pending'
    )

    def __str__(self):
        return f"Chat request from {self.sender.username} to {self.receiver.username}"
    
class Message(models.Model):
    chat = models.ForeignKey(Chat, null=True, blank=True, related_name='messages', on_delete=models.CASCADE)
    group_chat = models.ForeignKey(GroupChat, null=True, blank=True, on_delete=models.CASCADE, related_name='group_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='product_messages')
    renting = models.ForeignKey(Rental, null=True, blank=True, on_delete=models.SET_NULL, related_name='renting_messages')
    is_system_message = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"