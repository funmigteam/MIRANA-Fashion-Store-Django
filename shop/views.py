from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.jalali import to_en_digits
from core.models import SiteSetting

from .cart import Cart
from .models import Category, Product, ProductVariant, Wishlist

SORTS = {
    "new": ("-created_at", "جدیدترین"),
    "popular": ("-views", "پربازدیدترین"),
    "best": ("-sold", "پرفروش‌ترین"),
    "cheap": ("price", "ارزان‌ترین"),
    "expensive": ("-price", "گران‌ترین"),
}


def _int(v):
    try:
        return int(to_en_digits(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def product_list(request, slug=None):
    qs = Product.objects.filter(is_active=True).select_related("category").prefetch_related("variants", "images")
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        qs = qs.filter(category_id__in=category.family_ids())

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(short_description__icontains=q)
            | Q(category__name__icontains=q) | Q(sku__iexact=q)
        )
    gender = request.GET.get("gender")
    if gender in dict(Product.GENDER_CHOICES):
        qs = qs.filter(gender__in=[gender, "unisex"])
    pmin, pmax = _int(request.GET.get("min")), _int(request.GET.get("max"))
    if pmin is not None:
        qs = qs.filter(price__gte=pmin)
    if pmax is not None:
        qs = qs.filter(price__lte=pmax)
    if request.GET.get("sale"):
        qs = qs.filter(discount_price__isnull=False)
    if request.GET.get("stock"):
        qs = qs.filter(Q(stock__gt=0) | Q(variants__stock__gt=0)).distinct()
    size = request.GET.get("size")
    if size:
        qs = qs.filter(variants__size=size, variants__stock__gt=0).distinct()

    sort = request.GET.get("sort", "new")
    qs = qs.order_by(SORTS.get(sort, SORTS["new"])[0], "-id")

    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    all_sizes = (
        ProductVariant.objects.filter(product__is_active=True).exclude(size="")
        .values_list("size", flat=True).distinct().order_by("size")
    )
    return render(request, "shop/product_list.html", {
        "page": page, "category": category, "q": q, "sort": sort,
        "sorts": {k: v[1] for k, v in SORTS.items()},
        "genders": Product.GENDER_CHOICES[1:], "sizes": list(all_sizes),
    })


def product_detail(request, pk, slug=None):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images", "variants"),
        pk=pk, is_active=True,
    )
    Product.objects.filter(pk=pk).update(views=F("views") + 1)
    related = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(pk=pk).prefetch_related("variants", "images").order_by("?")[:4]
    )
    variants = [
        {"id": v.pk, "size": v.size, "color": v.color, "hex": v.color_hex,
         "stock": v.stock, "price": product.final_price + v.extra_price}
        for v in product.variants.all()
    ]
    return render(request, "shop/product_detail.html", {
        "product": product, "related": related, "variants": variants,
    })


def _cart_json(request, cart, ok=True, msg=""):
    items = cart.items()
    return JsonResponse({"ok": ok, "message": msg, "count": cart.count(), "subtotal": cart.subtotal(items)})


@require_POST
def cart_add(request):
    product = get_object_or_404(Product, pk=request.POST.get("product"), is_active=True)
    qty = max(1, _int(request.POST.get("qty")) or 1)
    variant = None
    if product.has_variants:
        vid = request.POST.get("variant")
        variant = ProductVariant.objects.filter(pk=vid or 0, product=product).first()
        if not variant:
            msg = "لطفاً سایز / رنگ را انتخاب کنید."
            if request.headers.get("x-requested-with") == "fetch":
                return JsonResponse({"ok": False, "message": msg}, status=400)
            messages.error(request, msg)
            return redirect(product.get_absolute_url())
    stock = variant.stock if variant else product.stock
    cart = Cart(request)
    if stock <= 0:
        ok, msg = False, "متاسفانه این محصول موجود نیست."
    else:
        before = cart.data.get(Cart.key(product.pk, variant.pk if variant else None), {}).get("qty", 0)
        after = cart.add(product, variant, qty)
        if after == before:
            ok, msg = False, "به سقف موجودی این محصول رسیده‌اید."
        else:
            ok, msg = True, f"«{product.name}» به سبد خرید اضافه شد."
    if request.headers.get("x-requested-with") == "fetch":
        return _cart_json(request, cart, ok, msg)
    (messages.success if ok else messages.error)(request, msg)
    return redirect(request.POST.get("next") or "shop:cart")


@require_POST
def cart_update(request):
    cart = Cart(request)
    key = request.POST.get("key", "")
    if key in cart.data:
        pid, vid = (int(x) for x in key.split(":"))
        product = get_object_or_404(Product, pk=pid)
        variant = ProductVariant.objects.filter(pk=vid).first() if vid else None
        qty = _int(request.POST.get("qty"))
        if qty is not None:
            cart.add(product, variant, qty, replace=True)
    if request.headers.get("x-requested-with") == "fetch":
        return _cart_json(request, cart)
    return redirect("shop:cart")


@require_POST
def cart_remove(request):
    cart = Cart(request)
    cart.remove(request.POST.get("key", ""))
    if request.headers.get("x-requested-with") == "fetch":
        return _cart_json(request, cart, msg="از سبد حذف شد.")
    messages.info(request, "محصول از سبد خرید حذف شد.")
    return redirect("shop:cart")


def cart_detail(request):
    cart = Cart(request)
    items = cart.items()
    subtotal = cart.subtotal(items)
    s = SiteSetting.load()
    free = bool(s.free_shipping_over) and subtotal >= s.free_shipping_over
    shipping = 0 if (free or not items) else s.shipping_cost
    remain = max(0, s.free_shipping_over - subtotal) if s.free_shipping_over else 0
    progress = min(100, subtotal * 100 // s.free_shipping_over) if s.free_shipping_over else 100
    return render(request, "shop/cart.html", {
        "items": items, "subtotal": subtotal, "shipping": shipping,
        "total": subtotal + shipping, "free_remain": remain, "free_progress": progress,
    })


@require_POST
def wishlist_toggle(request, pk):
    if not request.user.is_authenticated:
        if request.headers.get("x-requested-with") == "fetch":
            return JsonResponse({"ok": False, "login": True, "message": "برای افزودن به علاقه‌مندی‌ها وارد شوید."}, status=401)
        return redirect("accounts:login")
    product = get_object_or_404(Product, pk=pk)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
    msg = "به علاقه‌مندی‌ها اضافه شد." if created else "از علاقه‌مندی‌ها حذف شد."
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"ok": True, "active": created, "message": msg})
    messages.success(request, msg)
    return redirect(request.POST.get("next") or product.get_absolute_url())


@login_required
def wishlist(request):
    products = Product.objects.filter(wished_by__user=request.user, is_active=True).prefetch_related("variants", "images")
    return render(request, "shop/wishlist.html", {"products": products})
