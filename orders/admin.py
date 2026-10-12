from django.contrib import admin

from .models import Coupon, Order, OrderItem, OrderStatusLog


class ItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class LogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["code", "full_name", "phone", "total", "status", "created_at"]
    list_filter = ["status", "shipping_method"]
    search_fields = ["code", "full_name", "phone", "tracking_code"]
    inlines = [ItemInline, LogInline]


admin.site.register(Coupon)
