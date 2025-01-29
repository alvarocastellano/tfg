from django.core.management.base import BaseCommand
from main.community.models import GroupChat

class Command(BaseCommand):
    help = "Crea grupos de chat para las ciudades predefinidas"

    def handle(self, *args, **kwargs):
        city_data = {
        "Bruselas": {"country": "Bélgica", "flag": "belgica.png"},
        "Sofia": {"country": "Bulgaria", "flag": "bulgaria.png"},
        "Praga": {"country": "República Checa", "flag": "chequia.png"},
        "Copenhague": {"country": "Dinamarca", "flag": "dinamarca.png"},
        "Berlin": {"country": "Alemania", "flag": "alemania.png"},
        "Munich": {"country": "Alemania", "flag": "alemania.png"},
        "Tallinn": {"country": "Estonia", "flag": "estonia.png"},
        "Dublin": {"country": "Irlanda", "flag": "irlanda.png"},
        "Cork": {"country": "Irlanda", "flag": "irlanda.png"},
        "Atenas": {"country": "Grecia", "flag": "grecia.png"},
        "Madrid": {"country": "España", "flag": "spain.png"},
        "Sevilla": {"country": "España", "flag": "spain.png"},
        "Barcelona": {"country": "España", "flag": "spain.png"},
        "Paris": {"country": "Francia", "flag": "francia.png"},
        "Lens": {"country": "Francia", "flag": "francia.png"},
        "Marsella": {"country": "Francia", "flag": "francia.png"},
        "Zagreb": {"country": "Croacia", "flag": "croacia.png"},
        "Split": {"country": "Croacia", "flag": "croacia.png"},
        "Roma": {"country": "Italia", "flag": "italia.png"},
        "Salerno": {"country": "Italia", "flag": "italia.png"},
        "Florencia": {"country": "Italia", "flag": "italia.png"},
        "Bari": {"country": "Italia", "flag": "italia.png"},
        "Luxemburgo": {"country": "Luxemburgo", "flag": "luxemburgo.png"},
        "Budapest": {"country": "Hungría", "flag": "hungria.png"},
        "La Valeta": {"country": "Malta", "flag": "malta.png"},
        "Amsterdam": {"country": "Países Bajos", "flag": "holanda.png"},
        "Roterdam": {"country": "Países Bajos", "flag": "holanda.png"},
        "Viena": {"country": "Austria", "flag": "austria.png"},
        "Varsovia": {"country": "Polonia", "flag": "polonia.png"},
        "Lisboa": {"country": "Portugal", "flag": "portugal.png"},
        "Oporto": {"country": "Portugal", "flag": "portugal.png"},
        "Buenos Aires": {"country": "Argentina", "flag": "argentina.png"},
        "Canberra": {"country": "Australia", "flag": "australia.png"},
        "Brasilia": {"country": "Brasil", "flag": "brasil.png"},
        "Ottawa": {"country": "Canadá", "flag": "canada.png"},
        "Santiago": {"country": "Chile", "flag": "chile.png"},
        "Pekín": {"country": "China", "flag": "china.png"},
        "Washington D.C.": {"country": "Estados Unidos", "flag": "estados_unidos.png"},
        "Nueva Delhi": {"country": "India", "flag": "india.png"},
        "Tokio": {"country": "Japón", "flag": "japon.png"},
        "Montevideo": {"country": "Uruguay", "flag": "uruguay.png"}
    }


        created_count = 0
        for city, data in city_data.items():
            group_chat, created = GroupChat.objects.get_or_create(
                name=city,
                defaults={
                    'description': f"Chat grupal para la ciudad de {city}",
                    'image': data['flag']
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f"{created_count} grupos de chat creados.")
