from django.contrib import admin

from .models import Banner, ContactMessage, SiteSetting

admin.site.register(SiteSetting)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["title", "order", "is_active"]
    list_editable = ["order", "is_active"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "subject", "is_read", "created_at"]
    list_filter = ["is_read"]
