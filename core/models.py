from django.db import models


class SiteSetting(models.Model):

    site_name = models.CharField("نام سایت", max_length=100, default="میرانا")
    site_name_en = models.CharField("نام لاتین", max_length=100, default="MIRANA")
    slogan = models.CharField("شعار", max_length=200, default="پوشاک و اکسسوری با امضای میرانا")
    announcement = models.CharField(
        "نوار اعلان بالای سایت", max_length=250, blank=True,
        default="ارسال رایگان برای سفارش‌های بالای ۲ میلیون تومان 🚚",
    )
    telegram_id = models.CharField("آیدی تلگرام ادمین (بدون @)", max_length=100, default="mirana_admin")
    rubika_id = models.CharField("آیدی روبیکا ادمین (بدون @)", max_length=100, default="mirana_admin")
    telegram_channel = models.CharField("آیدی کانال تلگرام", max_length=100, blank=True, default="mirana_shop")
    rubika_channel = models.CharField("آیدی کانال روبیکا", max_length=100, blank=True, default="mirana_shop")
    instagram_id = models.CharField("آیدی اینستاگرام", max_length=100, blank=True)
    phone = models.CharField("تلفن پشتیبانی", max_length=50, blank=True, default="۰۹۱۲۰۰۰۰۰۰۰")
    email = models.EmailField("ایمیل", blank=True)
    address = models.CharField("آدرس فروشگاه", max_length=300, blank=True, default="تهران")
    working_hours = models.CharField("ساعت پاسخگویی", max_length=120, blank=True, default="همه‌روزه ۱۰ تا ۲۲")

    card_number = models.CharField("شماره کارت", max_length=30, blank=True, default="6037-0000-0000-0000")
    card_holder = models.CharField("به نام", max_length=100, blank=True, default="میرانا")
    sheba = models.CharField("شماره شبا", max_length=40, blank=True)

    shipping_cost = models.PositiveIntegerField("هزینه ارسال (تومان)", default=70000)
    free_shipping_over = models.PositiveIntegerField(
        "ارسال رایگان برای خرید بالای (تومان) - صفر یعنی غیرفعال", default=2000000
    )
    order_hold_hours = models.PositiveIntegerField("مهلت ارسال رسید پرداخت (ساعت)", default=24)

    about = models.TextField(
        "درباره ما",
        default=(
            "میرانا یک برند پوشاک ایرانی است که با تکیه بر طراحی مینیمال، پارچه‌های باکیفیت و دوخت دقیق، "
            "لباس و اکسسوری روزمره را برای سبک زندگی امروز می‌سازد."
        ),
    )
    footer_text = models.CharField(
        "متن فوتر", max_length=300, blank=True,
        default="تمامی حقوق برای برند میرانا محفوظ است.",
    )

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return "تنظیمات سایت"

    def save(self, *args, **kwargs):
        self.pk = 1
        for f in ("telegram_id", "rubika_id", "telegram_channel", "rubika_channel", "instagram_id"):
            setattr(self, f, (getattr(self, f) or "").strip().lstrip("@"))
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def telegram_url(self):
        return f"https://t.me/{self.telegram_id}" if self.telegram_id else ""

    @property
    def rubika_url(self):
        return f"https://rubika.ir/{self.rubika_id}" if self.rubika_id else ""

    @property
    def telegram_channel_url(self):
        return f"https://t.me/{self.telegram_channel}" if self.telegram_channel else ""

    @property
    def rubika_channel_url(self):
        return f"https://rubika.ir/{self.rubika_channel}" if self.rubika_channel else ""

    @property
    def instagram_url(self):
        return f"https://instagram.com/{self.instagram_id}" if self.instagram_id else ""


class Banner(models.Model):

    title = models.CharField("عنوان", max_length=120)
    subtitle = models.CharField("زیرعنوان", max_length=250, blank=True)
    image = models.ImageField("تصویر", upload_to="banners/", blank=True)
    button_text = models.CharField("متن دکمه", max_length=40, blank=True, default="مشاهده")
    link = models.CharField("لینک", max_length=250, blank=True, default="/shop/")
    theme = models.CharField(
        "رنگ زمینه", max_length=20, default="sand",
        choices=[("sand", "شنی"), ("dark", "تیره"), ("rose", "رز"), ("olive", "زیتونی"), ("sky", "آسمانی")],
    )
    order = models.PositiveIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["order", "-id"]
        verbose_name = "بنر"
        verbose_name_plural = "بنرها"

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField("نام", max_length=100)
    phone = models.CharField("تماس", max_length=50)
    subject = models.CharField("موضوع", max_length=150, blank=True)
    message = models.TextField("پیام")
    is_read = models.BooleanField("خوانده شده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def __str__(self):
        return f"{self.name} - {self.subject}"
