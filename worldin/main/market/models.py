from django.db import models
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta

class Product(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    city_associated = models.CharField(max_length=200, blank=True)
    money_associated = models.CharField(max_length=50, blank = True)
    highlighted = models.BooleanField(default=False)
    highlighted_until = models.DateTimeField(null=True, blank=True)
    highlighted_at = models.DateTimeField(null=True, blank=True)
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
    
    def set_highlighted(self, days=31):
        """Activa el destacado del producto y ajusta la fecha correspondiente."""
        self.highlighted = True
        self.highlighted_until = now() + timedelta(days=days)
        self.highlighted_at = now()
        self.save()

    def unset_highlighted(self):
        """Desactiva el destacado del producto y elimina la fecha correspondiente."""
        self.highlighted = False
        self.highlighted_until = None
        self.highlighted_at = None
        self.save()
    
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
    city_associated = models.CharField(max_length=100, blank=True)
    features = models.ManyToManyField(RentalFeature, blank=True)
    money_associated = models.CharField(max_length=50, blank = True)
    highlighted = models.BooleanField(default=False)
    highlighted_until = models.DateTimeField(null=True, blank=True)
    highlighted_at = models.DateTimeField(null=True, blank=True)
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
    
    def set_highlighted(self, days=31):
        """Activa el destacado del alquiler y ajusta las fechas correspondientes."""
        self.highlighted = True
        self.highlighted_until = now() + timedelta(days=days)
        self.highlighted_at = now()
        self.save()

    def unset_highlighted(self):
        """Desactiva el destacado del alquiler y elimina las fechas correspondientes."""
        self.highlighted = False
        self.highlighted_until = None
        self.highlighted_at = None
        self.save()
    
class RentalImage(models.Model):
    rental = models.ForeignKey(Rental, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='rental_pictures/', blank=False)

    def __str__(self):
        return f"Image for {self.rental.title}"