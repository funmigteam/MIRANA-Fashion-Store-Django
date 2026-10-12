from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import SiteSetting
from shop.models import Category, Product, ProductVariant

from .models import Coupon, Order


class FullFlowTests(TestCase):
    def setUp(self):
        SiteSetting.load()
        self.cat = Category.objects.create(name="پوشاک")
        self.p1 = Product.objects.create(name="تی‌شرت", category=self.cat, price=500000)
        self.v1 = ProductVariant.objects.create(product=self.p1, size="M", color="مشکی", color_hex="#000000", stock=3)
        self.p2 = Product.objects.create(name="کلاه", category=self.cat, price=200000, stock=5, discount_price=150000)
        self.admin = User.objects.create_superuser("admin", password="admin1234")

    def test_public_pages(self):
        for url in ["/", "/shop/", self.cat.get_absolute_url(), self.p1.get_absolute_url(), "/cart/",
                    "/about/", "/faq/", "/how-to-buy/", "/contact/", "/orders/track/", "/accounts/login/",
                    "/accounts/register/", "/shop/?q=کلاه&sort=cheap&sale=1&stock=1"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get("/nope/").status_code, 404)

    def test_full_order_flow(self):
        r = self.client.post("/accounts/register/", {
            "first_name": "سارا", "last_name": "احمدی", "mobile": "۰۹۱۲۱۲۳۴۵۶۷",
            "password1": "secret12", "password2": "secret12",
        })
        self.assertEqual(r.status_code, 302)
        user = User.objects.get(username="09121234567")

        r = self.client.post("/cart/add/", {"product": self.p1.pk, "variant": self.v1.pk, "qty": 2},
                             HTTP_X_REQUESTED_WITH="fetch")
        self.assertTrue(r.json()["ok"])
        r = self.client.post("/cart/add/", {"product": self.p2.pk, "qty": 1}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.json()["count"], 3)
        r = self.client.post("/cart/add/", {"product": self.p1.pk}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 400)

        Coupon.objects.create(code="OFF10", percent=10)
        self.client.post("/orders/checkout/", {"action": "coupon", "coupon": "off10"})
        r = self.client.post("/orders/checkout/", {
            "full_name": "سارا احمدی", "phone": "09121234567", "province": "تهران", "city": "تهران",
            "address": "خیابان آزادی", "postal_code": "1234567890", "shipping_method": "post", "save_address": "on",
        })
        order = Order.objects.get(user=user)
        self.assertRedirects(r, reverse("orders:send", args=[order.code]))
        self.assertEqual(order.status, Order.PENDING)
        self.assertEqual(order.subtotal, 1150000)
        self.assertEqual(order.discount, 115000)
        self.assertEqual(order.total, 1150000 - 115000 + 70000)
        self.v1.refresh_from_db()
        self.p2.refresh_from_db()
        self.assertEqual(self.v1.stock, 1)
        self.assertEqual(self.p2.stock, 4)

        r = self.client.get(reverse("orders:send", args=[order.code]))
        self.assertContains(r, "https://t.me/mirana_admin")
        self.assertContains(r, "https://rubika.ir/mirana_admin")
        self.assertContains(r, f"/panel/orders/{order.code}/")

        self.assertEqual(self.client.get(order.get_panel_url()).status_code, 302)

        self.client.logout()
        r = self.client.post("/panel/login/", {"username": "admin", "password": "admin1234"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get(order.get_panel_url()).status_code, 200)
        self.client.post(reverse("dashboard:order_status", args=[order.code]), {"status": "paid"})
        self.client.post(reverse("dashboard:order_status", args=[order.code]), {"status": "preparing"})
        self.client.post(reverse("dashboard:order_status", args=[order.code]), {"status": "shipped"})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.PREPARING)
        self.client.post(reverse("dashboard:order_status", args=[order.code]), {"status": "shipped", "tracking_code": "۱۲۳۴۵۶۷۸۹۰۱۲"})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.SHIPPED)
        self.assertEqual(order.tracking_code, "123456789012")
        self.assertIsNotNone(order.paid_at)
        self.assertEqual(order.logs.count(), 4)

        self.client.logout()
        self.client.post("/accounts/login/", {"username": "09121234567", "password": "secret12"})
        r = self.client.get(order.get_absolute_url())
        self.assertContains(r, "123456789012")
        r = self.client.get("/orders/track/", {"code": order.code, "phone": "09121234567"})
        self.assertContains(r, "123456789012")

    def test_cancel_restores_stock(self):
        user = User.objects.create_user("09120000000", password="x123456")
        self.client.force_login(user)
        self.client.post("/cart/add/", {"product": self.p2.pk, "qty": 3})
        self.client.post("/orders/checkout/", {
            "full_name": "علی", "phone": "09120000000", "province": "تهران", "city": "تهران",
            "address": "آدرس", "postal_code": "1234567890", "shipping_method": "post",
        })
        order = Order.objects.get(user=user)
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.stock, 2)
        self.client.post(reverse("orders:cancel", args=[order.code]))
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.stock, 5)

    def test_dashboard_pages_and_product_create(self):
        self.client.force_login(self.admin)
        for name in ["home", "orders", "products", "product_add", "categories", "category_add", "coupons",
                     "coupon_add", "banners", "banner_add", "users", "user_add", "messages", "settings", "badges"]:
            self.assertEqual(self.client.get(reverse(f"dashboard:{name}")).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("dashboard:product_edit", args=[self.p1.pk])).status_code, 200)
        r = self.client.post(reverse("dashboard:product_add"), {
            "name": "شلوار جدید", "category": self.cat.pk, "gender": "men", "price": 900000, "stock": 0,
            "is_active": "on",
            "img-TOTAL_FORMS": 0, "img-INITIAL_FORMS": 0,
            "var-TOTAL_FORMS": 2, "var-INITIAL_FORMS": 0,
            "var-0-color": "مشکی", "var-0-color_hex": "#000000", "var-0-size": "32", "var-0-stock": 4, "var-0-extra_price": 0,
            "var-1-color": "مشکی", "var-1-color_hex": "#000000", "var-1-size": "34", "var-1-stock": 2, "var-1-extra_price": 0,
        })
        self.assertEqual(r.status_code, 302)
        p = Product.objects.get(name="شلوار جدید")
        self.assertEqual(p.total_stock, 6)
        self.assertTrue(p.sku.startswith("MRN-"))
