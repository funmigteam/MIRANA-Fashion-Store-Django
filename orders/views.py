from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import SiteSetting
from shop.cart import Cart
from shop.models import Product, ProductVariant

from .forms import CheckoutForm, ReceiptForm, TrackForm
from .models import Coupon, Order, OrderItem, OrderStatusLog


def _totals(request, items):
    s = SiteSetting.load()
    subtotal = sum(i["total"] for i in items)
    discount, coupon = 0, None
    code = request.session.get("coupon_code")
    if code:
        coupon = Coupon.objects.filter(code=code).first()
        ok = coupon and coupon.validate_for(subtotal)[0]
        if ok:
            discount = coupon.discount_for(subtotal)
        else:
            request.session.pop("coupon_code", None)
            coupon = None
    free = bool(s.free_shipping_over) and subtotal >= s.free_shipping_over
    shipping = 0 if free else s.shipping_cost
    return {
        "subtotal": subtotal, "discount": discount, "coupon": coupon,
        "shipping": shipping, "total": max(0, subtotal - discount) + shipping,
    }


@login_required
def checkout(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        messages.info(request, "سبد خرید شما خالی است.")
        return redirect("shop:cart")

    if request.method == "POST" and request.POST.get("action") in ("coupon", "remove_coupon"):
        if request.POST["action"] == "remove_coupon":
            request.session.pop("coupon_code", None)
            messages.info(request, "کد تخفیف حذف شد.")
        else:
            code = request.POST.get("coupon", "").strip().upper()
            coupon = Coupon.objects.filter(code=code).first()
            if not coupon:
                messages.error(request, "کد تخفیف نامعتبر است.")
            else:
                ok, msg = coupon.validate_for(cart.subtotal(items))
                (messages.success if ok else messages.error)(request, msg)
                if ok:
                    request.session["coupon_code"] = code
        return redirect("orders:checkout")

    p = request.user.profile
    initial = {
        "full_name": request.user.get_full_name(), "phone": p.phone or request.user.username,
        "province": p.province, "city": p.city, "address": p.address, "postal_code": p.postal_code,
    }
    form = CheckoutForm(request.POST or None, initial=initial)
    totals = _totals(request, items)

    if request.method == "POST" and form.is_valid():
        try:
            order = _create_order(request, form, items, totals)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("shop:cart")
        if form.cleaned_data.get("save_address"):
            for f in ("phone", "province", "city", "address", "postal_code"):
                setattr(p, f, form.cleaned_data[f])
            p.save()
        cart.clear()
        return redirect("orders:send", code=order.code)

    return render(request, "orders/checkout.html", {"form": form, "items": items, **totals})


@transaction.atomic
def _create_order(request, form, items, totals):
    for it in items:
        if it["variant"]:
            locked = ProductVariant.objects.select_for_update().get(pk=it["variant"].pk)
        else:
            locked = Product.objects.select_for_update().get(pk=it["product"].pk)
        if locked.stock < it["qty"]:
            raise ValueError(f"موجودی «{it['product'].name}» کافی نیست. لطفاً سبد خرید را بررسی کنید.")

    order = form.save(commit=False)
    order.user = request.user
    order.subtotal = totals["subtotal"]
    order.discount = totals["discount"]
    order.shipping_cost = totals["shipping"]
    order.total = totals["total"]
    order.coupon = totals["coupon"]
    order.save()
    for it in items:
        v = it["variant"]
        OrderItem.objects.create(
            order=order, product=it["product"], variant=v, product_name=it["product"].name,
            variant_label=v.label if v else "", unit_price=it["unit_price"], quantity=it["qty"],
        )
        if v:
            ProductVariant.objects.filter(pk=v.pk).update(stock=F("stock") - it["qty"])
        else:
            Product.objects.filter(pk=it["product"].pk).update(stock=F("stock") - it["qty"])
    if order.coupon:
        Coupon.objects.filter(pk=order.coupon.pk).update(used=F("used") + 1)
    OrderStatusLog.objects.create(order=order, status=Order.PENDING, by=request.user, note="ثبت پیش‌سفارش توسط مشتری")
    return order


@login_required
def send_to_admin(request, code):
    order = get_object_or_404(Order, code=code, user=request.user)
    panel_link = request.build_absolute_uri(order.get_panel_url())
    return render(request, "orders/send.html", {
        "order": order, "admin_message": order.message_for_admin(panel_link), "panel_link": panel_link,
    })


@login_required
def my_orders(request):
    orders = request.user.orders.prefetch_related("items")
    status = request.GET.get("status")
    if status in dict(Order.STATUS_CHOICES):
        orders = orders.filter(status=status)
    return render(request, "orders/my_orders.html", {
        "orders": orders, "status": status, "statuses": Order.STATUS_CHOICES,
    })


@login_required
def order_detail(request, code):
    order = get_object_or_404(Order.objects.prefetch_related("items__product", "logs"), code=code, user=request.user)
    return render(request, "orders/detail.html", {"order": order, "receipt_form": ReceiptForm()})


@login_required
@require_POST
def upload_receipt(request, code):
    order = get_object_or_404(Order, code=code, user=request.user, status=Order.PENDING)
    form = ReceiptForm(request.POST, request.FILES, instance=order)
    if form.is_valid():
        form.save()
        OrderStatusLog.objects.create(order=order, status=order.status, by=request.user, note="رسید پرداخت بارگذاری شد")
        messages.success(request, "رسید پرداخت ثبت شد. پس از بررسی، سفارش شما تایید می‌شود.")
    else:
        messages.error(request, "؛ ".join(e for errs in form.errors.values() for e in errs))
    return redirect(order.get_absolute_url())


@login_required
@require_POST
def cancel_order(request, code):
    order = get_object_or_404(Order, code=code, user=request.user)
    if order.status != Order.PENDING:
        messages.error(request, "فقط پیش‌سفارش‌های پرداخت‌نشده قابل لغو هستند.")
    else:
        order.set_status(Order.CANCELLED, by=request.user, note="لغو توسط مشتری")
        messages.info(request, "سفارش لغو شد.")
    return redirect(order.get_absolute_url())


def track(request):
    form = TrackForm(request.GET or None)
    order = None
    if request.GET and form.is_valid():
        order = Order.objects.filter(code=form.cleaned_data["code"], phone=form.cleaned_data["phone"]).first()
        if not order:
            messages.error(request, "سفارشی با این مشخصات پیدا نشد.")
    return render(request, "orders/track.html", {"form": form, "order": order})
