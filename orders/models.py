import random

from django.conf import settings
from django.db import models, transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone


class Coupon(models.Model):
    code = models.CharField("کد تخفیف", max_length=30, unique=True)
    percent = models.PositiveIntegerField("درصد تخفیف", default=0)
    amount = models.PositiveIntegerField("مبلغ ثابت تخفیف (تومان)", default=0)
    max_discount = models.PositiveIntegerField("سقف تخفیف (تومان) - صفر یعنی بدون سقف", default=0)
    min_total = models.PositiveIntegerField("حداقل مبلغ سفارش (تومان)", default=0)
    usage_limit = models.PositiveIntegerField("سقف دفعات استفاده - صفر یعنی نامحدود", default=0)
    used = models.PositiveIntegerField("دفعات استفاده‌شده", default=0)
    valid_until = models.DateTimeField("معتبر تا", null=True, blank=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def validate_for(self, subtotal):
        if not self.is_active:
            return False, "این کد تخفیف غیرفعال است."
        if self.valid_until and self.valid_until < timezone.now():
            return False, "مهلت استفاده از این کد تمام شده است."
        if self.usage_limit and self.used >= self.usage_limit:
            return False, "ظرفیت استفاده از این کد تکمیل شده است."
        if subtotal < self.min_total:
            return False, f"حداقل مبلغ سفارش برای این کد {self.min_total:,} تومان است."
        return True, "کد تخفیف اعمال شد."

    def discount_for(self, subtotal):
        d = self.amount + subtotal * self.percent // 100
        if self.max_discount:
            d = min(d, self.max_discount)
        return min(d, subtotal)


class Order(models.Model):
    PENDING, PAID, PREPARING, SHIPPED, DELIVERED, CANCELLED = (
        "pending", "paid", "preparing", "shipped", "delivered", "cancelled",
    )
    STATUS_CHOICES = [
        (PENDING, "پیش‌سفارش - در انتظار پرداخت"),
        (PAID, "پرداخت تایید شد"),
        (PREPARING, "در حال آماده‌سازی"),
        (SHIPPED, "ارسال شد"),
        (DELIVERED, "تحویل داده شد"),
        (CANCELLED, "لغو شده"),
    ]
    FLOW = [PENDING, PAID, PREPARING, SHIPPED, DELIVERED]
    SHIPPING_CHOICES = [
        ("post", "پست پیشتاز"),
        ("tipax", "تیپاکس"),
        ("courier", "پیک (فقط تهران)"),
    ]

    code = models.CharField("کد سفارش", max_length=12, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="کاربر", on_delete=models.SET_NULL,
        null=True, related_name="orders",
    )
    status = models.CharField("وضعیت", max_length=12, choices=STATUS_CHOICES, default=PENDING, db_index=True)

    full_name = models.CharField("نام و نام خانوادگی گیرنده", max_length=120)
    phone = models.CharField("موبایل گیرنده", max_length=15)
    province = models.CharField("استان", max_length=50)
    city = models.CharField("شهر", max_length=50)
    address = models.TextField("آدرس کامل")
    postal_code = models.CharField("کد پستی", max_length=10)
    note = models.TextField("توضیحات سفارش", blank=True)
    shipping_method = models.CharField("روش ارسال", max_length=10, choices=SHIPPING_CHOICES, default="post")

    subtotal = models.PositiveIntegerField("جمع اقلام", default=0)
    discount = models.PositiveIntegerField("تخفیف", default=0)
    shipping_cost = models.PositiveIntegerField("هزینه ارسال", default=0)
    total = models.PositiveIntegerField("مبلغ قابل پرداخت", default=0)
    coupon = models.ForeignKey(Coupon, verbose_name="کد تخفیف", null=True, blank=True, on_delete=models.SET_NULL)

    receipt = models.ImageField("تصویر رسید پرداخت", upload_to="receipts/", blank=True)
    tracking_code = models.CharField("کد رهگیری مرسوله", max_length=60, blank=True)
    admin_note = models.TextField("یادداشت ادمین (برای مشتری نمایش داده می‌شود)", blank=True)
    private_note = models.TextField("یادداشت داخلی (فقط ادمین)", blank=True)

    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین تغییر", auto_now=True)
    paid_at = models.DateTimeField("تاریخ تایید پرداخت", null=True, blank=True)
    shipped_at = models.DateTimeField("تاریخ ارسال", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"

    def __str__(self):
        return f"سفارش {self.code}"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                code = f"MR{random.randint(100000, 999999)}"
                if not Order.objects.filter(code=code).exists():
                    self.code = code
                    break
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.code])

    def get_panel_url(self):
        return reverse("dashboard:order_detail", args=[self.code])

    @property
    def items_count(self):
        return sum(i.quantity for i in self.items.all())

    @property
    def step(self):
        if self.status == self.CANCELLED:
            return -1
        return self.FLOW.index(self.status)

    @property
    def tracking_url(self):
        if not self.tracking_code:
            return ""
        if self.shipping_method == "post":
            return f"https://tracking.post.ir/?id={self.tracking_code}"
        if self.shipping_method == "tipax":
            return "https://tipaxco.com/tracking"
        return ""

    def message_for_admin(self, panel_link):
        lines = [
            "سلام وقت بخیر 🌸",
            f"سفارش من در سایت میرانا با کد {self.code} ثبت شد.",
            f"گیرنده: {self.full_name} - {self.phone}",
            "اقلام:",
        ]
        for it in self.items.all():
            v = f" ({it.variant_label})" if it.variant_label else ""
            lines.append(f"• {it.product_name}{v} × {it.quantity}")
        lines += [
            f"مبلغ قابل پرداخت: {self.total:,} تومان",
            "لینک سفارش:",
            panel_link,
            "رسید پرداخت را هم ضمیمه می‌کنم. 🙏",
        ]
        return "\n".join(lines)

    @transaction.atomic
    def set_status(self, new_status, by=None, note=""):
        old = self.status
        if new_status == old:
            return False
        now = timezone.now()
        if new_status == self.CANCELLED and old != self.CANCELLED:
            self._restock(+1)
        elif old == self.CANCELLED and new_status != self.CANCELLED:
            self._restock(-1)
        if new_status in (self.PAID, self.PREPARING, self.SHIPPED, self.DELIVERED) and not self.paid_at:
            self.paid_at = now
            for it in self.items.all():
                if it.product_id:
                    type(it.product).objects.filter(pk=it.product_id).update(sold=F("sold") + it.quantity)
        if new_status in (self.SHIPPED, self.DELIVERED) and not self.shipped_at:
            self.shipped_at = now
        self.status = new_status
        self.save()
        OrderStatusLog.objects.create(order=self, status=new_status, by=by, note=note)
        return True

    def _restock(self, sign):
        from shop.models import Product, ProductVariant

        for it in self.items.all():
            delta = F("stock") + it.quantity * sign
            if it.variant_id:
                ProductVariant.objects.filter(pk=it.variant_id).update(stock=delta)
            elif it.product_id:
                Product.objects.filter(pk=it.product_id).update(stock=delta)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("shop.Product", on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey("shop.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField("نام محصول", max_length=200)
    variant_label = models.CharField("مشخصات", max_length=120, blank=True)
    unit_price = models.PositiveIntegerField("قیمت واحد")
    quantity = models.PositiveIntegerField("تعداد", default=1)

    class Meta:
        verbose_name = "قلم سفارش"
        verbose_name_plural = "اقلام سفارش"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    @property
    def total(self):
        return self.unit_price * self.quantity


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="logs")
    status = models.CharField(max_length=12, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=250, blank=True)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
