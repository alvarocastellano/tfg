from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from .models import Chat, ChatRequest, Message
from main.models import Follow, CustomUser, FollowRequest
from main.views import alertas_completar_perfil
from django.contrib import messages

@login_required
def all_chats(request):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    return render(request, 'community/all_chats.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'private_chats': private_chats
        })

@login_required
def create_private_chat(request):
    query = request.GET.get('q')
    users = CustomUser.objects.exclude(username=request.user.username)
    error_messages = []
    
    # Filtrar usuarios por nombre si existe un query
    if query:
        users = users.filter(username__icontains=query)

    if request.method == 'POST':
        selected_user_id = request.POST.get('selected_user')
        if not selected_user_id:
            error_messages.append('Selecciona a un usuario para poder iniciar un chat')
            return render(request, 'community/create_chat.html', {'users': users, 'error_messages': error_messages})
        else:
            initial_message = request.POST.get('initial_message', '')

            # Obtener el usuario seleccionado
            selected_user = get_object_or_404(CustomUser, id=selected_user_id)

            if Chat.objects.filter(Q(user1=request.user, user2=selected_user) | Q(user1=selected_user, user2=request.user)).exists():
                error_messages.append('Ya existe un chat activo con este usuario.')
                return render(request, 'community/create_chat.html', {'users': users, 'error_messages': error_messages})

            # Verificar Follow mutua
            follows_mutually = Follow.objects.filter(
                follower=request.user, following=selected_user
            ).exists() and Follow.objects.filter(
                follower=selected_user, following=request.user
            ).exists()

            if follows_mutually:
                # Si hay follow mutuo, crear un chat directamente
                if Chat.objects.filter(
                    user1=request.user, user2=selected_user
                ).exists():
                    error_messages.append('Ya existe un chat activo con este usuario.')
                    return render(request, 'community/create_chat.html', {'users': users, 'error_messages': error_messages})
                
                else:
                    chat, created = Chat.objects.get_or_create(
                        user1=request.user, user2=selected_user, initial_message=initial_message
                    )
                    # Redirigir a la página del chat (ejemplo)
                    return redirect('community:all_chats')
            else:
                existing_request = ChatRequest.objects.filter(
                    (Q(sender=request.user) & Q(receiver=selected_user)) |
                    (Q(sender=selected_user) & Q(receiver=request.user))
                ).order_by('-created_at').first()

                if existing_request:
                    # Si la solicitud existe, comprobar su estado
                    if existing_request.status in ['accepted', 'pending']:
                        error_messages.append('Ya existe una solicitud pendiente o aceptada entre estos usuarios.')
                        return render(request, 'community/create_chat.html', {'users': users, 'error_messages': error_messages})
                    elif existing_request.status == 'rejected':
                        # Si la solicitud fue rechazada, se puede crear una nueva
                        ChatRequest.objects.create(
                            sender=request.user,
                            receiver=selected_user,
                            initial_message=initial_message
                        )
                        return redirect('community:all_chats')
                else:
                    # Si no existe una solicitud previa, crear una nueva
                    ChatRequest.objects.create(
                        sender=request.user,
                        receiver=selected_user,
                        initial_message=initial_message
                    )
                    return redirect('community:all_chats')
    return render(request, 'community/create_chat.html', {'users': users, 'error_messages': error_messages})

@login_required
def accept_chat_request(request, request_id):
    chat_request = get_object_or_404(ChatRequest, id=request_id, receiver=request.user)
    if chat_request.status == 'pending':
        Chat.objects.create(user1=chat_request.sender, user2=chat_request.receiver)
        chat_request.status = 'accepted'
        chat_request.save()
    return redirect('community:chat_requests')

@login_required
def reject_chat_request(request, request_id):
    chat_request = get_object_or_404(ChatRequest, id=request_id, receiver=request.user)
    if chat_request.status == 'pending':
        chat_request.status = 'rejected'
        chat_request.save()
    return redirect('community:chat_requests')

@login_required
def chat_requests(request):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    
    pending_requests = request.user.chat_requests_received.filter(status='pending')

    my_requests = request.user.chat_requests_sent.filter().order_by('-created_at')

    return render(request, 'community/chat_requests.html', {
        'pending_requests': pending_requests,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'my_requests': my_requests
        })



def chat_detail(request, username):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user))

    try:
        chat_user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        return render(request, "user_not_found.html", {'complete_profile_alerts': complete_profile_alerts, 'pending_requests_count': pending_requests_count})
    
    chat = Chat.objects.filter(
        (Q(user1=request.user, user2=chat_user) | Q(user1=chat_user, user2=request.user))
    ).first()

    messages = chat.messages.order_by('timestamp')

    # Manejo de envío de mensaje
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Message.objects.create(chat=chat, sender=request.user, content=content)

    return render(request, "community/chat_detail.html", {
        'complete_profile_alerts': complete_profile_alerts, 
        'pending_requests_count': pending_requests_count,
        'chat': chat,
        'chat_user': chat_user,
        'private_chats': private_chats,
        'messages': messages
        } )




