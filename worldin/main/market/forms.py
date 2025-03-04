from django import forms
from .models import  Product, Rental, ProductImage, RentalImage
from django.forms import modelformset_factory

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'price']

class ProductImageForm(forms.ModelForm):
    delete_image = forms.BooleanField(required=False, label='Eliminar', initial=False)

    class Meta:
        model = ProductImage
        fields = ['image', 'delete_image']

ProductImageFormSet = modelformset_factory(ProductImage, form=ProductImageForm, extra= 3)

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['title', 'location', 'description', 'price', 'square_meters', 'rooms', 'max_people']

class RentalImageForm(forms.ModelForm):
    class Meta:
        model = RentalImage
        fields = ['image']

RentalImageFormSet = modelformset_factory(RentalImage, form=RentalImageForm, extra=4)