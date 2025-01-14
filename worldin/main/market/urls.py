from django.urls import path
from . import views

app_name = 'market'


urlpatterns = [
    path('my_market_profile/', views.my_market_profile, name='my_market_profile'),
    path('my_market_profile/ratings', views.my_market_ratings, name='my_market_ratings'),
    path('my_market_profile/add_product', views.add_product, name='add_product'),
    path('product_details/<int:product_id>/', views.product_details, name='product_details'),
    path('product/<int:product_id>/send_message/', views.send_message, name='send_message'),
    path('renting/<int:renting_id>/send_message/', views.send_message_renting, name='send_message_renting'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_image/<int:product_id>/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
    path('my_market_profile/add_renting', views.add_renting, name='add_renting'),
    path('renting_details/<int:renting_id>/', views.renting_details, name='renting_details'),
    path('delete_renting/<int:renting_id>/', views.delete_renting, name='delete_renting'),
    path('market/profile/user/<str:username>/', views.market_profile_other_user, name='market_profile_other_user'),
    path('edit_renting/<int:renting_id>/', views.edit_renting, name='edit_renting'),
    path('market/products/city=<str:selected_city>/', views.main_market_products, name="main_market_products"),
    path('market/rentings/city=<str:selected_city>/', views.main_market_rentings, name="main_market_rentings"),
    path('highlight_product/<int:product_id>/', views.highlight_product, name='highlight_product'),
    path('highlight_renting/<int:renting_id>/', views.highlight_renting, name='highlight_renting'),
    path('create-checkout-session-renting/<int:renting_id>/', views.create_checkout_session_renting, name='create_checkout_session_renting'),
    path('create-checkout-session-product/<int:product_id>/', views.create_checkout_session_product, name='create_checkout_session_product'),
    path('payment-success-product/', views.payment_success_product, name='payment_success_product'),
    path('payment-success-renting/', views.payment_success_renting, name='payment_success_renting'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('update_product_highlight_status/', views.update_product_highlight_status, name='update_product_highlight_status'),
    path('update_renting_highlight_status/', views.update_renting_highlight_status, name='update_renting_highlight_status'),
    path('book-product/<int:product_id>/', views.book_product, name='book_product'),
    path('unbook-product/<int:product_id>/', views.unbook_product, name='unbook_product'),
    path('sell-product/<int:product_id>/', views.sell_product, name='sell_product'),
    path('book-renting/<int:renting_id>/', views.book_renting, name='book_renting'),
    path('unbook-renting/<int:renting_id>/', views.unbook_renting, name='unbook_renting'),
    path('sell-renting/<int:renting_id>/', views.sell_renting, name='sell_renting'),
    path('market/profile/ratings/user/<str:username>/', views.other_user_ratings, name='other_user_ratings'),


]