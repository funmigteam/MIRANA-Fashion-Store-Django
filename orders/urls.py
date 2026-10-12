from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("track/", views.track, name="track"),
    path("", views.my_orders, name="list"),
    path("<str:code>/", views.order_detail, name="detail"),
    path("<str:code>/send/", views.send_to_admin, name="send"),
    path("<str:code>/receipt/", views.upload_receipt, name="receipt"),
    path("<str:code>/cancel/", views.cancel_order, name="cancel"),
]
