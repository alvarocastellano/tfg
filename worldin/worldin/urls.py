from django.contrib import admin
from django.urls import path
from main import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    path('', views.home, name='home'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('policy/', views.policy, name='policy'),
    path('usage/', views.usage, name='usage'),
    path('admin/', admin.site.urls),
    path('login/', views.login_user, name='login'),
    path('register/', views.register, name='register'),
    path('confirm_account/', views.confirm_account, name='confirm_account'),
    path('world/', views.world_page, name='world'),
    
    #path('profile/', views.profile, name='profile'),
    #path('profile/edit/', views.edit_profile, name='edit_profile'),
    #path('logout/', views.logout_view, name='logout'),



]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
