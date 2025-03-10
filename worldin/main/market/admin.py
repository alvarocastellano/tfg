from django.contrib import admin
from .models import Product, ProductImage, Rental, RentalImage, RentalFeature, Rating


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'title', 'description', 'price', 'city_associated', 'status', 'buyer')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'title', 'owner')  # Campos para búsqueda.

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'image')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'product')  # Campos para búsqueda.

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'title', 'location', 'description', 'square_meters', 'rooms', 'max_people', 'price', 'city_associated')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'title', 'owner')  # Campos para búsqueda.

@admin.register(RentalImage)
class RentalImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'rental', 'image')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'rental')  # Campos para búsqueda.

@admin.register(RentalFeature)
class RentalFeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'feature')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'feature')  # Campos para búsqueda.

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'renting', 'rating', 'comment')  # Personaliza los campos que quieras ver en el listado.
    search_fields = ('id', 'user')  # Campos para búsqueda.
