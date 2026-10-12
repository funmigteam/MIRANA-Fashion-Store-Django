from django.contrib import messages
from django.shortcuts import redirect, render

from shop.models import Category, Product

from .forms import ContactForm
from .models import Banner


def home(request):
    products = Product.objects.filter(is_active=True).select_related("category").prefetch_related("variants", "images")
    context = {
        "banners": Banner.objects.filter(is_active=True),
        "categories": Category.objects.filter(is_active=True, parent__isnull=True),
        "featured": products.filter(is_featured=True)[:8],
        "newest": products[:8],
        "best": products.order_by("-sold", "-views")[:8],
        "sale": products.filter(discount_price__isnull=False)[:4],
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def how_to_buy(request):
    return render(request, "core/how_to_buy.html")


def faq(request):
    return render(request, "core/faq.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "پیام شما دریافت شد. به زودی با شما تماس می‌گیریم.")
        return redirect("core:contact")
    return render(request, "core/contact.html", {"form": form})


def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)
