from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Chat, ChatRequest, GroupChat, GroupChatMember, Message
from main.models import Follow, CustomUser, FollowRequest
from main.views import alertas_completar_perfil
from main.views import city_data
from itertools import chain
from django.db import models

@login_required
def all_chats(request):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    all_groups_chats = GroupChat.objects.filter(members=request.user).exclude(name=request.user.city)
    pinned_chat = GroupChat.objects.filter(name=request.user.city).first()

    city_info = city_data.get(request.user.city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    all_my_chats = [pinned_chat] + sorted(
        chain(
            private_chats.annotate(last_message_date=models.Max('messages__timestamp')),
            all_groups_chats.annotate(last_message_date=models.Max('group_messages__timestamp'))
        ),
        key=lambda chat: chat.last_message_date if chat.last_message_date else chat.created_at,
        reverse=True
    )

    return render(request, 'community/all_chats.html', {
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'private_chats': private_chats,
        'all_my_chats': all_my_chats,
        'country': country,
        'flag_image': flag_image,
        'pending_chat_requests_count': pending_chat_requests_count,
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
        
        initial_message = request.POST.get('initial_message', '')
        if initial_message == '':
            error_messages.append('Escribe un mensaje inicial para la solicitud de chat')
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
                    (Q(sender=request.user) & Q(receiver=selected_user) & Q(group_chat__isnull=True)) |
                    (Q(sender=selected_user) & Q(receiver=request.user) & Q(group_chat__isnull=True))
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
    message = ""
    if chat_request.status == 'pending':
        if chat_request.product:
            initial = "He abierto este chat para hablar sobre el producto"
            chat = Chat.objects.create(user1=chat_request.sender, user2=chat_request.receiver, initial_message=initial)
            message = Message.objects.create(chat=chat, sender=chat_request.sender, content=chat_request.initial_message, product=chat_request.product)
            chat_request.status = 'accepted'
            chat_request.save()
        elif chat_request.renting:
            initial = "He abierto este chat para hablar sobre el alquiler"
            chat = Chat.objects.create(user1=chat_request.sender, user2=chat_request.receiver, initial_message=initial)
            message = Message.objects.create(chat=chat, sender=chat_request.sender, content=chat_request.initial_message, renting=chat_request.renting)
            chat_request.status = 'accepted'
            chat_request.save()
        elif chat_request.group_chat:
            chat_request.group_chat.members.add(chat_request.receiver)
            member = GroupChatMember.objects.get(user=chat_request.receiver, group_chat=chat_request.group_chat)
            member.membership_type = 'normal'
            member.save()
            chat_request.status = 'accepted'
            chat_request.save()
        else:
            Chat.objects.create(user1=chat_request.sender, user2=chat_request.receiver, initial_message=chat_request.initial_message)
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


@login_required
def chat_detail(request, username):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    all_groups_chats = GroupChat.objects.filter(members=request.user).exclude(name=request.user.city)
    pinned_chat = GroupChat.objects.filter(name=request.user.city).first()

    city_info = city_data.get(request.user.city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    all_my_chats = [pinned_chat] + sorted(
        chain(
            private_chats.annotate(last_message_date=models.Max('messages__timestamp')),
            all_groups_chats.annotate(last_message_date=models.Max('group_messages__timestamp'))
        ),
        key=lambda chat: chat.last_message_date if chat.last_message_date else chat.created_at,
        reverse=True
    )

    try:
        chat_user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        return render(request, "user_not_found.html", {'complete_profile_alerts': complete_profile_alerts, 'pending_requests_count': pending_requests_count})
    
    current_chat = Chat.objects.filter(
        (Q(user1=request.user, user2=chat_user) | Q(user1=chat_user, user2=request.user))
    ).first()

    messages = current_chat.messages.order_by('timestamp')

    # Manejo de envío de mensaje
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Message.objects.create(chat=current_chat, sender=request.user, content=content)

    return render(request, "community/chat_detail.html", {
        'complete_profile_alerts': complete_profile_alerts, 
        'pending_requests_count': pending_requests_count,
        'current_chat': current_chat,
        'chat_user': chat_user,
        'private_chats': private_chats,
        'messages': messages,
        'all_my_chats': all_my_chats,
        'country': country,
        'flag_image': flag_image,
        'pending_chat_requests_count': pending_chat_requests_count,
        } )

@login_required
def city_group_chat(request, city):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()


    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    all_groups_chats = GroupChat.objects.filter(members=request.user).exclude(name=request.user.city)
    pinned_chat = GroupChat.objects.filter(name=request.user.city).first()

    all_my_chats = [pinned_chat] + sorted(
        chain(
            private_chats.annotate(last_message_date=models.Max('messages__timestamp')),
            all_groups_chats.annotate(last_message_date=models.Max('group_messages__timestamp'))
        ),
        key=lambda chat: chat.last_message_date if chat.last_message_date else chat.created_at,
        reverse=True
    )

    city_info = city_data.get(request.user.city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    group_chat = GroupChat.objects.filter(name=city).first()

    if city==request.user.city and request.user not in group_chat.members.all():
        group_chat.members.add(request.user)

    if not group_chat:
        group_chat = GroupChat.objects.create(name=city, description=f"Grupo de chat para la ciudad de {city}", image=flag_image)

    # Verifica si el usuario ya está en el grupo
    group_member, created = GroupChatMember.objects.get_or_create(user=request.user, group_chat=group_chat)
    
    # Actualiza el tipo de membresía según la ciudad del usuario
    if request.user.city == city:
        group_member.membership_type = 'normal'
    else:
        group_member.membership_type = 'external'
    group_member.save()

    messages = group_chat.group_messages.order_by('timestamp')

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Message.objects.create(group_chat=group_chat, sender=request.user, content=content)

    return render(request, "community/group_chat.html", {
        'complete_profile_alerts': complete_profile_alerts, 
        'pending_requests_count': pending_requests_count,
        'all_my_chats': all_my_chats,
        'group_chat': group_chat,
        'messages': messages,
        'country': country,
        'flag_image': flag_image,
        'pending_chat_requests_count': pending_chat_requests_count,
    })

@login_required
def create_group_chat(request):
    query = request.GET.get('q')
    users = CustomUser.objects.exclude(username=request.user.username)
    error_messages = []
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    
    if query:
        users = users.filter(username__icontains=query)

    if request.method == 'POST':
        selected_users = request.POST.get('selected_users', '').split(',')
        if not selected_users:
            error_messages.append('Selecciona al menos un usuario para poder iniciar un chat grupal')
            return render(request, 'community/create_group_chat.html', {'users': users, 'error_messages': error_messages})

        group_name = request.POST.get('group_name', '')
        if group_name == '':
            error_messages.append('Escribe un nombre para el grupo')
            return render(request, 'community/create_group_chat.html', {'users': users, 'error_messages': error_messages})
        
        initial_message = request.POST.get('initial_message', '')
        if initial_message == '':
            error_messages.append('Escribe un mensaje inicial para el grupo')
            return render(request, 'community/create_group_chat.html', {'users': users, 'error_messages': error_messages})

        # Create the group chat
        group_chat = GroupChat.objects.create(name=group_name, description=request.POST.get('group_description', ''), initial_message=initial_message, image=request.FILES.get('group_image', None), is_friends_group = True)
        group_chat.members.add(request.user)
        admin_member = GroupChatMember.objects.get(user=request.user, group_chat=group_chat)
        admin_member.membership_type = 'admin'
        admin_member.save()

        # Add the selected members to the group chat
        for user_id in selected_users:
            try:
                user = CustomUser.objects.get(id=int(user_id))  # Convert the user_id to an integer
                ChatRequest.objects.create(sender=request.user, receiver=user, initial_message=initial_message, group_chat=group_chat)
                
            except CustomUser.DoesNotExist:
                return render(request, "user_not_found.html", {'complete_profile_alerts': complete_profile_alerts, 'pending_requests_count': pending_requests_count})

        Message.objects.create(group_chat=group_chat, sender=request.user, content=initial_message)

        return redirect('community:all_chats')

    return render(request, 'community/create_group_chat.html', {'users': users, 'error_messages': error_messages})

@login_required
def group_chat_details(request, name):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user))
    all_groups_chats = GroupChat.objects.filter(members=request.user).exclude(name=request.user.city)
    pinned_chat = GroupChat.objects.filter(name=request.user.city).first()

    city_info = city_data.get(request.user.city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    all_my_chats = [pinned_chat] + sorted(
        chain(
            private_chats.annotate(last_message_date=models.Max('messages__timestamp')),
            all_groups_chats.annotate(last_message_date=models.Max('group_messages__timestamp'))
        ),
        key=lambda chat: chat.last_message_date if chat.last_message_date else chat.created_at,
        reverse=True
    )


    group_chat = GroupChat.objects.filter(name=name).first()
    
    messages = group_chat.group_messages.order_by('timestamp')

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Message.objects.create(group_chat=group_chat, sender=request.user, content=content)

    return render(request, "community/group_chat.html", {
        'complete_profile_alerts': complete_profile_alerts, 
        'pending_requests_count': pending_requests_count,
        'all_my_chats': all_my_chats,
        'group_chat': group_chat,
        'messages': messages,
        'country': country,
        'flag_image': flag_image,
        'pending_chat_requests_count': pending_chat_requests_count,
    })

@login_required
def delete_group(request, name):
    error_messages = []
    group_chat = GroupChat.objects.filter(name=name).first()
    if not group_chat:
        error_messages.append('El grupo no existe')
        return render(request, 'community/all_chats.html', {'error_messages': error_messages})
    
    if GroupChatMember.objects.filter(user=request.user, group_chat=group_chat, membership_type='admin').exists():
        group_chat.delete()
    else:
        error_messages.append('No tienes permisos para eliminar este grupo')
        return render(request, 'community/all_chats.html', {'error_messages': error_messages})
    
    return redirect('community:all_chats')

