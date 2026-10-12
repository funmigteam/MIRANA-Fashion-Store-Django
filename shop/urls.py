from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("shop/", views.product_list, name="list"),
    path("category/<str:slug>/", views.product_list, name="category"),
    path("p/<int:pk>/", views.product_detail, name="product_short"),
    path("p/<int:pk>/<str:slug>/", views.product_detail, name="product"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/", views.cart_remove, name="cart_remove"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:pk>/", views.wishlist_toggle, name="wishlist_toggle"),
]
