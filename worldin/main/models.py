from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.timezone import now
# Modelo para representar una afición
class Hobby(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    birthday = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    selected_city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    erasmus = models.BooleanField(default=False)
    show_age = models.BooleanField(default=True) 
    profile_completed = models.BooleanField(default=False)
    account_visibility = models.CharField(max_length=10, choices=[('public', 'Pública'), ('private', 'Privada')], default='public')
    see_own_products = models.BooleanField(default=False)
    aficiones = models.ManyToManyField(Hobby, blank=True)

    groups = models.ManyToManyField(Group, verbose_name='groups', blank=True, related_name='customuser_set')
    user_permissions = models.ManyToManyField(Permission, verbose_name='user permissions', blank=True, related_name='customuser_set')

class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')  # Un usuario no puede seguir al mismo usuario más de una vez

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
class FollowRequest(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_requests_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follow_requests_received', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pendiente'),
            ('accepted', 'Aceptada'),
            ('rejected', 'Rechazada')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username} solicita seguir a {self.receiver.username}"


class Product(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    city_associated = models.CharField(max_length=200, blank=True)
    money_associated = models.CharField(max_length=50, blank = True)
    highlighted = models.BooleanField(default=False)
    highlighted_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def is_highlighted(self):
        """Verifica si el producto aún está destacado."""
        if self.highlighted and self.highlighted_until:
            return now() < self.highlighted_until
        return False
    
    def highlighted_days_left(self):
        """Calcula los días restantes para la destacación del producto."""
        if self.highlighted_until and now() < self.highlighted_until:
            return (self.highlighted_until - now()).days
        return 0
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_pictures/', blank=False)

    def __str__(self):
        return f"Image for {self.product.title}"
    
    
class RentalFeature(models.Model):
    feature = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.feature


class Rental(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rentals')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    square_meters = models.PositiveIntegerField()
    rooms = models.PositiveIntegerField()
    max_people = models.PositiveIntegerField()
    city_associated = models.CharField(max_length=150, blank=True)
    features = models.ManyToManyField(RentalFeature, blank=True)
    money_associated = models.CharField(max_length=50, blank = True)
    highlighted = models.BooleanField(default=False)
    highlighted_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def is_highlighted(self):
        """Verifica si el alquiler aún está destacado."""
        if self.highlighted and self.highlighted_until:
            return now() < self.highlighted_until
        return False
    
    def highlighted_days_left(self):
        """Calcula los días restantes para la destacación del alquiler."""
        if self.highlighted_until and now() < self.highlighted_until:
            return (self.highlighted_until - now()).days
        return 0
    
class RentalImage(models.Model):
    rental = models.ForeignKey(Rental, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='rental_pictures/', blank=False)

    def __str__(self):
        return f"Image for {self.rental.title}"
    
