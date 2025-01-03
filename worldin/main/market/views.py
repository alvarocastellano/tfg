from decimal import Decimal, InvalidOperation
from django.shortcuts import  render
from .forms import  ProductForm, RentalForm, ProductImageFormSet, RentalImageFormSet
from django.shortcuts import  render, redirect, get_object_or_404, reverse
from main.models import CustomUser, Follow, FollowRequest
from .models import Product, Rental, ProductImage, RentalImage, RentalFeature, Rating
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, BooleanField, Case, Value, When, Count
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import stripe
from django.conf import settings
import logging
import requests
from django.views.decorators.http import require_POST
from main.views import alertas_completar_perfil, city_data, valid_cities
from main.community.models import Chat, Message, ChatRequest, GroupChat
from django.utils.html import format_html
from django.contrib.auth import get_user_model


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
    elif request.user.city == "Buenos Aires":
        money = "$"  # Peso argentino
    elif request.user.city == "Canberra":
        money = "$"  # Dólar australiano
    elif request.user.city == "Brasilia":
        money = "R$"  # Real brasileño
    elif request.user.city == "Ottawa":
        money = "$"  # Dólar canadiense
    elif request.user.city == "Santiago":
        money = "$"  # Peso chileno
    elif request.user.city == "Pekín":
        money = "¥"  # Yuan renminbi chino
    elif request.user.city == "Washington D.C.":
        money = "$"  # Dólar estadounidense
    elif request.user.city == "Nueva Delhi":
        money = "₹"  # Rupia india
    elif request.user.city == "Tokio":
        money = "¥"  # Yen japonés
    elif request.user.city == "Montevideo":
        money = "$"  # Peso uruguayo
    else:
        money = "€"  # Países de la zona euro
    return money


def currency(request):
    currency = ""
    if request.user.city == "Sofia":
        currency = "BGN"  # Lev búlgaro
    elif request.user.city == "Praga":
        currency = "CZK"  # Corona checa
    elif request.user.city == "Copenhague":
        currency = "DKK"  # Corona danesa
    elif request.user.city == "Budapest":
        currency = "HUF"  # Florín húngaro
    elif request.user.city == "Varsovia":
        currency = "PLN"  # Zloty polaco
    elif request.user.city == "Buenos Aires":
        currency = "ARS"  # Peso argentino
    elif request.user.city == "Canberra":
        currency = "AUD"  # Dólar australiano
    elif request.user.city == "Brasilia":
        currency = "BRL"  # Real brasileño
    elif request.user.city == "Ottawa":
        currency = "CAD"  # Dólar canadiense
    elif request.user.city == "Santiago":
        currency = "CLP"  # Peso chileno
    elif request.user.city == "Pekín":
        currency = "CNY"  # Yuan renminbi chino
    elif request.user.city == "Washington D.C.":
        currency = "USD"  # Dólar estadounidense
    elif request.user.city == "Nueva Delhi":
        currency = "INR"  # Rupia india
    elif request.user.city == "Tokio":
        currency = "JPY"  # Yen japonés
    elif request.user.city == "Montevideo":
        currency = "UYU"  # Peso uruguayo
    else:
        currency = "EUR"  # Euro para la zona euro
    return currency




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
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=user, status='pending').count()

    total_alerts = pending_requests_count + complete_profile_alerts

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    # Parámetro para filtrar productos
    filter_option = request.GET.get('filter', 'articulos')  # Por defecto, 'todos'

    user_products = Product.objects.filter(owner=request.user).annotate(
        highlighted_order=Case(
            When(highlighted=True, then=Value(0)),  # Los destacados primero
            When(highlighted=False, then=Value(1)),  # Los no destacados después
            output_field=BooleanField(),
        )).order_by('highlighted_order', '-highlighted_at', '-created_at')


    # Ordenar los renting
    user_rentings = Rental.objects.filter(owner=request.user).annotate(
        highlighted_order=Case(
            When(highlighted=True, then=Value(0)),  # Los destacados primero
            When(highlighted=False, then=Value(1)),  # Los no destacados después
            output_field=BooleanField(),
        )).order_by('highlighted_order', '-highlighted_at', '-created_at')
    


    items_bought = list(Product.objects.filter(buyer=request.user)) + list(Rental.objects.filter(buyer=request.user))

    announce_count = len([product for product in user_products if product.status != 'sold']) + len([renting for renting in user_rentings if renting.status != 'sold'])

    total_announces = len(user_products) + len(user_rentings)

    sold_count = len([product for product in user_products if product.status == 'sold']) + len([renting for renting in user_rentings if renting.status == 'sold'])

    bought_count = len(items_bought)

    rated_announces = list(Product.objects.filter(owner=request.user, product_rating__isnull=False)) + list(Rental.objects.filter(owner=request.user, renting_rating__isnull=False))

    ratings_count = len(rated_announces)

    ratings_sum = 0
    for rating in rated_announces:
        if isinstance(rating, Product) and rating.product_rating:
            ratings_sum += rating.product_rating.rating
        elif isinstance(rating, Rental) and rating.renting_rating:
            ratings_sum += rating.renting_rating.rating


    if ratings_count != 0:
        average_rating = ratings_sum / ratings_count
    else:
        average_rating = 0.0

    # Filtrado según el parámetro 'filter'
    if filter_option == 'articulos':
        user_rentings = []  # Solo mostrar productos
    elif filter_option == 'alquileres':
        user_products = []  # Solo mostrar alquileres

    context = {
        
        'user_products': user_products,
        'user_rentings': user_rentings,
        'announce_count': announce_count,
        'rating_count': rating_count,
        'sell_count': sell_count,
        'buy_count': buy_count,
        'average_rating': average_rating,
        'range_of_stars': range_of_stars,
        'complete_profile_alerts' : complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'total_alerts': total_alerts,
        'sold_count': sold_count,
        'bought_count': bought_count,
        'filter_option': filter_option,
        'items_bought': items_bought,
        'rated_announces': rated_announces,
        'ratings_count': ratings_count,
        'average_rating': average_rating,
        'total_announces': total_announces,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    }
    return render(request, 'my_market_profile.html', context)


def my_market_ratings(request):
    announce_count = 0
    rating_count = 0
    sell_count = 0
    buy_count = 0
    stars_sum = 0
    total_alerts = 0
    range_of_stars = [i for i in range(5)]
    user = request.user
    success_messages = []

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
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    total_alerts = pending_requests_count + complete_profile_alerts

    user_products = Product.objects.filter(owner=request.user)
    user_rentings = Rental.objects.filter(owner=request.user)

    items_bought = list(Product.objects.filter(buyer=request.user)) + list(Rental.objects.filter(buyer=request.user))

    announce_count = len([product for product in user_products if product.status != 'sold']) + len([renting for renting in user_rentings if renting.status != 'sold'])

    sold_count = len([product for product in user_products if product.status == 'sold']) + len([renting for renting in user_rentings if renting.status == 'sold'])

    bought_count = len(items_bought)

    rated_announces = list(Product.objects.filter(owner=request.user, product_rating__isnull=False)) + list(Rental.objects.filter(owner=request.user, renting_rating__isnull=False))

    ratings_count = len(rated_announces)

    ratings_sum = 0
    for rating in rated_announces:
        if isinstance(rating, Product) and rating.product_rating:
            ratings_sum += rating.product_rating.rating
        elif isinstance(rating, Rental) and rating.renting_rating:
            ratings_sum += rating.renting_rating.rating


    if ratings_count != 0:
        average_rating = ratings_sum / ratings_count
    else:
        average_rating = 0.0

    context = {
        'user_products': user_products,
        'user_rentings': user_rentings,
        'announce_count': announce_count,
        'rating_count': rating_count,
        'sell_count': sell_count,
        'buy_count': buy_count,
        'average_rating': average_rating,
        'range_of_stars': range_of_stars,
        'complete_profile_alerts' : complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'total_alerts': total_alerts,
        'sold_count': sold_count,
        'bought_count': bought_count,
        'items_bought': items_bought,
        'success_messages': success_messages,
        'rated_announces': rated_announces,
        'ratings_count': ratings_count,
        'average_rating': average_rating,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    }

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        item_type = request.POST.get('item_type')
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')

        if item_type == 'product':
            product = Product.objects.get(id=item_id)
            Rating.objects.create(user=request.user, product=product, rating=rating, comment=comment)
        elif item_type == 'renting':
            renting = Rental.objects.get(id=item_id)
            Rating.objects.create(user=request.user, renting=renting, rating=rating, comment=comment)

        success_messages.append('Valoración guardada con éxito.')
        return render(request, 'my_market_ratings.html', context)
    
    return render(request, 'my_market_ratings.html', context)

@login_required
def other_user_ratings(request, username):
    
    announce_count = 0
    rating_count = 0
    sell_count = 0
    buy_count = 0
    total_alerts = 0
    range_of_stars = [i for i in range(5)]
    user = request.user
    success_messages = []

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
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    total_alerts = pending_requests_count + complete_profile_alerts

    try:
        # Intentar obtener el usuario
        profile_user = CustomUser.objects.get(username=username)
        if profile_user == request.user:
            return redirect('market:my_market_profile')
    except CustomUser.DoesNotExist:
        # Si no existe, redirigir a la página de error
        return render(request, 'user_not_found.html', {
            'pending_requests_count': pending_requests_count,
            'complete_profile_alerts': complete_profile_alerts,
            'total_alerts': total_alerts,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })

    user_products = Product.objects.filter(owner=profile_user)
    user_rentings = Rental.objects.filter(owner=profile_user)

    items_bought = list(Product.objects.filter(buyer=profile_user)) + list(Rental.objects.filter(buyer=profile_user))

    announce_count = len([product for product in user_products if product.status != 'sold']) + len([renting for renting in user_rentings if renting.status != 'sold'])

    sold_count = len([product for product in user_products if product.status == 'sold']) + len([renting for renting in user_rentings if renting.status == 'sold'])

    bought_count = len(items_bought)

    rated_announces = list(Product.objects.filter(owner=profile_user, product_rating__isnull=False)) + list(Rental.objects.filter(owner=profile_user, renting_rating__isnull=False))

    ratings_count = len(rated_announces)

    ratings_sum = 0
    for rating in rated_announces:
        if isinstance(rating, Product) and rating.product_rating:
            ratings_sum += rating.product_rating.rating
        elif isinstance(rating, Rental) and rating.renting_rating:
            ratings_sum += rating.renting_rating.rating


    if ratings_count != 0:
        average_rating = ratings_sum / ratings_count
    else:
        average_rating = 0.0

    context = {
        'user_products': user_products,
        'user_rentings': user_rentings,
        'announce_count': announce_count,
        'rating_count': rating_count,
        'sell_count': sell_count,
        'buy_count': buy_count,
        'average_rating': average_rating,
        'range_of_stars': range_of_stars,
        'complete_profile_alerts' : complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'total_alerts': total_alerts,
        'sold_count': sold_count,
        'bought_count': bought_count,
        'items_bought': items_bought,
        'success_messages': success_messages,
        'rated_announces': rated_announces,
        'ratings_count': ratings_count,
        'average_rating': average_rating,
        'profile_user': profile_user,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    }

    
    return render(request, 'other_user_ratings.html', context)


@login_required
def add_product(request):
    error_messages = []
    money = moneda_oficial(request)
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    if not request.user.city:
        messages.error(request, 'No puedes publicar un artículo hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('market:my_market_profile')

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
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })

        # Si no hay errores, guardar el producto
        if form.is_valid() and formset.is_valid() and not error_messages:
            product = form.save(commit=False)
            product.owner = request.user
            product.city_associated = request.user.city
            product.money_associated = money
            product.status = 'on_sale'
            product.save()

            for f in formset:
                if f.cleaned_data.get('image'):
                    ProductImage.objects.create(product=product, image=f.cleaned_data['image'])

            return redirect('market:highlight_product', product_id=product.id)

    else:
        form = ProductForm()
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())

    return render(request, 'add_product.html', {
        'form': form, 
        'formset': formset, 
        'money': money, 
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
        })

def highlight_product(request, product_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    
    if product.owner==request.user:
        if product.highlighted:
            return render(request, 'already_highlighted.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
        else:
            return render(request, 'highlight_product.html', {'product': product, 'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count, 'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,})
    else:
        return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            } )

def highlight_renting(request, renting_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        renting = Rental.objects.get(id=renting_id)
    except Rental.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    if renting.owner==request.user:
        if renting.highlighted:
            return render(request, 'already_highlighted.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
        else:
            return render(request, 'highlight_renting.html', {'renting': renting, 'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count, 'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,})
    else:
        return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            } )

def product_details(request, product_id):
    rating_count = 0
    stars_sum = 0
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    
    if rating_count !=0 :
        average_rating = stars_sum/rating_count
    else:
        average_rating = 0.0

    adjusted_rating = average_rating + 0.5
    
    context = {
        'product': product,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    }
    return render(request, 'product_details.html', context)

@login_required
def delete_product(request, product_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        product = Product.objects.get(id=product_id)
        if product.owner != request.user:
            # Si el producto no pertenece al usuario logueado, redirigir a la página de error
            return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    except Product.DoesNotExist:
        # Si el producto no existe, redirigir a una página de error o manejar de forma similar
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    product.delete()
    return redirect('market:my_market_profile')

@login_required
def edit_product(request, product_id):
    error_messages = []
    images_count = 0
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })

    if product.owner != request.user:
        return render(request, "market/edit_your_ads_only.html", {
            'complete_profile_alerts': complete_profile_alerts, 
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
            } )

    if not request.user.city:
        messages.error(request, 'No puedes editar un artículo hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('market:my_market_profile')

    for image in product.images.all():
            images_count += 1

    if request.method == 'POST':
        # Actualizar detalles del producto
        product_title = request.POST.get('title')
        product_description = request.POST.get('description')
        product_price = request.POST.get('price')
        product_city_associated = request.user.city


        # Validar nombre de producto
        if Product.objects.filter(title=product_title, owner=request.user).exclude(id=product.id).exists():
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
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
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
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })

        # Guardar cambios en el producto
        product.save()
        return redirect('market:product_details', product_id=product.id)

    return render(request, 'edit_product.html', {
        'product': product,
        'error_messages': error_messages,
        'images_count' : images_count,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
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
        return redirect('market:edit_product', product_id=product.id)  # Redirige de nuevo a la página de edición

    return redirect('market:edit_product', product_id=product.id)


@login_required
def add_renting(request):
    available_features= RentalFeature.objects.all()
    error_messages = []
    money = moneda_oficial(request)
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    if not request.user.city:
        messages.error(request, 'No puedes añadir un anuncio hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('market:my_market_profile')


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

            # Validación de rooms
            rooms = form.cleaned_data.get('rooms')
            if rooms is None or rooms <= 0:
                error_messages.append("El número de habitaciones debe ser un número positivo mayor que 0.")

            

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
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
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

            return redirect('market:highlight_renting',  renting_id=rental.id )

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
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
        })


def renting_details(request, renting_id):
    rating_count = 0
    stars_sum = 0
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    try:
        rental = Rental.objects.get(id=renting_id)
    except Rental.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    
    if rating_count !=0 :
        average_rating = stars_sum/rating_count
    else:
        average_rating = 0.0
    
    context = {
        'rental': rental,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    }
    return render(request, 'renting_details.html', context)


@login_required
def delete_renting(request, renting_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        renting = Rental.objects.get(id=renting_id)
        if renting.owner != request.user:
            # Si el producto no pertenece al usuario logueado, redirigir a la página de error
            return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    except Rental.DoesNotExist:
        # Si el producto no existe, redirigir a una página de error o manejar de forma similar
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    renting.delete()
    return redirect('market:my_market_profile')

def market_profile_other_user(request, username):
    request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    complete_profile_alerts = alertas_completar_perfil(request)
    
    try:
        # Intentar obtener el usuario
        profile_user = CustomUser.objects.get(username=username)
        if profile_user == request.user:
            return redirect('market:my_market_profile')
    except CustomUser.DoesNotExist:
        # Si no existe, redirigir a la página de error
        return render(request, 'user_not_found.html', {
            'pending_requests_count': pending_requests_count,
            'complete_profile_alerts': complete_profile_alerts,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    
    sell_count = 0
    buy_count = 0
    rating_count = 0
    is_own_profile = profile_user == request.user
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    user_followers = profile_user.followers.count()
    user_following = profile_user.following.count()
    announce_count = 0

    user_products = Product.objects.filter(owner=profile_user).annotate(
        highlighted_order=Case(
            When(highlighted=True, then=Value(0)),  # Los destacados primero
            When(highlighted=False, then=Value(1)),  # Los no destacados después
            output_field=BooleanField(),
        )).order_by('highlighted_order', '-highlighted_at', '-created_at')


    # Ordenar los renting
    user_rentings = Rental.objects.filter(owner=profile_user).annotate(
        highlighted_order=Case(
            When(highlighted=True, then=Value(0)),  # Los destacados primero
            When(highlighted=False, then=Value(1)),  # Los no destacados después
            output_field=BooleanField(),
        )).order_by('highlighted_order', '-highlighted_at', '-created_at')

    items_bought = list(Product.objects.filter(buyer=profile_user)) + list(Rental.objects.filter(buyer=profile_user))

    announce_count = len([product for product in user_products if product.status != 'sold']) + len([renting for renting in user_rentings if renting.status != 'sold'])

    sold_count = len([product for product in user_products if product.status == 'sold']) + len([renting for renting in user_rentings if renting.status == 'sold'])

    bought_count = len(items_bought)

    rated_announces = list(Product.objects.filter(owner=profile_user, product_rating__isnull=False)) + list(Rental.objects.filter(owner=profile_user, renting_rating__isnull=False))

    ratings_count = len(rated_announces)

    ratings_sum = 0
    for rating in rated_announces:
        if isinstance(rating, Product) and rating.product_rating:
            ratings_sum += rating.product_rating.rating
        elif isinstance(rating, Rental) and rating.renting_rating:
            ratings_sum += rating.renting_rating.rating


    if ratings_count != 0:
        average_rating = ratings_sum / ratings_count
    else:
        average_rating = 0.0

    filter_option = request.GET.get('filter', 'articulos')



    # Filtrado según el parámetro 'filter'
    if filter_option == 'articulos':
        user_rentings = []  # Solo mostrar productos
    elif filter_option == 'alquileres':
        user_products = []  # Solo mostrar alquileres

    pending_follow_request = FollowRequest.objects.filter(sender=request.user, receiver=profile_user, status='pending').first()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()

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
        'average_rating': average_rating,
        'sold_count': sold_count,
        'bought_count': bought_count,
        'items_bought': items_bought,
        'rated_announces': rated_announces,
        'ratings_count': ratings_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    }
    
    return render(request, 'market_profile_other_user.html', context)

def edit_renting(request, renting_id):
    error_messages = []
    images_count = 0
    available_features= RentalFeature.objects.all()
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    try:
        renting = Rental.objects.get(id=renting_id)
    except Rental.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })

    if renting.owner != request.user:
        return render(request, "market/edit_your_ads_only.html", {
            'complete_profile_alerts': complete_profile_alerts, 
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
            } ) 

    if not request.user.city:
        messages.error(request, 'No puedes editar un anuncio hasta que tengas una ciudad asignada en tu perfil.')
        return redirect('market:my_market_profile')

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
            

            # Validación de rooms
            if renting_rooms is None or renting_rooms <= 0:
                error_messages.append("El número de habitaciones debe ser un número positivo mayor que 0.")
            

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
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
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
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })

        # Guardar cambios en el producto
        renting.features.set(RentalFeature.objects.filter(id__in=selected_features))
        renting.save()
        return redirect('market:renting_details', renting_id=renting.id)

    return render(request, 'edit_renting.html', {
        'renting': renting,
        'error_messages': error_messages,
        'images_count' : images_count,
        'available_features': available_features,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    })

def main_market_products(request, selected_city):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    order = request.GET.get('order', None)
    search_query = request.GET.get('q', '')

    if selected_city not in valid_cities:
        return render(request, "market/invalid_city.html",
        {
            'complete_profile_alerts': complete_profile_alerts, 
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
            } )

    if request.user.selected_city == "":
        return render(request, "market/select_city_before_searching.html", {
            'complete_profile_alerts': complete_profile_alerts, 
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
            } )    

    city_info = city_data.get(selected_city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    products = Product.objects.filter(city_associated=selected_city).annotate(
        highlighted_order=Case(
            When(highlighted=True, then=Value(0)),  # Los destacados primero
            When(highlighted=False, then=Value(1)),  # Los no destacados después
            output_field=BooleanField(),
        )).order_by('highlighted_order', '-highlighted_at', '-created_at')

    # Buscador
    filtered_products = products  # Para mantener todos los productos en caso de búsqueda sin resultados
    if search_query:
        filtered_products = products.filter(title__icontains=search_query)
        if not filtered_products.exists():
            # Si no hay resultados, mostrar todos los productos pero indicar que no se encontraron resultados específicos
            no_results_message = f"No se encuentran resultados para la búsqueda: '{search_query}'"
            filtered_products = products  # Revertimos a todos los productos
        else:
            no_results_message = None
    else:
        no_results_message = None

    #filtrados
    if order == 'newest':
        filtered_products = filtered_products.order_by('-created_at')
    elif order == 'older':
        filtered_products = filtered_products.order_by('created_at')
    elif order == 'cheapest':
        filtered_products = filtered_products.order_by('price')
    elif order == 'expensive':
        filtered_products = filtered_products.order_by('-price')

    products_count = filtered_products.count()

    only_user_products = (
        filtered_products.exists() and 
        not filtered_products.exclude(owner=request.user).exists()
    )

    # Paginación
    paginator = Paginator(filtered_products, 20)  # 20 productos por página
    page = request.GET.get('page', 1)

    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)


    context = {
        'selected_city': selected_city,
        'country': country,
        'flag_image': flag_image,
        'order': order,
        'search_query': search_query,
        'products': paginated_products,
        'products_count': products_count,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'only_user_products': only_user_products,
        'no_results_message': no_results_message,
        'total_unread_count': total_unread_count,
    }
    return render(request, "main_market_products.html", context)

def main_market_rentings(request, selected_city):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    order = request.GET.get('order', None)
    search_query = request.GET.get('q', '')
    selected_features = request.GET.getlist('features')

    if selected_city not in valid_cities:
        return render(request, "market/invalid_city.html",
        {
            'complete_profile_alerts': complete_profile_alerts, 
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            } )

    if request.user.selected_city == "":
        return render(request, "market/select_city_before_searching.html", {
            'complete_profile_alerts': complete_profile_alerts, 
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
            } )

    city_info = city_data.get(selected_city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    # Filtrar los anuncios asociados a la ciudad seleccionada
    rentings = Rental.objects.filter(city_associated=selected_city).annotate(
        highlighted_order=Case(
            When(highlighted=True, then=Value(0)),  # Los destacados primero
            When(highlighted=False, then=Value(1)),  # Los no destacados después
            output_field=BooleanField(),
        )).order_by('highlighted_order', '-highlighted_at', '-created_at')

    # Filtrar por caracteristicas
    if selected_features:
        for feature_id in selected_features:
            rentings = rentings.filter(features__id=feature_id)

        rentings = rentings.distinct()

        if not rentings.exists():
            no_caracts_message = "No hay ningún anuncio publicado que cuente con todas las características seleccionadas."
            filtered_rentings = Rental.objects.none()
        else:
            no_caracts_message = None
            filtered_rentings = rentings
    else:
        no_caracts_message = None
        filtered_rentings = rentings

    #Buscador
    if search_query:
        filtered_rentings = rentings.filter(location__icontains=search_query)
        if not filtered_rentings.exists():
            # Si no hay resultados, mostrar todos los anuncios pero indicar que no se encontraron resultados específicos
            no_results_message = f"No se encuentran resultados para la búsqueda: '{search_query}'"
            filtered_rentings = rentings  # Revertimos a todos los anuncios
        else:
            no_results_message = None
    else:
        no_results_message = None

    #filtrados
    if order == 'newest':
        filtered_rentings = filtered_rentings.order_by('-created_at')
    elif order == 'older':
        filtered_rentings = filtered_rentings.order_by('created_at')
    elif order == 'cheapest':
        filtered_rentings = filtered_rentings.order_by('price')
    elif order == 'expensive':
        filtered_rentings = filtered_rentings.order_by('-price')
    elif order == 'min_to_max_square_meters':
        filtered_rentings = filtered_rentings.order_by('square_meters')
    elif order == 'max_to_min_square_meters':
        filtered_rentings = filtered_rentings.order_by('-square_meters')
    elif order == 'min_to_max_rooms':
        filtered_rentings = filtered_rentings.order_by('rooms')
    elif order == 'max_to_min_rooms':
        filtered_rentings = filtered_rentings.order_by('-rooms')
    elif order == 'min_to_max_people':
        filtered_rentings = filtered_rentings.order_by('max_people')
    elif order == 'max_to_min_people':
        filtered_rentings = filtered_rentings.order_by('-max_people')

    rentings_count = filtered_rentings.count()

    # Verificar si solo hay anuncios del usuario en la ciudad
    only_user_rentings = (
        filtered_rentings.exists() and 
        not filtered_rentings.exclude(owner=request.user).exists()
    )

    all_features = RentalFeature.objects.all()

        # Paginación
    paginator = Paginator(filtered_rentings, 20)  # 20 anuncios por página
    page = request.GET.get('page', 1)

    try:
        paginated_rentings = paginator.page(page)
    except PageNotAnInteger:
        paginated_rentings = paginator.page(1)
    except EmptyPage:
        paginated_rentings = paginator.page(paginator.num_pages)


    context = {
        'selected_city': selected_city,
        'country': country,
        'flag_image': flag_image,
        'rentings': paginated_rentings,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'rentings_count': rentings_count,
        'only_user_rentings': only_user_rentings,
        'no_results_message': no_results_message,
        'all_features': all_features,
        'selected_features': selected_features,
        'no_caracts_message': no_caracts_message,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
    }
    return render(request, "main_market_rentings.html", context)

def get_exchange_rate(to_currency):
    """
    Obtiene la tasa de cambio de EUR a la moneda especificada.
    Usa una API externa para obtener las tasas.
    """
    try:
        # Reemplaza con tu clave de API y endpoint (por ejemplo, Fixer.io o ExchangeRate-API)
        API_URL = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(API_URL)
        data = response.json()

        # Extrae la tasa de cambio
        return data['rates'].get(to_currency, None)
    except Exception as e:
        print(f"Error al obtener la tasa de cambio: {e}")
        return None  # Retorna None si ocurre un error


stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session_renting(request, renting_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    try:
        renting = Rental.objects.get(id=renting_id)
    except Rental.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    
    if renting.highlighted:
        return render(request, 'already_highlighted.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    else:

        user_currency = currency(request)

        # Obtén la tasa de cambio
        exchange_rate = get_exchange_rate(user_currency)

        if exchange_rate is None:
            # Define un valor predeterminado si la API falla (asumiendo tasa 1:1)
            exchange_rate = 1

        # Convierte el precio base en euros (5.99 EUR) a la moneda destino
        base_price_eur = 599  # Precio en centavos de euro
        converted_price = int(base_price_eur * exchange_rate)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': user_currency,
                        'product_data': {
                            'name': "Destacar el anuncio: " + renting.title,
                        },
                        'unit_amount': converted_price,
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                'renting_id': renting_id,
            },
            mode='payment',
            success_url=request.build_absolute_uri('/marketplace/payment-success-renting/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/marketplace/payment-cancel/') + '?session_id={CHECKOUT_SESSION_ID}',
        )
        return redirect(session.url, code=303)

def create_checkout_session_product(request, product_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        # Si el producto no existe, redirige a la plantilla invalid_id
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    
    if product.highlighted:
        return render(request, 'already_highlighted.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    else:
        user_currency = currency(request)

        # Obtén la tasa de cambio
        exchange_rate = get_exchange_rate(user_currency)

        if exchange_rate is None:
            # Define un valor predeterminado si la API falla (asumiendo tasa 1:1)
            exchange_rate = 1

        # Convierte el precio base en euros (5.99 EUR) a la moneda destino
        base_price_eur = 399  # Precio en centavos de euro
        converted_price = int(base_price_eur * exchange_rate)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': user_currency,
                        'product_data': {
                            'name': "Destacar el producto: " + product.title,
                        },
                        'unit_amount': converted_price,
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                'product_id': product_id,
            },
            mode='payment',
            success_url=request.build_absolute_uri('/marketplace/payment-success-product/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/marketplace/payment-cancel/') + '?session_id={CHECKOUT_SESSION_ID}',
        )
        return redirect(session.url, code=303)

def payment_success_renting(request):
    session_id = request.GET.get('session_id')  # Recoge el session_id de la URL.
    if not session_id:
        return HttpResponse("Falta el ID de la sesión", status=400)

    try:
        # Recupera la sesión desde Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            # Procesa la lógica del alquiler destacado
            metadata = session.get('metadata', {})
            renting_id = metadata.get('renting_id')
            if renting_id:
                try:
                    renting = Rental.objects.get(id=renting_id)
                    renting.set_highlighted(days=31)
                except Rental.DoesNotExist:
                    return HttpResponse("Alquiler no encontrado", status=404)
    except stripe.error.StripeError as e:
        return HttpResponse(f"Error al verificar el pago: {e}", status=400)
    
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    return render(request, 'payment_success.html', {
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,})


def payment_success_product(request):
    session_id = request.GET.get('session_id')  # Recoge el session_id de la URL.
    if not session_id:
        return HttpResponse("Falta el ID de la sesión", status=400)

    try:
        # Recupera la sesión desde Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            # Procesa la lógica del producto destacado
            metadata = session.get('metadata', {})
            product_id = metadata.get('product_id')
            if product_id:
                try:
                    product = Product.objects.get(id=product_id)
                    product.set_highlighted(days=31)
                except Product.DoesNotExist:
                    return HttpResponse("Producto no encontrado", status=404)
    except stripe.error.StripeError as e:
        return HttpResponse(f"Error al verificar el pago: {e}", status=400)
    
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    return render(request, 'payment_success.html', {
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
        })

def payment_cancel(request):
    session_id = request.GET.get('session_id')  # Obtén el session_id, si lo necesitas.
    if not session_id:
        return HttpResponse("Falta el ID de la sesión", status=400)
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        logger = logging.getLogger(__name__)
        logger.info(f"Pago cancelado. ID de sesión: {session_id}")
    except stripe.error.StripeError as e:
        logger.error(f"Error al recuperar la sesión cancelada: {e}")
        pass

    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    return render(request, 'payment_cancel.html', {
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
        })

@csrf_exempt
@require_POST
def update_product_highlight_status(request):
    try:
        data = json.loads(request.body)
        object_id = data.get('id')

        product = Product.objects.get(id=object_id)
        product.unset_highlighted()
        return JsonResponse({'status': 'success', 'message': 'Estado de destacado actualizado para el producto'})
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Producto no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Error en los datos de entrada'}, status=400)
    
@csrf_exempt
@require_POST
def update_renting_highlight_status(request):
    try:
        data = json.loads(request.body)
        object_id = data.get('id')

        renting = Rental.objects.get(id=object_id)
        renting.unset_highlighted()
        return JsonResponse({'status': 'success', 'message': 'Estado de destacado actualizado para el alquiler'})
    except Rental.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Alquiler no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Error en los datos de entrada'}, status=400)
    

@login_required
def send_message(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    owner = product.owner
    user = request.user
    error_messages = []
    success_messages = []

    follow_mutually = Follow.objects.filter(
                follower=user, following=owner
            ).exists() and Follow.objects.filter(
                follower=owner, following=user
            ).exists()

    if request.method == 'POST':
        initial_message = request.POST.get('initial_message')

        if Chat.objects.filter(Q(user1=user, user2=owner) | Q(user1=owner, user2=user)).exists():
            # Si ya existe un chat, pero no tiene producto asociado, agrega el mensaje
            chat = Chat.objects.filter(Q(user1=user, user2=owner) | Q(user1=owner, user2=user)).first()
            if chat.messages.filter(product=product).exists():
                error_messages.append(
                    format_html(
                        'Ya has enviado un mensaje a este usuario interesándote por el producto. Consulta la conversación en tus <a href="{}">chats activos</a>.',
                        reverse('community:all_chats')
                    )
                )
                return render(request, 'market/product_details.html', {
                    'product': product,
                    'error_messages': error_messages,
                })
            else:
                Message.objects.create(chat=chat, sender=user, content=initial_message, product=product)
                chat.products.add(product)
                success_messages.append(format_html(
                        'Mensaje enviado correctamente. Puedes acceder a la conversación en tus <a href="{}">chats activos</a>.',
                        reverse('community:all_chats')
                    ))
                return render(request, 'market/product_details.html', {
                    'product': product,
                    'success_messages': success_messages,
                })
        elif ChatRequest.objects.filter(Q(sender=user, receiver=owner, product=product)).exists():
            # Si ya hay una solicitud de chat enviada
            error_messages.append(format_html(
                        'Ya has enviado una solicitud a este usuario preguntando por este artículo. Consulta su estado accediendo a la pestaña de "Solicitudes enviadas" en <a href="{}">tus solicitudes de chat pendientes</a>.',
                        reverse('community:chat_requests')
                    ))
            return render(request, 'market/product_details.html', {
                'product': product,
                'error_messages': error_messages,
            })
        elif ChatRequest.objects.filter(Q(sender=owner, receiver=user, status='pending', group_chat__isnull=True)).exists() or ChatRequest.objects.filter(Q(sender=user, receiver=owner, status='pending', group_chat__isnull=True)).exists():
            # Si ya hay una solicitud de chat pendiente
            error_messages.append(format_html(
                        'Ya hay una solicitud de chat pendiente con este usuario. Consulta su estado accediendo a la pestaña de "Solicitudes recibidas" en <a href="{}">tus solicitudes de chat pendientes</a>.',
                        reverse('community:chat_requests')
                    ))
            return render(request, 'market/product_details.html', {
                'product': product,
                'error_messages': error_messages,
            })
        elif follow_mutually and not Chat.objects.filter(Q(user1=user, user2=owner) | Q(user1=owner, user2=user)).exists():
            #Si ambos se siguen mutuamente pero no había chat previo
            chat = Chat.objects.create(user1=user, user2=owner, initial_message="He iniciado este chat para preguntarte por producto")
            chat.products.add(product)
            Message.objects.create(chat=chat, sender=user, content=initial_message, product=product)
            success_messages.append(format_html(
                        'Mensaje enviado correctamente. Puedes acceder a la conversación a través de tus <a href="{}">chats activos</a>.',
                        reverse('community:all_chats')
                    ))
            return render(request, 'market/product_details.html', {
                'product': product,
                'success_messages': success_messages,
            })

        else:
            # Crear una nueva solicitud de chat si no existe un chat previo
            ChatRequest.objects.create(sender=user, receiver=owner, initial_message=initial_message, product=product)
            success_messages.append(format_html(
                        'Se ha enviado una solicitud de chat al vendedor. Consulta su estado accediendo a la pestaña de "Solicitudes enviadas" en <a href="{}">tus solicitudes de chat pendientes</a>.',
                        reverse('community:chat_requests')
                    ))
            return render(request, 'market/product_details.html', {
                'product': product,
                'success_messages': success_messages,
            })
        
    return redirect('market:product_details', product_id=product.id)

@login_required
def send_message_renting(request, renting_id):
    rental = get_object_or_404(Rental, id=renting_id)
    owner = rental.owner
    user = request.user
    error_messages = []
    success_messages = []

    follow_mutually = Follow.objects.filter(
                follower=user, following=owner
            ).exists() and Follow.objects.filter(
                follower=owner, following=user
            ).exists()

    if request.method == 'POST':
        initial_message = request.POST.get('initial_message')

        if Chat.objects.filter(Q(user1=user, user2=owner) | Q(user1=owner, user2=user)).exists():
            # Si ya existe un chat con el mismo anuncio mencionado
            chat = Chat.objects.filter(Q(user1=user, user2=owner) | Q(user1=owner, user2=user)).first()
            if chat.messages.filter(renting=rental).exists():
                error_messages.append(
                    format_html(
                        'Ya has enviado un mensaje a este usuario interesándote por el anuncio. Consulta la conversación en tus <a href="{}">chats activos</a>.',
                        reverse('community:all_chats')
                    )
                )
                return render(request, 'renting_details.html', {
                    'rental': rental,
                    'error_messages': error_messages,
                })
            else:
                Message.objects.create(chat=chat, sender=user, content=initial_message, renting=rental)
                chat.rentings.add(rental)
                success_messages.append(format_html(
                        'Mensaje enviado correctamente. Puedes acceder a la conversación en tus <a href="{}">chats activos</a>.',
                        reverse('community:all_chats')
                    ))
                return render(request, 'renting_details.html', {
                    'rental': rental,
                    'success_messages': success_messages,
                })
        elif ChatRequest.objects.filter(Q(sender=user, receiver=owner, renting=rental)).exists():
            # Si ya hay una solicitud de chat enviada
            error_messages.append(format_html(
                        'Ya has enviado una solicitud a este usuario preguntando por este anuncio. Consulta su estado accediendo a la pestaña de "Solicitudes enviadas" en <a href="{}">tus solicitudes de chat pendientes</a>.',
                        reverse('community:chat_requests')
                    ))
            return render(request, 'renting_details.html', {
                'rental': rental,
                'error_messages': error_messages,
            })
        elif ChatRequest.objects.filter(Q(sender=owner, receiver=user, status='pending', group_chat__isnull=True)).exists() or ChatRequest.objects.filter(Q(sender=user, receiver=owner, status='pending', group_chat__isnull=True)).exists():
            # Si ya hay una solicitud de chat pendiente
            error_messages.append(format_html(
                        'Ya hay una solicitud de chat pendiente con este usuario. Consulta su estado accediendo a la pestaña de "Solicitudes recibidas" en <a href="{}">tus solicitudes de chat pendientes</a>.',
                        reverse('community:chat_requests')
                    ))
            return render(request, 'renting_details.html', {
                'rental': rental,
                'error_messages': error_messages,
            })
        elif follow_mutually and not Chat.objects.filter(Q(user1=user, user2=owner) | Q(user1=owner, user2=user)).exists():
            #Si ambos se siguen mutuamente pero no había chat previo
            chat = Chat.objects.create(user1=user, user2=owner, initial_message="He iniciado este chat para preguntarte por un anuncio")
            chat.rentings.add(rental)
            Message.objects.create(chat=chat, sender=user, content=initial_message, renting=rental)
            success_messages.append(format_html(
                        'Mensaje enviado correctamente. Puedes acceder a la conversación a través de tus <a href="{}">chats activos</a>.',
                        reverse('community:all_chats')
                    ))
            return render(request, 'renting_details.html', {
                'rental': rental,
                'success_messages': success_messages,
            })

        else:
            # Crear una nueva solicitud de chat si no existe un chat previo
            ChatRequest.objects.create(sender=user, receiver=owner, initial_message=initial_message, renting=rental)
            success_messages.append(format_html(
                        'Se ha enviado una solicitud de chat al propietario. Consulta su estado accediendo a la pestaña de "Solicitudes enviadas" en <a href="{}">tus solicitudes de chat pendientes</a>.',
                        reverse('community:chat_requests')
                    ))
            return render(request, 'renting_details.html', {
                'rental': rental,
                'success_messages': success_messages,
            })
        
    return redirect('market:renting_details', renting_id=rental.id)

def book_product(request, product_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        product = Product.objects.get(id=product_id)
        if product.owner != request.user:
            # Si el producto no pertenece al usuario logueado, redirigir a la página de error
            return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    except Product.DoesNotExist:
        # Si el producto no existe, redirigir a una página de error o manejar de forma similar
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    product.status = 'booked'
    product.save()

    chat = Chat.objects.filter(products=product).first()
    if chat:
        Message.objects.create(
            chat=chat,
            sender=request.user,
            content=f'El producto "{product.title}" ha sido reservado.',
            product=product,
            is_system_message=True
        )
    
    return redirect('my_profile')

def unbook_product(request, product_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        product = Product.objects.get(id=product_id)
        if product.owner != request.user:
            # Si el producto no pertenece al usuario logueado, redirigir a la página de error
            return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    except Product.DoesNotExist:
        # Si el producto no existe, redirigir a una página de error o manejar de forma similar
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    product.status = 'on_sale'
    product.save()

    chat = Chat.objects.filter(products=product).first()
    if chat:
        Message.objects.create(
            chat=chat,
            sender=request.user,
            content=f'Se ha eliminado la reserva del producto "{product.title}". Vuelve a estar disponible.',
            product=product,
            is_system_message=True
        )
    return redirect('my_profile')

def sell_product(request, product_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
        
    if request.method == 'POST':
        buyer_id = request.POST.get('buyer_id')
        product = get_object_or_404(Product, id=product_id, owner=request.user)
        
        User = get_user_model()
        buyer = get_object_or_404(User, id=buyer_id)

        product.status = 'sold'
        product.highlighted = False
        product.buyer = buyer
        product.save()

        chat = Chat.objects.filter(products=product).first()
        if chat:
            Message.objects.create(
                chat=chat,
                sender=request.user,
                content=f'El producto "{product.title}" ha sido vendido.',
                product=product,
                is_system_message=True
            )
        return redirect('my_profile')
            
    else:
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })

def book_renting(request, renting_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        renting = Rental.objects.get(id=renting_id)
        if renting.owner != request.user:
            # Si el producto no pertenece al usuario logueado, redirigir a la página de error
            return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    except Rental.DoesNotExist:
        # Si el producto no existe, redirigir a una página de error o manejar de forma similar
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    renting.status = 'booked'
    renting.save()

    chat = Chat.objects.filter(rentings=renting).first()
    if chat:
        Message.objects.create(
            chat=chat,
            sender=request.user,
            content=f'El anuncio de alquiler "{renting.title}" ha sido reservado.',
            renting=renting,
            is_system_message=True
        )
    return redirect('my_profile')

def unbook_renting(request, renting_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
    try:
        renting = Rental.objects.get(id=renting_id)
        if renting.owner != request.user:
            # Si el producto no pertenece al usuario logueado, redirigir a la página de error
            return render(request, 'edit_your_ads_only.html', {
                'complete_profile_alerts': complete_profile_alerts,
                'pending_requests_count':pending_requests_count,
                'pending_chat_requests_count': pending_chat_requests_count,
                'total_unread_count': total_unread_count,
            })
    except Rental.DoesNotExist:
        # Si el producto no existe, redirigir a una página de error o manejar de forma similar
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })
    renting.status = 'on_sale'
    renting.save()

    chat = Chat.objects.filter(rentings=renting).first()
    if chat:
        Message.objects.create(
            chat=chat,
            sender=request.user,
            content=f'Se ha eliminado la reserva del anuncio de alquiler "{renting.title}". Vuelve a estar disponible.',
            renting=renting,
            is_system_message=True
        )
    return redirect('my_profile')

def sell_renting(request, renting_id):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()
    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()
    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats) + pending_chat_requests_count
        
    if request.method == 'POST':
        buyer_id = request.POST.get('renting_buyer_id')
        rental = get_object_or_404(Rental, id=renting_id, owner=request.user)
        
        User = get_user_model()
        buyer = get_object_or_404(User, id=buyer_id)

        rental.status = 'sold'
        rental.highlighted = False
        rental.buyer = buyer
        rental.save()

        chat = Chat.objects.filter(rentings=rental).first()
        if chat:
            Message.objects.create(
                chat=chat,
                sender=request.user,
                content=f'El alquiler "{rental.title}" ha encontrado inquilino(s). Ya no está disponible.',
                renting=rental,
                is_system_message=True
            )
        return redirect('my_profile')
            
    else:
        return render(request, 'invalid_id.html', {
            'complete_profile_alerts': complete_profile_alerts,
            'pending_requests_count': pending_requests_count,
            'pending_chat_requests_count': pending_chat_requests_count,
            'total_unread_count': total_unread_count,
        })