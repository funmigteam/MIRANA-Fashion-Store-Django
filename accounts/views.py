from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from shop.cart import Cart

from .forms import LoginForm, ProfileForm, RegisterForm, UserForm


def _next(request, default="core:home"):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
        return nxt
    return default


def _login_keep_cart(request, user):
    cart_data = Cart(request).data
    coupon = request.session.get("coupon_code")
    login(request, user)
    if cart_data:
        c = Cart(request)
        c.data = cart_data
        c._save()
    if coupon:
        request.session["coupon_code"] = coupon


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        _login_keep_cart(request, user)
        messages.success(request, f"{user.first_name} عزیز، به میرانا خوش آمدید 🌿")
        return redirect(_next(request))
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_next(request))
    form = LoginForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.user
        _login_keep_cart(request, user)
        if not form.cleaned_data.get("remember"):
            request.session.set_expiry(0)
        messages.success(request, f"خوش آمدید {user.get_full_name() or user.username}")
        default = "dashboard:home" if user.is_staff else "core:home"
        return redirect(_next(request, default))
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "با موفقیت خارج شدید.")
    return redirect("core:home")


@login_required
def profile(request):
    uform = UserForm(request.POST or None, instance=request.user, prefix="u")
    pform = ProfileForm(request.POST or None, instance=request.user.profile, prefix="p")
    if request.method == "POST" and uform.is_valid() and pform.is_valid():
        uform.save()
        pform.save()
        messages.success(request, "اطلاعات شما ذخیره شد.")
        return redirect("accounts:profile")
    orders = request.user.orders.all()
    return render(request, "accounts/profile.html", {
        "uform": uform, "pform": pform,
        "orders_recent": orders[:3], "orders_count": orders.count(),
        "orders_open": orders.exclude(status__in=["delivered", "cancelled"]).count(),
    })


@login_required
def password_change(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    form.fields["old_password"].label = "رمز فعلی"
    form.fields["new_password1"].label = "رمز جدید"
    form.fields["new_password1"].help_text = ""
    form.fields["new_password2"].label = "تکرار رمز جدید"
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "رمز عبور تغییر کرد.")
        return redirect("accounts:profile")
    return render(request, "accounts/password.html", {"form": form})
