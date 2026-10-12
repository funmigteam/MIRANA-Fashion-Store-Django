from shop.cart import Cart
from shop.models import Category

from .models import SiteSetting


def site(request):
    cart = Cart(request)
    wish_ids = []
    if request.user.is_authenticated:
        wish_ids = list(request.user.wishlist.values_list("product_id", flat=True))
    return {
        "site": SiteSetting.load(),
        "nav_categories": Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children"),
        "cart_count": cart.count(),
        "wish_ids": wish_ids,
    }
