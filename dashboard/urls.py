from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.panel_login, name="login"),
    path("logout/", views.panel_logout, name="logout"),
    path("badges/", views.badge_counts, name="badges"),

    path("orders/", views.order_list, name="orders"),
    path("orders/<str:code>/", views.order_detail, name="order_detail"),
    path("orders/<str:code>/status/", views.order_status, name="order_status"),
    path("orders/<str:code>/invoice/", views.order_invoice, name="order_invoice"),
    path("orders/<str:code>/delete/", views.order_delete, name="order_delete"),

    path("products/", views.product_list, name="products"),
    path("products/add/", views.product_form, name="product_add"),
    path("products/<int:pk>/", views.product_form, name="product_edit"),
    path("products/<int:pk>/toggle/", views.product_toggle, name="product_toggle"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:pk>/duplicate/", views.product_duplicate, name="product_duplicate"),
    path("stock/<int:pk>/", views.stock_update, name="stock_update"),

    path("categories/", views.category_list, name="categories"),
    path("categories/add/", views.category_form, name="category_add"),
    path("categories/<int:pk>/", views.category_form, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    path("coupons/", views.coupon_list, name="coupons"),
    path("coupons/add/", views.coupon_form, name="coupon_add"),
    path("coupons/<int:pk>/", views.coupon_form, name="coupon_edit"),
    path("coupons/<int:pk>/delete/", views.coupon_delete, name="coupon_delete"),

    path("banners/", views.banner_list, name="banners"),
    path("banners/add/", views.banner_form, name="banner_add"),
    path("banners/<int:pk>/", views.banner_form, name="banner_edit"),
    path("banners/<int:pk>/delete/", views.banner_delete, name="banner_delete"),

    path("users/", views.user_list, name="users"),
    path("users/add/", views.user_form, name="user_add"),
    path("users/<int:pk>/", views.user_form, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),

    path("messages/", views.message_list, name="messages"),
    path("messages/<int:pk>/", views.message_action, name="message_action"),
    path("settings/", views.settings_view, name="settings"),
]
