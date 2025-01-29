from django.contrib.auth.decorators import login_required
from main.views import city_data 
from django.shortcuts import render
import requests


@login_required
def city_map(request, city_name):
    city_info = city_data.get(city_name)

    # Información adicional
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    if not city_info:
        return render(request, 'invalid_city.html', {"city_name": city_name})

    lat, lon = city_info["lat"], city_info["lon"]

    # URL para Overpass API
    overpass_url = f'https://overpass-api.de/api/interpreter?data=[out:json];area[name="{city_name}"];node["tourism"]["tourism"!~"^(hotel|hostel|motel|picnic_site|camp_site|chalet|artwork|viewpoint|apartment|guest_house|attraction|gallery)$"](area);out;'

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
        "flag_image": flag_image
    })