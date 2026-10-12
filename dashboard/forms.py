from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from core.models import Banner, SiteSetting
from orders.models import Coupon, Order
from shop.models import Category, Product, ProductImage, ProductVariant


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "category", "gender", "price", "discount_price", "stock", "image",
            "short_description", "description", "material", "care", "sku", "is_active", "is_featured",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "short_description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.select_related("parent").order_by("parent__order", "order")
        self.fields["sku"].required = False
        self.fields["sku"].help_text = "خالی بگذارید تا خودکار ساخته شود."

    def clean(self):
        c = super().clean()
        p, d = c.get("price"), c.get("discount_price")
        if p and d and d >= p:
            self.add_error("discount_price", "قیمت با تخفیف باید کمتر از قیمت اصلی باشد.")
        return c


ImageFormSet = inlineformset_factory(
    Product, ProductImage, fields=["image", "order"], extra=0, can_delete=True,
)
VariantFormSet = inlineformset_factory(
    Product, ProductVariant, fields=["color", "color_hex", "size", "stock", "extra_price"],
    extra=0, can_delete=True, widgets={"color_hex": forms.TextInput(attrs={"type": "color"})},
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "parent", "description", "image", "order", "is_active", "slug"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Category.objects.filter(parent__isnull=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = qs
        self.fields["parent"].empty_label = "— دسته اصلی —"
        self.fields["slug"].required = False
        self.fields["slug"].help_text = "آدرس دسته در سایت؛ خالی بگذارید تا خودکار ساخته شود."


class CouponForm(forms.ModelForm):
    valid_until = forms.DateTimeField(
        label="معتبر تا (اختیاری)", required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Coupon
        fields = ["code", "percent", "amount", "max_discount", "min_total", "usage_limit", "valid_until", "is_active"]

    def clean_percent(self):
        p = self.cleaned_data["percent"]
        if p > 100:
            raise forms.ValidationError("درصد نمی‌تواند بیشتر از ۱۰۰ باشد.")
        return p

    def clean(self):
        c = super().clean()
        if not c.get("percent") and not c.get("amount"):
            raise forms.ValidationError("درصد یا مبلغ ثابت تخفیف را وارد کنید.")
        return c


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ["title", "subtitle", "image", "button_text", "link", "theme", "order", "is_active"]


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = "__all__"
        widgets = {"about": forms.Textarea(attrs={"rows": 5})}


class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name", "phone", "province", "city", "address", "postal_code",
            "shipping_method", "tracking_code", "admin_note", "private_note",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
            "admin_note": forms.Textarea(attrs={"rows": 2}),
            "private_note": forms.Textarea(attrs={"rows": 2}),
        }


class StaffUserForm(forms.ModelForm):
    password = forms.CharField(
        label="رمز عبور جدید", required=False, widget=forms.PasswordInput,
        help_text="برای تغییر ندادن، خالی بگذارید.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff"]
        labels = {
            "username": "نام کاربری / موبایل", "first_name": "نام", "last_name": "نام خانوادگی",
            "email": "ایمیل", "is_active": "فعال", "is_staff": "دسترسی به پنل مدیریت",
        }
        help_texts = {"username": "", "is_staff": "", "is_active": ""}

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
