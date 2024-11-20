from decimal import Decimal, InvalidOperation
from django.shortcuts import  render
from worldin.forms import CustomUserCreationForm, CustomAuthenticationForm, ProductForm, RentalForm, ProductImageFormSet, RentalImageFormSet
from django.shortcuts import  render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import CustomUser, Hobby, Follow, FollowRequest, Product, Rental, ProductImage, RentalImage, RentalFeature
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib import messages
from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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
    
def alertas_completar_perfil(request):
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
    return complete_profile_alerts

#ACCESO RÁPIDO A VISTA DE MI PERFIL
@login_required
def profile(request):
    user = request.user
    complete_profile_alerts = 0
    announce_count = 0

    filter_option = request.GET.get('filter', 'todos')

    user_products = Product.objects.filter(owner=request.user)
    user_rentings = Rental.objects.filter(owner=request.user)

    # Contadores
    announce_count = len(user_products) + len(user_rentings)

    # Filtrado según el parámetro 'filter'
    if filter_option == 'articulos':
        user_rentings = []  # Solo mostrar productos
    elif filter_option == 'alquileres':
        user_products = []  # Solo mostrar alquileres

    

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
        'user_products': user_products,
        'user_rentings' : user_rentings,
        'age': age,
        'followers_count': followers_count,
        'following_count': following_count,
        'pending_requests_count': pending_requests_count,
        'complete_profile_alerts': complete_profile_alerts,
        'total_alerts' : total_alerts,
        'announce_count' : announce_count,
        'filter_option': filter_option,
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
                'complete_profile_alerts': complete_profile_alerts,
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
    error_messages = []

    has_pending_requests = user.follow_requests_received.filter(status='pending').exists()

    if request.method == 'POST':
        show_age = request.POST.get('show_age') == 'on'
        account_visibility = request.POST.get('account_visibility')

        # Comprobar si intenta cambiar a pública con solicitudes pendientes
        if has_pending_requests and account_visibility == 'public' and user.account_visibility == 'private':
            error_messages.append("Para hacer tu cuenta pública, primero debes aceptar o rechazar todas las solicitudes de seguimiento pendientes.")

        if error_messages:
            context = {
                'user': user,
                'has_pending_requests': has_pending_requests,
                'error_messages': error_messages,
            }
            return render(request, 'profile_settings.html', context)
        else:
            # Guardar cambios
            user.show_age = show_age
            user.account_visibility = account_visibility
            user.save()
            return redirect('my_profile')

    # Manejar solicitudes GET
    context = {
        'user': user,
        'has_pending_requests': has_pending_requests,
        'error_messages': error_messages,  # No habrá errores en un GET inicial
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
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    if query:
        users = CustomUser.objects.filter(username__icontains=query)
    
    return render(request, 'search_users.html', {
        'users': users, 
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,})

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

#ACCESO RÁPIDO A LA VISTA DE PERFIL DE OTRO USUARIO
@login_required
def other_user_profile(request, username):
    request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
    profile_user = get_object_or_404(CustomUser, username=username)
    is_own_profile = profile_user == request.user
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    user_followers = profile_user.followers.count()
    user_following = profile_user.following.count()
    announce_count = 0
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    filter_option = request.GET.get('filter', 'todos')

    user_products = Product.objects.filter(owner=profile_user)
    user_rentings = Rental.objects.filter(owner=profile_user)

    # Contadores
    announce_count = len(user_products) + len(user_rentings)

    # Filtrado según el parámetro 'filter'
    if filter_option == 'articulos':
        user_rentings = []  # Solo mostrar productos
    elif filter_option == 'alquileres':
        user_products = []  # Solo mostrar alquileres

    pending_follow_request = FollowRequest.objects.filter(sender=request.user, receiver=profile_user, status='pending').first()

    follow_button_value = 'unfollow' if is_following else 'follow'

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'user_products' : user_products,
        'user_rentings': user_rentings,
        'is_following': is_following,
        'user_followers': user_followers,
        'user_following': user_following,
        'follow_button_value': follow_button_value,
        'current_user': request.user,
        'pending_follow_request': pending_follow_request,
        'announce_count' : announce_count,
        'filter_option': filter_option,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
    }
    
    return render(request, 'profile_other_user.html', context)


@login_required
def followers_and_following(request, username):
    request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
    profile_user = get_object_or_404(CustomUser, username=username)
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    
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
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
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
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests = request.user.follow_requests_received.filter(status='pending')
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    return render(request, 'follow_requests.html', {
        'pending_requests': pending_requests,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        })

@login_required
def sidebar(request):
    user = request.user

    selected_city = user.selected_city if user.selected_city!="" else user.city

    complete_profile_alerts = 0    
    if user.birthday is None:
        complete_profile_alerts += 1
    if user.city == "":
        complete_profile_alerts += 1
    if user.description == "":
        complete_profile_alerts += 1
    if user.profile_picture == "":
        complete_profile_alerts += 1
    if len(user.aficiones.all()) == 0:
        complete_profile_alerts += 1

    pending_requests_count = FollowRequest.objects.filter(receiver=user, status='pending').count()

    return render(request, 'sidebar.html', {
        'user': user,
        'pending_requests_count': pending_requests_count,
        'complete_profile_alerts': complete_profile_alerts,
        'selected_city': selected_city,
    })

@login_required
def update_city(request):
    if request.method == 'POST':
        selected_city = request.POST.get('selected_city')

        # Verifica si la ciudad seleccionada está en la lista permitida
        valid_cities = [
            "Bruselas", "Sofia", "Praga", "Copenhague", "Berlin", "Munich",
            "Tallin", "Dublin", "Cork", "Atenas", "Madrid", "Sevilla",
            "Barcelona", "Paris", "Lens", "Marsella", "Zagreb", "Split",
            "Roma", "Salerno", "Florencia", "Bari", "Luxemburgo", "Budapest",
            "La Valeta", "Amsterdam", "Roterdam", "Viena", "Varsovia",
            "Lisboa", "Oporto"
        ]

        if selected_city in valid_cities:
            user = request.user
            user.selected_city = selected_city
            user.save()
            
            # Retorna una respuesta en formato JSON indicando éxito
            return JsonResponse({'success': True, 'new_city': selected_city})
        else:
            return JsonResponse({'success': False, 'message': 'Ciudad no válida'}, status=400)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

#===========================AQUI COMIENZAN LAS VISTAS DEL MERCADO==========================================

def moneda_oficial(request):
    money = ""
    if request.user.city == "Sofia":
        money = "лв"  # Bulgaria
    elif request.user.city == "Praga":
        money = "Kč"  # República Checa
    elif request.user.city == "Copenhague":
        money = "kr"  # Dinamarca
    elif request.user.city == "Budapest":
        money = "Ft"  # Hungría
    elif request.user.city == "Varsovia":
        money = "zł"  # Polonia
    else:
        money = "€"  # Países de la zona euro
    return money


def my_market_profile(request):
    announce_count = 0
    rating_count = 0
    sell_count = 0
    buy_count = 0
    stars_sum = 0
    total_alerts = 0
    range_of_stars = [i for i in range(5)]
    user = request.user

    complete_profile_alerts = 0    
    if user.birthday is None:
        complete_profile_alerts += 1
    if user.city == "":
        complete_profile_alerts += 1
    if user.description == "":
        complete_profile_alerts += 1
    if user.profile_picture == "":
        complete_profile_alerts += 1
    if len(user.aficiones.all()) == 0:
        complete_profile_alerts += 1

    pending_requests_count = FollowRequest.objects.filter(receiver=user, status='pending').count()

    total_alerts = pending_requests_count + complete_profile_alerts

    # Parámetro para filtrar productos
    filter_option = request.GET.get('filter', 'todos')  # Por defecto, 'todos'

    if rating_count != 0:
        average_rating = stars_sum / rating_count
    else:
        average_rating = 0.0

    adjusted_rating = average_rating + 0.5

    user_products = Product.objects.filter(owner=request.user)
    user_rentings = Rental.objects.filter(owner=request.user)

    announce_count = len(user_products) + len(user_rentings)

    # Filtrado según el parámetro 'filter'
    if filter_option == 'articulos':
        user_rentings = []  # Solo mostrar productos
    elif filter_option == 'alquileres':
        user_products = []  # Solo mostrar alquileres

    # Contadores
    

    context = {
        'user_products': user_products,
        'user_rentings': user_rentings,
        'announce_count': announce_count,
        'rating_count': rating_count,
        'sell_count': sell_count,
        'buy_count': buy_count,
        'average_rating': average_rating,
        'range_of_stars': range_of_stars,
        'adjusted_rating': adjusted_rating,
        'filter_option': filter_option,
        'complete_profile_alerts' : complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'total_alerts': total_alerts,
    }
    return render(request, 'my_market_profile.html', context)


def my_market_ratings(request):
    return render(request, 'my_market_ratings.html')


@login_required
def add_product(request):
    error_messages = []
    money = moneda_oficial(request)
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    if not request.user.city:
        messages.error(request, 'No puedes publicar un artículo hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('my_market_profile')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())

        # Validaciones del formulario
        if form.is_valid():
            
            title = form.cleaned_data.get('title')
            if title.isnumeric():
                error_messages.append("El título no puede ser únicamente numérico.")

            price = form.cleaned_data.get('price')
            if price is None:
                error_messages.append("El precio es obligatorio.")
            else:
                try:
                    price = Decimal(price)
                    if price <= 0 or price < Decimal('0.1'):
                        error_messages.append("El precio debe ser mayor que 0.1")
                    elif price.quantize(Decimal('.01')) != price:
                        error_messages.append("El precio debe tener como máximo 2 decimales.")
                except InvalidOperation:
                    error_messages.append("El precio debe ser un número válido.")
        else:
            error_messages.append("Todos los campos son obligatorios.")

        # Validación del formset para las imágenes
        if formset.is_valid():
            image_count = sum(1 for f in formset if f.cleaned_data.get('image'))
            if image_count < 1:
                error_messages.append("Debes cargar al menos 1 imagen.")
        else:
            error_messages.append("Las imágenes no son válidas o no se cargaron correctamente.")

        if error_messages:
            # Si hay errores, volver a mostrar los datos previos en los formularios
            return render(request, 'add_product.html', {
                'form': form,
                'formset': formset,
                'error_messages': error_messages,
                'money': money,
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count': pending_requests_count,
            })

        # Si no hay errores, guardar el producto
        if form.is_valid() and formset.is_valid() and not error_messages:
            product = form.save(commit=False)
            product.owner = request.user
            product.city_associated = request.user.city
            product.money_associated = money
            product.save()

            for f in formset:
                if f.cleaned_data.get('image'):
                    ProductImage.objects.create(product=product, image=f.cleaned_data['image'])

            return redirect('my_market_profile')

    else:
        form = ProductForm()
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())

    return render(request, 'add_product.html', {
        'form': form, 
        'formset': formset, 
        'money': money, 
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        })


def product_details(request, product_id):
    # Obtener el producto y su propietario
    product = get_object_or_404(Product, id=product_id)
    rating_count = 0
    stars_sum = 0
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    
    if rating_count !=0 :
        average_rating = stars_sum/rating_count
    else:
        average_rating = 0.0

    adjusted_rating = average_rating + 0.5
    
    context = {
        'product': product,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
    }
    return render(request, 'product_details.html', context)

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    product.delete()
    return redirect('my_market_profile')

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    error_messages = []
    images_count = 0
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    if not request.user.city:
        messages.error(request, 'No puedes editar un artículo hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('my_market_profile')

    for image in product.images.all():
            images_count += 1

    if request.method == 'POST':
        # Actualizar detalles del producto
        product_title = request.POST.get('title')
        product_description = request.POST.get('description')
        product_price = request.POST.get('price')
        product_city_associated = request.user.city


        # Validar nombre de producto
        if Product.objects.filter(title=product_title).exclude(id=product.id).exists():
            error_messages.append('El nombre del producto ya está en uso.')

        # Verificar que los campos obligatorios no estén vacíos
        if not product_title or not product_description or not product_price:
            error_messages.append('Por favor, completa todos los campos obligatorios.')

        # Verificar que el producto tenga al menos una imagen
        if product.images.count() == 0 and request.FILES.get('product_image') is None:
            error_messages.append('El producto debe tener al menos una imagen.')

        # Si hay errores, no actualizar el producto
        if error_messages:
            return render(request, 'edit_product.html', {
                'product': product,
                'error_messages': error_messages,
                'images_count' : images_count,
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count': pending_requests_count,
            })

        # Si no hay errores, actualizar los detalles del producto
        product.title = product_title
        product.description = product_description
        product.price = product_price
        product.city_associated = product_city_associated
        product.money_associated = moneda_oficial(request)

        # Procesar nueva imagen del producto
        if request.FILES.get('product_image'):
            ProductImage.objects.create(product=product, image=request.FILES.get('product_image'))

        if request.FILES.get('product_image2'):
            ProductImage.objects.create(product=product, image=request.FILES.get('product_image2'))

        if request.FILES.get('product_image3'):
            ProductImage.objects.create(product=product, image=request.FILES.get('product_image3'))

        # Eliminar imágenes seleccionadas por el usuario
        if 'eliminar_imagen' in request.POST:
            images_to_delete = request.POST.getlist('eliminar_imagen')
            if len(images_to_delete) >= product.images.count():  # Si se elimina todas las imágenes, no permitimos la acción
                error_messages.append('El producto debe tener al menos una imagen.')
            else:
                for image_id in images_to_delete:
                    image = get_object_or_404(ProductImage, id=image_id)
                    image.delete()

        # Si hay errores después de eliminar imágenes, no actualizamos el producto
        if error_messages:
            return render(request, 'edit_product.html', {
                'product': product,
                'error_messages': error_messages,
                'images_count' : images_count,
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count': pending_requests_count,
            })

        # Guardar cambios en el producto
        product.save()
        return redirect('product_details', product_id=product.id)

    return render(request, 'edit_product.html', {
        'product': product,
        'error_messages': error_messages,
        'images_count' : images_count,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
    })




@login_required
def delete_product_image(request, product_id, image_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    # Obtener la imagen y verificar que pertenece al producto del usuario
    image = get_object_or_404(ProductImage, id=image_id, product=product)

    if request.method == 'POST':
        # Eliminar la imagen del producto
        image.image.delete()  # Borra el archivo de imagen
        image.delete()  # Elimina el registro de la base de datos
        return redirect('edit_product', product_id=product.id)  # Redirige de nuevo a la página de edición

    return redirect('edit_product', product_id=product.id)


@login_required
def add_renting(request):
    available_features= RentalFeature.objects.all()
    error_messages = []
    money = moneda_oficial(request)
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    if not request.user.city:
        messages.error(request, 'No puedes añadir un anuncio hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('my_market_profile')


    if request.method == 'POST':
        
        form = RentalForm(request.POST)
        selected_features = request.POST.getlist('features')
        formset = RentalImageFormSet(request.POST, request.FILES, queryset=RentalImage.objects.none())

        # Validaciones
        if form.is_valid():
            title = form.cleaned_data.get('title')
            if title.isnumeric():
                error_messages.append("El título no puede ser únicamente numérico.")

            # Validación del precio
            price = form.cleaned_data.get('price')
            if price is None:
                error_messages.append("El precio es obligatorio.")
            else:
                try:
                    price = int(price)  # Convertimos a entero
                    if price <= 0 or price < 100:
                        error_messages.append("El precio debe ser un número entero mayor que 100.")
                except ValueError:
                    error_messages.append("El precio debe ser un número válido y entero.")

            # Validación de rooms
            square_meters = form.cleaned_data.get('square_meters')
            if square_meters is None or square_meters <= 0:
                error_messages.append("los metros cuadrados deben ser un número positivo mayor que 0.")

            # Validación de max_people
            max_people = form.cleaned_data.get('max_people')
            if max_people is None or max_people <= 0:
                error_messages.append("El número máximo de personas debe ser un número positivo mayor que 0.")
            else:
                rooms = form.cleaned_data.get('rooms')
                if max_people > rooms:
                    error_messages.append("El número máximo de personas no puede ser mayor que el número de habitaciones.")

            # Validación de rooms
            rooms = form.cleaned_data.get('rooms')
            if rooms is None or rooms <= 0:
                error_messages.append("El número de habitaciones debe ser un número positivo mayor que 0.")
            elif rooms < max_people:
                error_messages.append("El número de habitaciones no puede ser menor que el número máximo de personas.")


            

        else:
            error_messages.append("Todos los campos son obligatorios, excepto las características, aunque altamente recomendado.")

        # Validación del formset para las imágenes
        if formset.is_valid():
            image_count = sum(1 for f in formset if f.cleaned_data.get('image'))
            if image_count < 1:
                error_messages.append("Debes cargar al menos 1 imagen.")
        else:
            error_messages.append("Las imágenes no son válidas o no se cargaron correctamente.")

        if error_messages:
            # Enviar el formulario y el formset con los datos previos (sin reiniciar los campos)
            return render(request, 'add_renting.html', {
                'form': form,
                'formset': formset,
                'error_messages': error_messages,
                'available_features': available_features,
                'selected_features': selected_features,
                'money': money,
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count': pending_requests_count,
            })

        if form.is_valid() and formset.is_valid() and not error_messages:
            rental = form.save(commit=False)
            rental.owner = request.user
            rental.city_associated = request.user.city
            rental.money_associated = money
            rental.save()

            rental.features.set(RentalFeature.objects.filter(id__in=selected_features))

            for f in formset:
                if f.cleaned_data.get('image'):
                    RentalImage.objects.create(rental=rental, image=f.cleaned_data['image'])

            return redirect('my_market_profile')

    else:
        form = RentalForm()
        formset = RentalImageFormSet(queryset=RentalImage.objects.none())

    return render(request, 'add_renting.html', {
        'form': form, 
        'formset': formset, 
        'available_features': available_features, 
        'error_messages': error_messages,
        'money': money,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        })


def renting_details(request, renting_id):
    # Obtener el producto y su propietario
    rental = get_object_or_404(Rental, id=renting_id)
    rating_count = 0
    stars_sum = 0
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    
    if rating_count !=0 :
        average_rating = stars_sum/rating_count
    else:
        average_rating = 0.0

    adjusted_rating = average_rating + 0.5
    
    context = {
        'rental': rental,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
    }
    return render(request, 'renting_details.html', context)


@login_required
def delete_renting(request, renting_id):
    renting = get_object_or_404(Rental, id=renting_id, owner=request.user)
    renting.delete()
    return redirect('my_market_profile')

def market_profile_other_user(request, username):
    request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
    profile_user = get_object_or_404(CustomUser, username=username)
    sell_count = 0
    buy_count = 0
    rating_count = 0
    is_own_profile = profile_user == request.user
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    user_followers = profile_user.followers.count()
    user_following = profile_user.following.count()
    announce_count = 0
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    complete_profile_alerts = alertas_completar_perfil(request)

    filter_option = request.GET.get('filter', 'todos')

    user_products = Product.objects.filter(owner=profile_user)
    user_rentings = Rental.objects.filter(owner=profile_user)

    # Contadores
    announce_count = len(user_products) + len(user_rentings)

    # Filtrado según el parámetro 'filter'
    if filter_option == 'articulos':
        user_rentings = []  # Solo mostrar productos
    elif filter_option == 'alquileres':
        user_products = []  # Solo mostrar alquileres

    pending_follow_request = FollowRequest.objects.filter(sender=request.user, receiver=profile_user, status='pending').first()

    follow_button_value = 'unfollow' if is_following else 'follow'

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'user_products' : user_products,
        'user_rentings': user_rentings,
        'is_following': is_following,
        'user_followers': user_followers,
        'user_following': user_following,
        'follow_button_value': follow_button_value,
        'current_user': request.user,
        'pending_follow_request': pending_follow_request,
        'announce_count' : announce_count,
        'filter_option': filter_option,
        'sell_count' : sell_count,
        'buy_count': buy_count,
        'rating_count': rating_count,
        'pending_requests_count': pending_requests_count,
        'complete_profile_alerts': complete_profile_alerts,
    }
    
    return render(request, 'market_profile_other_user.html', context)

def edit_renting(request, renting_id):
    renting = get_object_or_404(Rental, id=renting_id)
    error_messages = []
    images_count = 0
    available_features= RentalFeature.objects.all()
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    if not request.user.city:
        messages.error(request, 'No puedes editar un anuncio hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('my_market_profile')

    for image in renting.images.all():
            images_count += 1

    if request.method == 'POST':
        # Actualizar detalles del producto
        renting_title = request.POST.get('title')
        renting_description = request.POST.get('description')
        renting_price = request.POST.get('price')
        renting_square_meters = request.POST.get('square_meters')
        renting_max_people = request.POST.get('max_people')
        renting_rooms = request.POST.get('rooms')
        renting_location = request.POST.get('location')
        renting_city_associated = request.user.city
        
        if renting_title.isnumeric():
            error_messages.append("El título no puede ser únicamente numérico.")

            # Validación del precio
        if renting_price is None:
            error_messages.append("El precio es obligatorio.")
        else:
            try:
                renting_price = int(renting_price)  # Convertimos a entero
                if renting_price <= 0 or renting_price < 100:
                    error_messages.append("El precio debe ser un número entero mayor que 100.")
            except ValueError:
                error_messages.append("El precio debe ser un número válido y entero.")

            # Validación de metros cuadrados
            renting_square_meters = int(renting_square_meters)
            if renting_square_meters is None or renting_square_meters <= 0:
                error_messages.append("los metros cuadrados deben ser un número positivo mayor que 0.")

            # Validación de max_people
            renting_max_people = int(renting_max_people)
            renting_rooms = int(renting_rooms)
            if renting_max_people is None or renting_max_people <= 0:
                error_messages.append("El número máximo de personas debe ser un número positivo mayor que 0.")
            else:
                if renting_max_people > renting_rooms:
                    error_messages.append("El número máximo de personas no puede ser mayor que el número de habitaciones.")

            # Validación de rooms
            if renting_rooms is None or renting_rooms <= 0:
                error_messages.append("El número de habitaciones debe ser un número positivo mayor que 0.")
            elif renting_rooms < renting_max_people:
                error_messages.append("El número de habitaciones no puede ser menor que el número máximo de personas.")

            selected_features = request.POST.getlist('features')

        # Validar nombre de producto
        if Product.objects.filter(title=renting_title).exclude(id=renting.id).exists():
            error_messages.append('El nombre del anuncio ya está en uso.')

        # Verificar que los campos obligatorios no estén vacíos
        if not renting_title or not renting_description or not renting_location or not renting_price or not renting_square_meters or not renting_rooms or not renting_max_people:
            error_messages.append('Por favor, completa todos los campos obligatorios.')

        # Verificar que el anuncio tenga al menos una imagen
        if renting.images.count() == 0 and request.FILES.get('renting_image') is None:
            error_messages.append('El anuncio debe tener al menos una imagen.')

        # Si hay errores, no actualizar el producto
        if error_messages:
            return render(request, 'edit_renting.html', {
                'renting': renting,
                'error_messages': error_messages,
                'images_count' : images_count,
                'available_features': available_features,
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count': pending_requests_count,
            })

        # Si no hay errores, actualizar los detalles del producto
        renting.title = renting_title
        renting.description = renting_description
        renting.price = renting_price
        renting.location = renting_location
        renting.square_meters = renting_square_meters
        renting.rooms = renting_rooms
        renting.max_people = renting_max_people
        renting.city_associated = renting_city_associated
        renting.money_associated = moneda_oficial(request)
        selected_features = request.POST.getlist('features')

        # Procesar nueva imagen del producto
        if request.FILES.get('renting_image'):
            RentalImage.objects.create(rental=renting, image=request.FILES.get('renting_image'))
        
        if request.FILES.get('renting_image2'):
            RentalImage.objects.create(rental=renting, image=request.FILES.get('renting_image2'))

        if request.FILES.get('renting_image3'):
            RentalImage.objects.create(rental=renting, image=request.FILES.get('renting_image3'))

        

        # Eliminar imágenes seleccionadas por el usuario
        if 'eliminar_imagen' in request.POST:
            images_to_delete = request.POST.getlist('eliminar_imagen')
            if len(images_to_delete) >= renting.images.count():  # Si se elimina todas las imágenes, no permitimos la acción
                error_messages.append('El anuncio debe tener al menos una imagen.')
            else:
                for image_id in images_to_delete:
                    image = get_object_or_404(RentalImage, id=image_id)
                    image.delete()

        # Si hay errores después de eliminar imágenes, no actualizamos el producto
        if error_messages:
            return render(request, 'edit_renting.html', {
                'renting': renting,
                'error_messages': error_messages,
                'images_count' : images_count,
                'available_features': available_features,
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count': pending_requests_count,
            })

        # Guardar cambios en el producto
        renting.features.set(RentalFeature.objects.filter(id__in=selected_features))
        renting.save()
        return redirect('renting_details', renting_id=renting.id)

    return render(request, 'edit_renting.html', {
        'renting': renting,
        'error_messages': error_messages,
        'images_count' : images_count,
        'available_features': available_features,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
    })