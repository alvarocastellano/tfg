from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Event
from .forms import EventForm
from main.community.models import ChatRequest, Chat, GroupChat, ChatMember
from main.models import FollowRequest
from main.views import alertas_completar_perfil, city_data, valid_cities
import calendar
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware


@login_required
def event_calendar(request, selected_city):
    # Obtener mes y año de la URL o usar los actuales
    current_year = int(request.GET.get('year', datetime.now().year))
    current_month = int(request.GET.get('month', datetime.now().month))
    today = make_aware(datetime.now())

    # Día seleccionado desde GET (si existe)
    selected_day = request.GET.get('day', None)
    selected_date = (
        make_aware(datetime(current_year, current_month, int(selected_day)))
        if selected_day else None
    )

    # Navegación entre meses
    first_day_of_month = make_aware(datetime(current_year, current_month, 1))
    previous_month = (first_day_of_month - timedelta(days=1)).month
    previous_year = (first_day_of_month - timedelta(days=1)).year
    next_month = (first_day_of_month + timedelta(days=31)).month
    next_year = (first_day_of_month + timedelta(days=31)).year

    # Crear calendario
    cal = calendar.HTMLCalendar()
    month_days = cal.monthdayscalendar(current_year, current_month)

    # Obtener eventos para el mes actual
    events = Event.objects.filter(city=selected_city, start__year=current_year, start__month=current_month)

    # Filtrar eventos para el día seleccionado
    events_for_day = []
    if selected_date:
        for event in events:
            # Calcula todos los días que abarca el evento
            event_start_date = event.start.date()
            event_end_date = event.end.date()
            
            # Si el evento comienza y termina en el mismo día, solo se muestra en ese día
            if event_start_date == event_end_date:
                if event_start_date == selected_date.date():
                    events_for_day.append(event)
            
            # Si el evento abarca varios días, lo agregamos a todos los días del rango
            else:
                current_day = event_start_date
                while current_day <= event_end_date:
                    if current_day == selected_date.date():
                        events_for_day.append(event)
                        break
                    current_day += timedelta(days=1)


    # Información adicional
    city_info = city_data.get(selected_city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

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

    # Meses en español
    meses_espanol = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    mes_actual_espanol = meses_espanol[current_month - 1]

    return render(request, 'calendar.html', {
        'events': events,
        'events_for_day': events_for_day,
        'selected_city': selected_city,
        'country': country,
        'flag_image': flag_image,
        'month_days': month_days,
        'current_month': current_month,
        'current_year': current_year,
        'previous_month': previous_month,
        'previous_year': previous_year,
        'next_month': next_month,
        'next_year': next_year,
        'mes_actual_espanol': mes_actual_espanol,
        'complete_profile_alerts': complete_profile_alerts,
        'pending_requests_count': pending_requests_count,
        'pending_chat_requests_count': pending_chat_requests_count,
        'total_unread_count': total_unread_count,
        'today': today,
        'selected_date': selected_date,
    })


@login_required
def create_event(request, selected_city):

    error_messages = []
    city_info = city_data.get(selected_city, {})
    country = city_info.get('country', 'Desconocido')
    flag_image = city_info.get('flag', '')

    # Validar si el usuario es administrador de la ciudad
    if not request.user.is_city_admin or request.user.city != selected_city:
        return redirect('events:event_calendar', selected_city=selected_city)

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            if event.start >= event.end:
                error_messages.append("La fecha de inicio del evento debe ser anterior a su fecha de finalización.")
                return render(request, 'events/event_form.html', {'form':form, 'error_messages':error_messages, 'selected_city':selected_city, 'country':country, 'flag_image':flag_image})
            else:
                event.creator = request.user
                event.city = selected_city  # Asociar el evento a la ciudad seleccionada
                assigned_chat = GroupChat.objects.create(name=event.title, is_event_group=True, description=event.description)
                ChatMember.objects.create(group_chat=assigned_chat, user=request.user, user_type='admin')
                event.associated_chat = assigned_chat
                event.save()
                return redirect('events:event_calendar', selected_city=selected_city)
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {
        'form': form,
        'selected_city': selected_city,
        'country': country,
        'flag_image': flag_image,
    })


@login_required
def edit_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.creator != request.user:
        return redirect('events:event_calendar')  # Solo el creador puede editar

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('events:event_calendar')
    else:
        form = EventForm(instance=event)
    return render(request, 'events/event_form.html', {'form': form})
