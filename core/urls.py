from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("how-to-buy/", views.how_to_buy, name="how_to_buy"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
]
