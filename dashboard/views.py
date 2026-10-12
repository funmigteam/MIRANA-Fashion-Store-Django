from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, ProtectedError, Q, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.forms import LoginForm
from core.jalali import jalali, to_en_digits
from core.models import Banner, ContactMessage, SiteSetting
from orders.models import Coupon, Order
from shop.models import Category, Product, ProductVariant

from .forms import (
    BannerForm, CategoryForm, CouponForm, ImageFormSet, OrderEditForm, ProductForm,
    SiteSettingForm, StaffUserForm, VariantFormSet,
)

PAID_STATUSES = [Order.PAID, Order.PREPARING, Order.SHIPPED, Order.DELIVERED]
LOW_STOCK = 3


def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('dashboard:login')}?next={request.get_full_path()}")
        if not request.user.is_staff:
            messages.error(request, "شما به پنل مدیریت دسترسی ندارید.")
            return redirect("core:home")
        return view(request, *args, **kwargs)
    return wrapper


def _page(request, qs, per=20):
    return Paginator(qs, per).get_page(request.GET.get("page"))


def panel_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard:home")
    form = LoginForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not form.user.is_staff:
            form.add_error(None, "این حساب دسترسی مدیریت ندارد.")
        else:
            login(request, form.user)
            nxt = request.GET.get("next", "")
            return redirect(nxt if nxt.startswith("/panel/") else "dashboard:home")
    return render(request, "dashboard/login.html", {"form": form})


@require_POST
def panel_logout(request):
    logout(request)
    return redirect("dashboard:login")


@staff_required
def home(request):
    now = timezone.localtime()
    today = now.date()
    month_start = today.replace(day=1)
    paid = Order.objects.filter(status__in=PAID_STATUSES)

    days = 14
    start = today - timedelta(days=days - 1)
    rows = (
        paid.filter(paid_at__date__gte=start).annotate(d=TruncDate("paid_at"))
        .values("d").annotate(total=Sum("total"), n=Count("id"))
    )
    by_day = {r["d"]: r for r in rows}
    chart, peak = [], 1
    for i in range(days):
        d = start + timedelta(days=i)
        r = by_day.get(d, {})
        chart.append({"label": jalali(d, "short"), "total": r.get("total") or 0, "n": r.get("n") or 0})
        peak = max(peak, r.get("total") or 0)
    for c in chart:
        c["pct"] = round(c["total"] * 100 / peak)

    status_counts = dict(Order.objects.values_list("status").annotate(c=Count("id")))
    max_status = max(status_counts.values(), default=0) or 1
    low_variants = ProductVariant.objects.filter(stock__lte=LOW_STOCK, product__is_active=True).select_related("product")[:8]
    low_products = Product.objects.filter(is_active=True, variants__isnull=True, stock__lte=LOW_STOCK)[:8]

    ctx = {
        "today_orders": Order.objects.filter(created_at__date=today).count(),
        "pending_count": status_counts.get(Order.PENDING, 0),
        "to_ship": status_counts.get(Order.PAID, 0) + status_counts.get(Order.PREPARING, 0),
        "month_revenue": paid.filter(paid_at__date__gte=month_start).aggregate(s=Sum("total"))["s"] or 0,
        "total_revenue": paid.aggregate(s=Sum("total"))["s"] or 0,
        "products_count": Product.objects.count(),
        "users_count": User.objects.filter(is_staff=False).count(),
        "new_users": User.objects.filter(date_joined__date__gte=today - timedelta(days=7)).count(),
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
        "chart": chart,
        "chart_sum": sum(c["total"] for c in chart),
        "status_rows": [
            (k, v, status_counts.get(k, 0), round(status_counts.get(k, 0) * 100 / max_status))
            for k, v in Order.STATUS_CHOICES
        ],
        "recent_orders": Order.objects.select_related("user")[:8],
        "top_products": Product.objects.filter(sold__gt=0).order_by("-sold")[:5],
        "low_variants": low_variants,
        "low_products": low_products,
        "now": now,
    }
    return render(request, "dashboard/home.html", ctx)


@staff_required
def order_list(request):
    qs = Order.objects.select_related("user").annotate(n=Sum("items__quantity")).order_by("-created_at")
    status = request.GET.get("status", "")
    if status in dict(Order.STATUS_CHOICES):
        qs = qs.filter(status=status)
    q = to_en_digits(request.GET.get("q", "").strip())
    if q:
        qs = qs.filter(
            Q(code__icontains=q) | Q(full_name__icontains=q) | Q(phone__icontains=q)
            | Q(tracking_code__icontains=q) | Q(user__username__icontains=q)
        )
    counts = dict(Order.objects.values_list("status").annotate(c=Count("id")))
    return render(request, "dashboard/orders.html", {
        "page": _page(request, qs), "status": status, "q": request.GET.get("q", ""),
        "tabs": [("", "همه", sum(counts.values()))] + [(k, v, counts.get(k, 0)) for k, v in Order.STATUS_CHOICES],
    })


@staff_required
def order_detail(request, code):
    order = get_object_or_404(Order.objects.select_related("user", "coupon"), code=code)
    form = OrderEditForm(request.POST or None, instance=order)
    if request.method == "POST" and request.POST.get("action") == "edit":
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات سفارش ذخیره شد.")
            return redirect(order.get_panel_url())
    return render(request, "dashboard/order_detail.html", {
        "order": order, "form": form,
        "items": order.items.select_related("product"),
        "logs": order.logs.select_related("by"),
        "statuses": Order.STATUS_CHOICES,
    })


@staff_required
@require_POST
def order_status(request, code):
    order = get_object_or_404(Order, code=code)
    new = request.POST.get("status")
    if new not in dict(Order.STATUS_CHOICES):
        messages.error(request, "وضعیت نامعتبر است.")
        return redirect(order.get_panel_url())
    tracking = request.POST.get("tracking_code", "").strip()
    if new == Order.SHIPPED:
        if not (tracking or order.tracking_code):
            messages.error(request, "برای ثبت ارسال، کد رهگیری مرسوله را وارد کنید.")
            return redirect(order.get_panel_url())
        if tracking:
            order.tracking_code = to_en_digits(tracking)
            order.save(update_fields=["tracking_code"])
    note = request.POST.get("note", "").strip()
    if order.set_status(new, by=request.user, note=note):
        messages.success(request, f"وضعیت سفارش {order.code} به «{order.get_status_display()}» تغییر کرد.")
    return redirect(request.POST.get("next") or order.get_panel_url())


@staff_required
def order_invoice(request, code):
    order = get_object_or_404(Order, code=code)
    return render(request, "dashboard/invoice.html", {"order": order, "items": order.items.all()})


@staff_required
@require_POST
def order_delete(request, code):
    order = get_object_or_404(Order, code=code)
    if order.status not in (Order.CANCELLED, Order.DELIVERED):
        order.set_status(Order.CANCELLED, by=request.user, note="حذف سفارش")
    order.delete()
    messages.success(request, "سفارش حذف شد.")
    return redirect("dashboard:orders")


@staff_required
def product_list(request):
    qs = Product.objects.select_related("category").annotate(
        vstock=Sum("variants__stock"), vcount=Count("variants")
    ).order_by("-created_at")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(Q(category_id=cat) | Q(category__parent_id=cat))
    state = request.GET.get("state")
    if state == "active":
        qs = qs.filter(is_active=True)
    elif state == "hidden":
        qs = qs.filter(is_active=False)
    elif state == "sale":
        qs = qs.filter(discount_price__isnull=False)
    elif state == "low":
        qs = qs.filter(Q(vcount=0, stock__lte=LOW_STOCK) | Q(vcount__gt=0, vstock__lte=LOW_STOCK))
    return render(request, "dashboard/products.html", {
        "page": _page(request, qs), "q": q, "cat": cat, "state": state,
        "categories": Category.objects.all(), "low": LOW_STOCK,
    })


@staff_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else Product()
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    images = ImageFormSet(request.POST or None, request.FILES or None, instance=product, prefix="img")
    variants = VariantFormSet(request.POST or None, instance=product, prefix="var")
    if request.method == "POST":
        if form.is_valid() and images.is_valid() and variants.is_valid():
            with transaction.atomic():
                product = form.save()
                images.instance = product
                images.save()
                variants.instance = product
                variants.save()
                start = product.images.count()
                from shop.models import ProductImage
                for i, f in enumerate(request.FILES.getlist("gallery_bulk")):
                    ProductImage.objects.create(product=product, image=f, order=start + i)
            messages.success(request, f"محصول «{product.name}» ذخیره شد.")
            if request.POST.get("and_new"):
                return redirect("dashboard:product_add")
            return redirect("dashboard:product_edit", pk=product.pk)
        messages.error(request, "لطفاً خطاهای فرم را بررسی کنید.")
    return render(request, "dashboard/product_form.html", {
        "form": form, "images": images, "variants": variants, "product": product,
    })


@staff_required
@require_POST
def product_toggle(request, pk):
    p = get_object_or_404(Product, pk=pk)
    field = request.POST.get("field", "is_active")
    if field not in ("is_active", "is_featured"):
        return JsonResponse({"ok": False}, status=400)
    setattr(p, field, not getattr(p, field))
    p.save(update_fields=[field])
    return JsonResponse({"ok": True, "value": getattr(p, field)})


@staff_required
@require_POST
def product_delete(request, pk):
    p = get_object_or_404(Product, pk=pk)
    p.delete()
    messages.success(request, f"محصول «{p.name}» حذف شد.")
    return redirect("dashboard:products")


@staff_required
@require_POST
def product_duplicate(request, pk):
    p = get_object_or_404(Product, pk=pk)
    variants = list(p.variants.all())
    p.pk = None
    p.slug = ""
    p.sku = ""
    p.name = f"{p.name} (کپی)"
    p.is_active = False
    p.views = p.sold = 0
    p.save()
    for v in variants:
        v.pk = None
        v.product = p
        v.save()
    messages.success(request, "یک کپی غیرفعال از محصول ساخته شد.")
    return redirect("dashboard:product_edit", pk=p.pk)


@staff_required
@require_POST
def stock_update(request, pk):
    kind = request.POST.get("kind")
    try:
        value = max(0, int(to_en_digits(request.POST.get("value", "0"))))
    except ValueError:
        return JsonResponse({"ok": False}, status=400)
    model = ProductVariant if kind == "variant" else Product
    model.objects.filter(pk=pk).update(stock=value)
    return JsonResponse({"ok": True, "value": value})


def _simple_form(request, form_class, instance, title, back, template="dashboard/form.html", extra=None):
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "با موفقیت ذخیره شد.")
        return redirect(back)
    return render(request, template, {"form": form, "title": title, "back": back, "obj": instance, **(extra or {})})


@staff_required
def category_list(request):
    cats = Category.objects.filter(parent__isnull=True).prefetch_related("children").annotate(n=Count("products"))
    counts = dict(Category.objects.annotate(n=Count("products")).values_list("pk", "n"))
    return render(request, "dashboard/categories.html", {"categories": cats, "counts": counts})


@staff_required
def category_form(request, pk=None):
    obj = get_object_or_404(Category, pk=pk) if pk else Category()
    return _simple_form(request, CategoryForm, obj, "ویرایش دسته‌بندی" if pk else "دسته‌بندی جدید", "dashboard:categories")


@staff_required
@require_POST
def category_delete(request, pk):
    c = get_object_or_404(Category, pk=pk)
    try:
        c.delete()
        messages.success(request, "دسته‌بندی حذف شد.")
    except ProtectedError:
        messages.error(request, "این دسته (یا زیردسته‌هایش) محصول دارد؛ ابتدا محصولات را منتقل یا حذف کنید.")
    return redirect("dashboard:categories")


@staff_required
def coupon_list(request):
    return render(request, "dashboard/coupons.html", {"coupons": Coupon.objects.all(), "now": timezone.now()})


@staff_required
def coupon_form(request, pk=None):
    obj = get_object_or_404(Coupon, pk=pk) if pk else Coupon()
    return _simple_form(request, CouponForm, obj, "ویرایش کد تخفیف" if pk else "کد تخفیف جدید", "dashboard:coupons")


@staff_required
@require_POST
def coupon_delete(request, pk):
    get_object_or_404(Coupon, pk=pk).delete()
    messages.success(request, "کد تخفیف حذف شد.")
    return redirect("dashboard:coupons")


@staff_required
def banner_list(request):
    return render(request, "dashboard/banners.html", {"banners": Banner.objects.all()})


@staff_required
def banner_form(request, pk=None):
    obj = get_object_or_404(Banner, pk=pk) if pk else Banner()
    return _simple_form(request, BannerForm, obj, "ویرایش اسلاید" if pk else "اسلاید جدید", "dashboard:banners")


@staff_required
@require_POST
def banner_delete(request, pk):
    get_object_or_404(Banner, pk=pk).delete()
    messages.success(request, "اسلاید حذف شد.")
    return redirect("dashboard:banners")


@staff_required
def user_list(request):
    qs = User.objects.annotate(
        n_orders=Count("orders", distinct=True),
        spent=Sum("orders__total", filter=Q(orders__status__in=PAID_STATUSES)),
    ).order_by("-date_joined")
    q = to_en_digits(request.GET.get("q", "").strip())
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    role = request.GET.get("role")
    if role == "staff":
        qs = qs.filter(is_staff=True)
    elif role == "customer":
        qs = qs.filter(is_staff=False)
    elif role == "inactive":
        qs = qs.filter(is_active=False)
    return render(request, "dashboard/users.html", {"page": _page(request, qs), "q": request.GET.get("q", ""), "role": role})


@staff_required
def user_form(request, pk=None):
    obj = get_object_or_404(User, pk=pk) if pk else User()
    if pk and obj.is_superuser and not request.user.is_superuser:
        messages.error(request, "فقط مدیر کل می‌تواند این حساب را ویرایش کند.")
        return redirect("dashboard:users")
    extra = {}
    if pk:
        extra["user_orders"] = obj.orders.all()[:10]
        extra["profile"] = getattr(obj, "profile", None)
    form = StaffUserForm(request.POST or None, instance=obj)
    if not pk:
        form.fields["password"].required = True
        form.fields["password"].help_text = ""
    if request.method == "POST" and form.is_valid():
        u = form.save()
        if u == request.user:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, u)
        messages.success(request, "کاربر ذخیره شد.")
        return redirect("dashboard:users")
    return render(request, "dashboard/user_form.html", {"form": form, "obj": obj, **extra})


@staff_required
@require_POST
def user_delete(request, pk):
    u = get_object_or_404(User, pk=pk)
    if u == request.user or u.is_superuser:
        messages.error(request, "این کاربر قابل حذف نیست.")
    else:
        u.delete()
        messages.success(request, "کاربر حذف شد.")
    return redirect("dashboard:users")


@staff_required
def message_list(request):
    qs = ContactMessage.objects.all()
    if request.GET.get("unread"):
        qs = qs.filter(is_read=False)
    return render(request, "dashboard/messages.html", {"page": _page(request, qs)})


@staff_required
@require_POST
def message_action(request, pk):
    m = get_object_or_404(ContactMessage, pk=pk)
    if request.POST.get("action") == "delete":
        m.delete()
    else:
        m.is_read = not m.is_read
        m.save(update_fields=["is_read"])
    return redirect("dashboard:messages")


@staff_required
def settings_view(request):
    return _simple_form(
        request, SiteSettingForm, SiteSetting.load(), "تنظیمات فروشگاه", "dashboard:settings",
        template="dashboard/settings.html",
    )


@staff_required
def badge_counts(request):
    return JsonResponse({
        "pending": Order.objects.filter(status=Order.PENDING).count(),
        "messages": ContactMessage.objects.filter(is_read=False).count(),
    })
