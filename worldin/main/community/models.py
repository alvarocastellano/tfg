from django.conf import settings
from django.db import models

# Modelo para el Chat
class Chat(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chats_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chats_user2', on_delete=models.CASCADE)
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
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('sender', 'receiver')  # Una sola solicitud entre dos usuarios a la vez

    def __str__(self):
        return f"Chat request from {self.sender.username} to {self.receiver.username}"
