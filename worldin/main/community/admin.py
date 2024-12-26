from django.contrib import admin
from .models import Chat, ChatRequest, Message, GroupChat, GroupChatMember


@admin.register(Chat)
class IndividualChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'user1', 'user2')  # Campos para búsqueda.

@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'status')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'sender')  # Campos para búsqueda.

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'content', 'product', 'renting')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'sender')  # Campos para búsqueda.

@admin.register(GroupChat)
class GroupChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'name')  # Campos para búsqueda.

@admin.register(GroupChatMember)
class GroupChatMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'group_chat', 'membership_type')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'user')