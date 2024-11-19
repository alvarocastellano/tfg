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
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
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
    path('my_market_profile/', views.my_market_profile, name='my_market_profile'),
    path('my_market_profile/ratings', views.my_market_ratings, name='my_market_ratings'),
    path('my_market_profile/add_product', views.add_product, name='add_product'),
    path('update-city/', views.update_city, name='update_city'),
    path('product_details/<int:product_id>/', views.product_details, name='product_details'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_image/<int:product_id>/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
    path('my_market_profile/add_renting', views.add_renting, name='add_renting'),
    path('renting_details/<int:renting_id>/', views.renting_details, name='renting_details'),
    path('delete_renting/<int:renting_id>/', views.delete_renting, name='delete_renting'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)