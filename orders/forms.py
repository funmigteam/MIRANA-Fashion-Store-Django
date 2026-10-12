import re

from django import forms

from core.jalali import to_en_digits

from .models import Order

PROVINCES = [
    "آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "اصفهان", "البرز", "ایلام", "بوشهر", "تهران",
    "چهارمحال و بختیاری", "خراسان جنوبی", "خراسان رضوی", "خراسان شمالی", "خوزستان", "زنجان",
    "سمنان", "سیستان و بلوچستان", "فارس", "قزوین", "قم", "کردستان", "کرمان", "کرمانشاه",
    "کهگیلویه و بویراحمد", "گلستان", "گیلان", "لرستان", "مازندران", "مرکزی", "هرمزگان", "همدان", "یزد",
]


def clean_mobile(value):
    v = to_en_digits(value or "").strip().replace(" ", "").replace("-", "")
    if v.startswith("+98"):
        v = "0" + v[3:]
    elif v.startswith("98") and len(v) == 12:
        v = "0" + v[2:]
    if not re.fullmatch(r"09\d{9}", v):
        raise forms.ValidationError("شماره موبایل معتبر نیست (مثال: ۰۹۱۲۳۴۵۶۷۸۹).")
    return v


class CheckoutForm(forms.ModelForm):
    province = forms.ChoiceField(label="استان", choices=[("", "انتخاب استان")] + [(p, p) for p in PROVINCES])
    save_address = forms.BooleanField(label="ذخیره این آدرس در پروفایل من", required=False, initial=True)

    class Meta:
        model = Order
        fields = ["full_name", "phone", "province", "city", "address", "postal_code", "shipping_method", "note"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": "خیابان، کوچه، پلاک، واحد"}),
            "note": forms.Textarea(attrs={"rows": 2, "placeholder": "اگر توضیحی درباره سفارش دارید بنویسید (اختیاری)"}),
            "shipping_method": forms.RadioSelect,
            "phone": forms.TextInput(attrs={"inputmode": "tel", "placeholder": "۰۹۱۲۳۴۵۶۷۸۹"}),
            "postal_code": forms.TextInput(attrs={"inputmode": "numeric", "placeholder": "۱۰ رقم"}),
        }

    def clean_phone(self):
        return clean_mobile(self.cleaned_data["phone"])

    def clean_postal_code(self):
        v = to_en_digits(self.cleaned_data["postal_code"]).strip().replace("-", "")
        if not re.fullmatch(r"\d{10}", v):
            raise forms.ValidationError("کد پستی باید ۱۰ رقم باشد.")
        return v


class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["receipt"]

    def clean_receipt(self):
        f = self.cleaned_data.get("receipt")
        if not f:
            raise forms.ValidationError("لطفاً تصویر رسید را انتخاب کنید.")
        return f


class TrackForm(forms.Form):
    code = forms.CharField(label="کد سفارش", max_length=12, widget=forms.TextInput(attrs={"placeholder": "MR123456"}))
    phone = forms.CharField(label="موبایل ثبت‌شده در سفارش", max_length=15)

    def clean_code(self):
        return to_en_digits(self.cleaned_data["code"]).strip().upper()

    def clean_phone(self):
        return clean_mobile(self.cleaned_data["phone"])
