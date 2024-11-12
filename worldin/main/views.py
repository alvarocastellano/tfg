from django.shortcuts import  render
from worldin.forms import CustomUserCreationForm, CustomAuthenticationForm
from django.shortcuts import  render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import CustomUser, Hobby, Follow, FollowRequest
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib import messages
from datetime import datetime
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.contrib.messages import get_messages
from dateutil.relativedelta import relativedelta

def home(request):
    return render(request, 'home.html')

def contact_us(request):
    return render(request, 'contact_us.html')

def policy(request):
    return render(request, 'policy.html')

def usage(request):
    return render(request, 'usage.html')

@never_cache
def login_user(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('world')
        else:
            print(form.errors)
    else:
        form = CustomAuthenticationForm(request)
    return render(request, 'login.html', {'form': form})



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            if password1 == password2:
                user = form.save(commit=False)
                user.password = make_password(password1)
                user.is_active = False  # Desactivar la cuenta hasta confirmar
                user.save()

                # Generar un código de confirmación
                confirmation_code = get_random_string(6, allowed_chars='0123456789')
                request.session['confirmation_code'] = confirmation_code
                request.session['user_id'] = user.id

                message = f"""
                ¡BIENVENID@ A WORLDIN!
                Necesitamos que verifiques tu cuenta para completar tu registro.

                Tu código de confirmación es: {confirmation_code}

                Si no has registrado una nueva cuenta en Worldin, puedes obviar este mensaje.

                Atte. El equipo de Worldin
                """

                # Enviar el código por email
                send_mail(
                    'Confirma tu cuenta en Worldin',
                    message,
                    'noreply.confirmation.worldin@gmail.com',
                    [user.email],
                    fail_silently=False,
                )

                return redirect('confirm_account')
            else:
                form.add_error('password2', 'Las contraseñas no coinciden')

    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

@never_cache
def confirm_account(request):
    if request.method == 'POST':
        input_code = request.POST.get('code')
        session_code = request.session.get('confirmation_code')
        user_id = request.session.get('user_id')

        if input_code == session_code:
            # Activar la cuenta
            user = CustomUser.objects.get(id=user_id)
            user.is_active = True
            user.save()
            del request.session['confirmation_code']  # Limpiar la sesión
            del request.session['user_id']
            
            # Establecer el backend antes de iniciar sesión
            user.backend = 'django.contrib.auth.backends.ModelBackend'  # o 'allauth.account.auth_backends.AuthenticationBackend' si usas allauth

            # Loguear al usuario
            login(request, user)  
            return redirect('world')  # Redirigir a la página principal
        else:
            return render(request, 'confirm_account.html', {'error': 'Código incorrecto'})

    return render(request, 'confirm_account.html')

def password_reset(request):
    return render(request, 'password_reset.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


def world_page(request):
    user_city = None
    total_alerts = 0

    
    if request.user.is_authenticated:
        user = request.user
        complete_profile_alerts = 0
        pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

        if user.birthday is None:
            complete_profile_alerts+=1
        
        if user.city=="":
            complete_profile_alerts+=1

        if user.description=="":
            complete_profile_alerts+=1
        
        if user.profile_picture=="":
            complete_profile_alerts+=1

        if len(user.aficiones.all()) == 0:
            complete_profile_alerts+=1

        total_alerts = pending_requests_count + complete_profile_alerts

        user_city = request.user.city.split(',')[0] if request.user.city else None

    else:
        pending_requests_count = 0

    context = {
        'user_city': user_city,
        'total_alerts': total_alerts,
    }
    return render(request, 'world.html', context)

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email', '').lower()
        User = get_user_model()

        # Limpiar mensajes existentes
        storage = get_messages(request)
        list(storage)  # Esto limpia los mensajes previos

        try:
            # Verificar si ya existe una cuenta con ese correo electrónico
            existing_user = User.objects.get(email=email)
            sociallogin.state['process'] = 'login'
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # Si no existe el usuario, redirigir al formulario de registro en lugar de crear uno nuevo
            return redirect('register')

        # Si existe, continuar con el inicio de sesión
        return super().pre_social_login(request, sociallogin)


@login_required
def profile(request):
    user = request.user
    complete_profile_alerts = 0

    # Calcular la edad
    if user.birthday:
        birthday_date = datetime.strptime(user.birthday.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
        today = datetime.today().date()
        age = relativedelta(today, birthday_date).years

    else:
        age = None
   

    if user.birthday is None:
        complete_profile_alerts+=1
    
    if user.city=="":
        complete_profile_alerts+=1

    if user.description=="":
        complete_profile_alerts+=1
    
    if user.profile_picture=="":
        complete_profile_alerts+=1

    if len(user.aficiones.all()) == 0:
        complete_profile_alerts+=1

    # Contar seguidores y seguidos
    followers_count = user.followers.count()  # Suponiendo que tienes una relación de muchos a muchos
    following_count = user.following.count()  # Suponiendo que tienes una relación de muchos a muchos

    pending_requests_count = FollowRequest.objects.filter(receiver=user, status='pending').count()

    total_alerts = pending_requests_count + complete_profile_alerts

    return render(request, 'my_profile.html', {
        'user': user,
        'age': age,
        'followers_count': followers_count,
        'following_count': following_count,
        'pending_requests_count': pending_requests_count,
        'complete_profile_alerts': complete_profile_alerts,
        'total_alerts' : total_alerts,
    })

def is_profile_complete(user):
    return (
        user.birthday is not None and
        user.city != "" and
        user.description != "" and
        user.profile_picture != "" and
        user.aficiones.exists()
    )

@login_required
def edit_profile(request):
    available_hobbies = Hobby.objects.all()
    error_messages = []
    complete_profile_alerts = 0

    if request.user.birthday is None:
        complete_profile_alerts += 1
    if request.user.city == "":
        complete_profile_alerts += 1
    if request.user.description == "":
        complete_profile_alerts += 1
    if request.user.profile_picture == "":
        complete_profile_alerts += 1
    if len(request.user.aficiones.all()) == 0:
        complete_profile_alerts += 1

    if request.method == 'POST':
        user = request.user
        selected_hobbies = request.POST.getlist('hobbies')

        # Verificar número de aficiones seleccionadas
        if len(selected_hobbies) > 7:
            error_messages.append('No puedes seleccionar más de 7 aficiones.')
            return render(request, 'edit_profile.html', {
                'user': user,
                'available_hobbies': available_hobbies,
                'error_messages': error_messages,
                'complete_profile_alerts': complete_profile_alerts
            })

        # Actualizar aficiones
        user.aficiones.set(Hobby.objects.filter(id__in=selected_hobbies))

        # Procesar datos del formulario
        new_username = request.POST.get('username')

        # Verificar si el nombre de usuario es único
        if CustomUser.objects.filter(username=new_username).exclude(id=user.id).exists():
            error_messages.append('El nombre de usuario ya está en uso.')
            return render(request, 'edit_profile.html', {
                'user': user,
                'available_hobbies': available_hobbies,
                'error_messages': error_messages,
                'complete_profile_alerts': complete_profile_alerts
            })

        user.username = new_username
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('name')
        user.last_name = request.POST.get('surname')

        if not user.username or not user.email or not user.first_name or not user.last_name:
            error_messages.append('Por favor, completa todos los campos obligatorios, marcados con "*".')
            return render(request, 'edit_profile.html', {
                'user': user,
                'available_hobbies': available_hobbies,
                'error_messages': error_messages,
                'complete_profile_alerts': complete_profile_alerts
            })

        # Procesar cumpleaños
        birthday = request.POST.get('birthday')
        if birthday:
            try:
                birthday_date = datetime.strptime(birthday, '%Y-%m-%d').date()
                today = datetime.today().date()
                age = relativedelta(today, birthday_date).years

                # Validar la edad
                if birthday_date > today:
                    error_messages.append("La fecha de nacimiento no puede ser en el futuro.")
                elif age < 14:
                    error_messages.append("Debes tener al menos 14 años.")
                elif age > 100:
                    error_messages.append("La edad máxima permitida es de 100 años.")
                else:
                    user.birthday = birthday_date
            except ValueError:
                error_messages.append("Formato de fecha de nacimiento no válido.")
        else:
            user.birthday = None

        # Actualizar otros datos
        user.city = request.POST.get('city')
        user.description = request.POST.get('description')

        # Eliminar foto de perfil
        if 'eliminar_foto_perfil' in request.POST:
            user.profile_picture.delete()
            user.save()
            return HttpResponseRedirect(request.path)

        # Procesar nueva foto de perfil
        if request.FILES.get('profile_photo'):
            user.profile_picture = request.FILES.get('profile_photo')

        # Procesar Erasmus
        erasmus = request.POST.get('erasmus', False)
        user.erasmus = erasmus

        # Procesar la eliminación de seguidores
        if 'remove_follower' in request.POST:
            follower_id = request.POST.get('follower_id')
            if follower_id:
                try:
                    follower = CustomUser.objects.get(id=follower_id)
                    # Verificar que el usuario logueado tiene al seguidor en su lista de seguidores
                    if follower in user.followers.all():
                        user.followers.remove(follower)
                    else:
                        error_messages.append('El usuario no es un seguidor.')
                except CustomUser.DoesNotExist:
                    error_messages.append('El seguidor no existe.')

        # Verificar si el perfil está completo
        profile_is_now_complete = (
            user.birthday and user.city and user.description and user.profile_picture and user.aficiones.exists()
        )
        if profile_is_now_complete and not user.profile_completed:
            user.profile_completed = True
            request.session['profile_completed_recently'] = True

        user.save()

        if error_messages:
            return render(request, 'edit_profile.html', {
                'user': user,
                'available_hobbies': available_hobbies,
                'error_messages': error_messages,
                'complete_profile_alerts': complete_profile_alerts
            })

        return redirect('my_profile')

    return render(request, 'edit_profile.html', {
        'user': request.user,
        'available_hobbies': available_hobbies,
        'error_messages': error_messages,
        'complete_profile_alerts': complete_profile_alerts
    })

@login_required
def profile_settings(request):
    user = request.user

    has_pending_requests = user.follow_requests_received.filter(status='pending').exists()
    
    if request.method == 'POST':
        show_age = request.POST.get('show_age') == 'on'
        account_visibility = request.POST.get('account_visibility')

        # Comprobar si intenta cambiar a pública con solicitudes pendientes
        if has_pending_requests and account_visibility == 'public' and user.account_visibility == 'private':
            messages.warning(request, "Para hacer tu cuenta pública, primero debes aceptar o rechazar todas las solicitudes de seguimiento pendientes.")
            return redirect('profile_settings')

        # Guardar cambios
        user.show_age = show_age
        user.account_visibility = account_visibility
        user.save()
        return redirect('my_profile')
    
    context = {
        'user': user,
        'has_pending_requests': has_pending_requests,
    }
    
    return render(request, 'profile_settings.html', context)

@login_required
def delete_account(request):
    user = request.user
    user.delete()  # Borra el usuario
    return redirect('home')  # Redirige a una página adecuada después de borrar

def search_users(request):
    query = request.GET.get('q')
    users = CustomUser.objects.exclude(username=request.user.username)

    if query:
        users = CustomUser.objects.filter(username__icontains=query)
    
    return render(request, 'search_users.html', {'users': users})

@login_required
def followers_count(request, username):
    user_to_follow = get_object_or_404(CustomUser, username=username)
    
    if request.method == "POST":
        if request.POST['value'] == 'follow':
            # Verificar visibilidad de la cuenta
            if user_to_follow.account_visibility == 'private' and not Follow.objects.filter(follower=request.user, following=user_to_follow).exists():
                # Crear una solicitud de seguimiento si es cuenta privada
                FollowRequest.objects.get_or_create(sender=request.user, receiver=user_to_follow)
            else:
                # Si es cuenta publica, seguir directamente
                Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        elif request.POST['value'] == 'unfollow':
            # Eliminar seguimiento
            Follow.objects.filter(follower=request.user, following=user_to_follow).delete()
    
    return redirect('other_user_profile', username=user_to_follow.username)

@login_required
def other_user_profile(request, username):
    request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
    profile_user = get_object_or_404(CustomUser, username=username)
    is_own_profile = profile_user == request.user
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    user_followers = profile_user.followers.count()
    user_following = profile_user.following.count()

    pending_follow_request = FollowRequest.objects.filter(sender=request.user, receiver=profile_user, status='pending').first()

    follow_button_value = 'unfollow' if is_following else 'follow'

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'user_followers': user_followers,
        'user_following': user_following,
        'follow_button_value': follow_button_value,
        'current_user': request.user,
        'pending_follow_request': pending_follow_request
    }
    
    return render(request, 'profile_other_user.html', context)


@login_required
def followers_and_following(request, username):
    request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
    profile_user = get_object_or_404(CustomUser, username=username)
    
    # Capturar parámetros de búsqueda y ordenación
    search_query = request.GET.get('search', '')
    sort_order = request.GET.get('sort_order', 'newest')

    # Inicializar variables para el mensaje de alerta
    no_followers_results = False
    no_following_results = False
    
    # Filtrar seguidores y seguidos cuyos nombres empiezan por la letra indicada en la búsqueda
    if search_query:
        followers = profile_user.followers.filter(Q(follower__username__istartswith=search_query))
        following = profile_user.following.filter(Q(following__username__istartswith=search_query))

        # Verificar si hay resultados
        no_followers_results = followers.count() == 0
        no_following_results = following.count() == 0
    else:
        followers = profile_user.followers.all()
        following = profile_user.following.all()
    
    # Ordenar según la opción seleccionada
    if sort_order == 'newest':
        followers = followers.order_by('-id')  # Asegúrate de tener un campo adecuado para ordenar cronológicamente
        following = following.order_by('-id')
    elif sort_order == 'oldest':
        followers = followers.order_by('id')
        following = following.order_by('id')

    # Contar los seguidores y seguidos
    followers_count = profile_user.followers.count()
    following_count = request.user.following.count()

    # Verificar si el usuario autenticado es el mismo que el perfil que se está viendo
    is_own_profile = (request.user.id == profile_user.id)

    context = {
        'user': profile_user,
        'followers': followers,
        'following': following,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_own_profile': is_own_profile,
        'no_followers_results': no_followers_results,
        'no_following_results': no_following_results, 
    }
    
    return render(request, 'followers_and_following.html', context)


def remove_follower(request, follower_id):
    if request.method == "POST":
        follow_instance = get_object_or_404(Follow, follower_id=follower_id, following=request.user)
        follow_instance.delete()
        return redirect('followers_and_following', username=request.user.username)

def unfollow_user(request, following_id):
    if request.method == "POST":
        follow_instance = get_object_or_404(Follow, follower=request.user, following_id=following_id)
        follow_instance.delete()
        return redirect('followers_and_following', username=request.user.username)
    
@login_required
def accept_follow_request(request, request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, receiver=request.user)
    if follow_request.status == 'pending':
        # Crear relación de seguimiento y actualizar el estado de la solicitud
        Follow.objects.create(follower=follow_request.sender, following=follow_request.receiver)
        follow_request.delete()
    return redirect('follow_requests')

@login_required
def reject_follow_request(request, request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, receiver=request.user)
    if follow_request.status == 'pending':
        follow_request.delete()
    return redirect('follow_requests')

@login_required
def follow_requests(request):
    pending_requests = request.user.follow_requests_received.filter(status='pending')
    return render(request, 'follow_requests.html', {'pending_requests': pending_requests})

@login_required
def sidebar(request):
    user = request.user
    complete_profile_alerts = 0    

    if user.birthday is None:
        complete_profile_alerts+=1
    
    if user.city=="":
        complete_profile_alerts+=1

    if user.description=="":
        complete_profile_alerts+=1
    
    if user.profile_picture=="":
        complete_profile_alerts+=1

    if len(user.aficiones.all()) == 0:
        complete_profile_alerts+=1

    pending_requests_count = FollowRequest.objects.filter(receiver=user, status='pending').count()

    return render(request, 'sidebar.html', {
        'user': user,
        'pending_requests_count': pending_requests_count,
        'complete_profile_alerts': complete_profile_alerts,
    })