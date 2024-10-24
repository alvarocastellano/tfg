from django.shortcuts import  render
from worldin.forms import CustomUserCreationForm, CustomAuthenticationForm
from django.shortcuts import  render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import CustomUser, Hobby, Follow
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib import messages
from datetime import datetime
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.contrib.messages import get_messages


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
    if request.user.is_authenticated:
        user_city = request.user.city.split(',')[0] if request.user.city else None
    context = {
        'user_city': user_city,
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

    # Calcular la edad
    if user.birthday:
        today = datetime.now()
        age = today.year - user.birthday.year - ((today.month, today.day) < (user.birthday.month, user.birthday.day))
    else:
        age = None

    # Contar seguidores y seguidos
    followers_count = user.followers.count()  # Suponiendo que tienes una relación de muchos a muchos
    following_count = user.following.count()  # Suponiendo que tienes una relación de muchos a muchos

    return render(request, 'my_profile.html', {
        'user': user,
        'age': age,
        'followers_count': followers_count,
        'following_count': following_count,
    })

@login_required
def edit_profile(request):
    available_hobbies = Hobby.objects.all()
    error_messages = []

    if request.method == 'POST':
        # Obtener el usuario actualmente autenticado
        user = request.user

        selected_hobbies = request.POST.getlist('hobbies')  # Obtener aficiones seleccionadas

        if len(selected_hobbies) > 7:
            error_messages.append('No puedes seleccionar más de 7 aficiones.')
            return render(request, 'edit_profile.html', {'user': user, 'available_hobbies': available_hobbies, 'error_messages': error_messages})

        user.aficiones.set(Hobby.objects.filter(id__in=selected_hobbies))  # Actualiza las aficiones del usuario

        # Procesar los datos del formulario
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('name')
        user.last_name = request.POST.get('surname')

        # Validar que los campos requeridos no estén vacíos
        if not user.username or not user.email or not user.first_name or not user.last_name:
            error_messages.append('Por favor, completa todos los campos requeridos: Nombre de usuario, correo electrónico, nombre y apellidos.')
            return render(request, 'edit_profile.html', {'user': user, 'available_hobbies' : available_hobbies, 'error_messages': error_messages})
        
        # Verificar si se proporcionó la fecha de nacimiento
        birthday = request.POST.get('birthday')
        if birthday:
            user.birthday = birthday
        else:
            user.birthday = None
        
        user.city = request.POST.get('city')
        user.description = request.POST.get('description')

        # Procesar la eliminación de la foto de perfil, si se solicita
        if 'eliminar_foto_perfil' in request.POST:
            # Eliminar la foto de perfil actual
            user.profile_picture.delete()
            user.save()
            return HttpResponseRedirect(request.path)

        # Procesar la imagen de perfil, si se proporciona
        if request.FILES.get('profile_photo'):
            user.profile_picture = request.FILES.get('profile_photo')

        erasmus = request.POST.get('erasmus', False)

        user.erasmus = erasmus

        # Guardar los cambios en el usuario
        user.save()

        if error_messages:
            return render(request, 'edit_profile.html', {'user': user, 'available_hobbies': available_hobbies, 'error_messages': error_messages})

        # Redirigir al usuario a una página de éxito o a otra página relevante
        return redirect('my_profile')  # Cambia 'profile' por el nombre de la URL de la página de perfil

    # Si el método de solicitud es GET, renderiza el formulario vacío
    return render(request, 'edit_profile.html', {'user': request.user, 'available_hobbies':available_hobbies, 'error_messages': error_messages})

@login_required
def profile_settings(request):
    user = request.user
    
    if request.method == 'POST':
        # Actualiza los campos del usuario
        user.show_age = request.POST.get('show_age') == 'on'  # Convierte a booleano
        user.account_visibility = request.POST.get('account_visibility')
        user.save()
        return redirect('my_profile')  # Redirige al perfil después de guardar los cambios
    
    context = {
        'user': user
    }
    
    return render(request, 'profile_settings.html', context)

@login_required
def delete_account(request):
    user = request.user
    user.delete()  # Borra el usuario
    return redirect('home')  # Redirige a una página adecuada después de borrar

@login_required
def follow_user(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)

    follow_instance, created = Follow.objects.get_or_create(follower=request.user, following=profile_user)

    # Actualizar los contadores de seguidores y seguidos
    followers_count = request.user.followers.count()  # Los seguidores del perfil
    following_count = profile_user.following.count()  # Los seguidos del usuario actual

    return JsonResponse({
        'followers_count': followers_count,  # Actualizar seguidores del perfil
        'following_count': following_count,  # Actualizar seguidos del usuario actual
        'created': created,
    })

@login_required
def unfollow_user(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)

    Follow.objects.filter(follower=request.user, following=profile_user).delete()

    # Actualizar los contadores de seguidores y seguidos
    followers_count = request.user.followers.count()  # Los seguidores del perfil
    following_count = profile_user.following.count()  # Los seguidos del usuario actual

    return JsonResponse({
        'followers_count': followers_count,  # Actualizar seguidores del perfil
        'following_count': following_count,  # Actualizar seguidos del usuario actual
        'created': False,
    })


def search_users(request):
    query = request.GET.get('q')
    users = CustomUser.objects.filter(username__icontains=query) if query else CustomUser.objects.none()  # Cambia a CustomUser
    return render(request, 'search_users.html', {'users': users})

@login_required
def other_user_profile(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)

    # Comprobar si el usuario actual ya sigue al perfil
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    # Contar seguidores y seguidos
    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    return render(request, 'profile_other_user.html', {
        'profile_user': profile_user,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following, 
    })


@login_required
def followers_and_following(request, user_id):
    profile_user = get_object_or_404(CustomUser, id=user_id)
    
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
