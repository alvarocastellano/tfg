from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from .models import Chat, ChatRequest
from main.models import Follow, CustomUser, FollowRequest
from main.views import alertas_completar_perfil
from django.contrib import messages

@login_required
def all_chats(request):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(user1=request.user)

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
                        user1=request.user, user2=selected_user
                    )
                    # Redirigir a la página del chat (ejemplo)
                    return redirect('community:all_chats')
            else:
                existing_request = ChatRequest.objects.filter(
                    sender=request.user, receiver=selected_user
                ).exists()

                if not existing_request:
                    # Si no hay follow mutuo, crear una solicitud de chat
                    ChatRequest.objects.create(
                        sender=request.user,
                        receiver=selected_user,
                        initial_message=initial_message
                    )
                    return redirect('community:all_chats')
                else:
                    error_messages.append('Ya hay una solicitud de chat pendiente con este usuario, no puedes enviar otra.')
                    return render(request, 'community/create_chat.html', {'users': users, 'error_messages': error_messages})
    return render(request, 'community/create_chat.html', {'users': users, 'error_messages': error_messages})

