from django.contrib import admin
from django.urls import path, include
from main import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('policy/', views.policy, name='policy'),
    path('usage/', views.usage, name='usage'),
    path('admin/', admin.site.urls),
    path('login/', views.login_user, name='login'),
    path('register/', views.register, name='register'),
    path('confirm_account/', views.confirm_account, name='confirm_account'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html', 
        email_template_name='registration/password_reset_email.html', 
        subject_template_name='registration/password_reset_subject.txt', 
        extra_context={'domain':'localhost:8000'}), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html', extra_context={'domain':'localhost:8000'}), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),
    path('world/', views.world_page, name='world'),
    path('accounts/', include('allauth.urls')),
    path('my_profile/', views.profile, name='my_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/profile_settings/', views.profile_settings, name='profile_settings'),
    path('profile/profile_settings/delete_account', views.delete_account, name='delete_account'),
    path('profile/user/<str:username>/followers_count/', views.followers_count, name='followers_count'),
    path('search/', views.search_users, name='search_users'),
    path('profile/user/<str:username>/', views.other_user_profile, name='other_user_profile'),
    path('followers_and_following/user/<str:username>/', views.followers_and_following, name='followers_and_following'),
    path('remove_follower/<int:follower_id>/', views.remove_follower, name='remove_follower'),
    path('unfollow_user/<int:following_id>/', views.unfollow_user, name='unfollow_user'),
    path('follow_requests/', views.follow_requests, name='follow_requests'),
    path('accept_follow_request/<int:request_id>/', views.accept_follow_request, name='accept_follow_request'),
    path('reject_follow_request/<int:request_id>/', views.reject_follow_request, name='reject_follow_request'),
    path('update-city/', views.update_city, name='update_city'),
    path('marketplace/', include('main.market.urls', namespace='market')),
    path('community/', include('main.community.urls', namespace='community')),
    path('events/', include('main.events.urls', namespace='events')),
    path('turism/', include('main.turism.urls', namespace='turism')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)