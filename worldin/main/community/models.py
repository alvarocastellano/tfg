from django.conf import settings
from django.db import models
from main.market.models import Product, Rental

# Modelo para el Chat
class Chat(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chats_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chats_user2', on_delete=models.CASCADE)
    initial_message = models.TextField(blank=True)
    products = models.ManyToManyField(Product, blank=True, related_name='associated_chats')
    rentings = models.ManyToManyField(Rental, blank=True, related_name='rentings_associated_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')  # Un chat único entre dos usuarios

    def __str__(self):
        return f"Chat between {self.user1.username} and {self.user2.username}"

# Modelo para la solicitud de chat
class ChatRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_requests_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_requests_received', on_delete=models.CASCADE)
    initial_message = models.TextField(blank=False)
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
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='product_messages')
    renting = models.ForeignKey(Rental, null=True, blank=True, on_delete=models.SET_NULL, related_name='renting_messages')
    is_system_message = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"