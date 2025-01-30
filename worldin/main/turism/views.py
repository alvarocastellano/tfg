from django.contrib.auth.decorators import login_required
from main.views import city_data 
from django.shortcuts import render
import requests
from main.models import FollowRequest
from main.community.models import ChatRequest, Chat, GroupChat
from django.db.models import Count, Q
from main.views import alertas_completar_perfil
from urllib.parse import quote

def city_conversor(city):
    if city == "La Valeta":
        return "Valletta"
    elif city == "Atenas":
        return "Athens"
    elif city == "Luxemburgo":
        return "Luxembourg"
    elif city == "Roterdam":
        return "Rotterdam"
    elif city == "Viena":
        return "Wien"
    elif city == "Varsovia":
        return "Warsaw"
    elif city == "Oporto":
        return "Porto"
    elif city == "Buenos Aires":
        return "Buenos%20Aires"
    elif city == "Washington D.C.":
        return "Washington"
    elif city == "Nueva Delhi":
        return "New%20Delhi"
    elif city == "Sofia":
        return quote("София")
    elif city == "Copenhague":
        return quote("København")
    elif city == "Brasilia":
        return quote("Brasília")
    elif city == "Praga":
        return "Praha"
    elif city == "Pekín":
        return quote("北京")
    else:
        return city

@login_required
def city_map(request, city_name):
    complete_profile_alerts = alertas_completar_perfil(request)
    pending_requests_count = FollowRequest.objects.filter(receiver=request.user, status='pending').count()

    pending_chat_requests_count = ChatRequest.objects.filter(receiver=request.user, status='pending').count()

    private_chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    )

    all_groups_chats = GroupChat.objects.filter(members__user=request.user).exclude(name=request.user.city).annotate(
        unread_count=Count('group_messages', filter=Q(group_messages__is_read=False) & ~Q(group_messages__sender=request.user))
    )

    total_unread_count = sum(chat.unread_count for chat in private_chats) + sum(chat.unread_count for chat in all_groups_chats)
    city_info = city_data.get(city_name)

    # Información adicional
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    if not city_info:
        return render(request, 'invalid_city.html', {
            "city_name": city_name,
            "complete_profile_alerts": complete_profile_alerts,
            "pending_requests_count": pending_requests_count,
            "pending_chat_requests_count": pending_chat_requests_count,
            "total_unread_count": total_unread_count,})

    lat, lon = city_info["lat"], city_info["lon"]

    conversor = city_conversor(city_name)

    # URL para Overpass API
    overpass_url = f'https://overpass-api.de/api/interpreter?data=[out:json];area[name="{conversor}"];node["tourism"]["tourism"!~"^(hotel|hostel|motel|picnic_site|camp_site|chalet|viewpoint|apartment|guest_house|attraction|gallery)$"](area);out;'

    response = requests.get(overpass_url)
    data = response.json() if response.status_code == 200 else {"elements": []}

    # Extraer los lugares turísticos
    places = []
    for elem in data["elements"]:
        if "lat" in elem and "lon" in elem:
            tags = elem.get("tags", {})
            places.append({
                "name": tags.get("name", "Lugar turístico"),
                "lat": elem["lat"],
                "lon": elem["lon"],
                "address": f'{tags.get("addr:street", "")} {tags.get("addr:housenumber", "")} {tags.get("addr:postcode", "")}'.strip(),
                "opening_hours": tags.get("opening_hours", "Horario no disponible"),
                "price": tags.get("fee", ""),
                "website": tags.get("website", ""),
                "phone": tags.get("phone", ""),
            })

    return render(request, "turism/city_map.html", {
        "city_name": city_name,
        "lat": lat,
        "lon": lon,
        "places": places,
        "country": country,
        "flag_image": flag_image,
        "complete_profile_alerts": complete_profile_alerts,
        "pending_requests_count": pending_requests_count,
        "pending_chat_requests_count": pending_chat_requests_count,
        "total_unread_count": total_unread_count,
    })