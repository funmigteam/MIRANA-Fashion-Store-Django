from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.models import User

from core.jalali import to_en_digits
from orders.forms import PROVINCES, clean_mobile

from .models import Profile


class RegisterForm(forms.Form):
    first_name = forms.CharField(label="نام", max_length=50)
    last_name = forms.CharField(label="نام خانوادگی", max_length=50)
    mobile = forms.CharField(label="شماره موبایل", max_length=15,
                             widget=forms.TextInput(attrs={"inputmode": "tel", "placeholder": "۰۹۱۲۳۴۵۶۷۸۹"}))
    password1 = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تکرار رمز عبور", widget=forms.PasswordInput)

    def clean_mobile(self):
        m = clean_mobile(self.cleaned_data["mobile"])
        if User.objects.filter(username=m).exists():
            raise forms.ValidationError("با این شماره قبلاً ثبت‌نام شده است. وارد شوید.")
        return m

    def clean(self):
        c = super().clean()
        p1, p2 = c.get("password1"), c.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "رمز عبور و تکرار آن یکسان نیستند.")
        elif p1:
            try:
                password_validation.validate_password(p1)
            except forms.ValidationError:
                self.add_error("password1", "رمز عبور باید حداقل ۶ کاراکتر باشد.")
        return c

    def save(self):
        c = self.cleaned_data
        user = User.objects.create_user(
            username=c["mobile"], password=c["password1"],
            first_name=c["first_name"], last_name=c["last_name"],
        )
        user.profile.phone = c["mobile"]
        user.profile.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(label="موبایل یا نام کاربری", max_length=150)
    password = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)
    remember = forms.BooleanField(label="مرا به خاطر بسپار", required=False, initial=True)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        c = super().clean()
        u, p = c.get("username"), c.get("password")
        if u and p:
            u = to_en_digits(u).strip()
            try:
                u2 = clean_mobile(u)
            except forms.ValidationError:
                u2 = u
            self.user = authenticate(self.request, username=u2, password=p) or authenticate(
                self.request, username=u, password=p
            )
            if not self.user:
                raise forms.ValidationError("نام کاربری یا رمز عبور اشتباه است.")
            if not self.user.is_active:
                raise forms.ValidationError("حساب کاربری شما غیرفعال شده است.")
        return c


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {"first_name": "نام", "last_name": "نام خانوادگی", "email": "ایمیل (اختیاری)"}


class ProfileForm(forms.ModelForm):
    province = forms.ChoiceField(label="استان", required=False,
                                 choices=[("", "انتخاب استان")] + [(p, p) for p in PROVINCES])

    class Meta:
        model = Profile
        fields = ["phone", "province", "city", "address", "postal_code"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        v = self.cleaned_data.get("phone")
        return clean_mobile(v) if v else v

    def clean_postal_code(self):
        return to_en_digits(self.cleaned_data.get("postal_code") or "").strip()
