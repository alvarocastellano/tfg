from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Event
from .forms import EventForm
from main.community.models import ChatRequest, Chat, GroupChat
from main.models import FollowRequest
from main.views import alertas_completar_perfil, city_data, valid_cities
import calendar
from datetime import datetime, timedelta

@login_required
def event_calendar(request, selected_city):
    # Obtener mes y año de la URL o usar los actuales
    current_year = int(request.GET.get('year', datetime.now().year))
    current_month = int(request.GET.get('month', datetime.now().month))
    today = datetime.now()

    # Navegación entre meses
    first_day_of_month = datetime(current_year, current_month, 1)
    previous_month = (first_day_of_month - timedelta(days=1)).month
    previous_year = (first_day_of_month - timedelta(days=1)).year
    next_month = (first_day_of_month + timedelta(days=31)).month
    next_year = (first_day_of_month + timedelta(days=31)).year

    # Crear calendario
    cal = calendar.HTMLCalendar()
    month_days = cal.monthdayscalendar(current_year, current_month)

    # Obtener eventos para el mes actual
    events = Event.objects.filter(city=selected_city, start__year=current_year, start__month=current_month)

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
    })

@login_required
def create_event(request):
    if not request.user.is_city_admin:
        return redirect('events:event_calendar')  # Sólo administradores pueden crear eventos

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            event.save()
            return redirect('events:event_calendar')
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form})

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
