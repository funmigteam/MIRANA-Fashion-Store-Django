from django.contrib import admin

from .models import Category, Product, ProductImage, ProductVariant, Wishlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "order", "is_active"]
    list_editable = ["order", "is_active"]


class ImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "category", "price", "discount_price", "is_active", "is_featured"]
    list_filter = ["category", "is_active", "is_featured", "gender"]
    search_fields = ["name", "sku"]
    inlines = [VariantInline, ImageInline]


admin.site.register(Wishlist)
