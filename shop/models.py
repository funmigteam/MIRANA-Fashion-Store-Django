from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def make_slug(model, text, instance_pk=None):
    base = slugify(text, allow_unicode=True) or "item"
    slug, i = base, 2
    while model.objects.filter(slug=slug).exclude(pk=instance_pk).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


class Category(models.Model):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField("اسلاگ", max_length=120, unique=True, allow_unicode=True, blank=True)
    parent = models.ForeignKey(
        "self", verbose_name="دسته والد", null=True, blank=True,
        on_delete=models.CASCADE, related_name="children",
    )
    description = models.CharField("توضیح کوتاه", max_length=250, blank=True)
    image = models.ImageField("تصویر", upload_to="categories/", blank=True)
    order = models.PositiveIntegerField("ترتیب", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        return f"{self.parent.name} › {self.name}" if self.parent_id else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_slug(Category, self.name, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:category", args=[self.slug])

    def family_ids(self):
        return [self.pk] + list(self.children.values_list("pk", flat=True))


class Product(models.Model):
    GENDER_CHOICES = [
        ("unisex", "همه"),
        ("women", "زنانه"),
        ("men", "مردانه"),
        ("kids", "بچگانه"),
    ]

    name = models.CharField("نام محصول", max_length=200)
    slug = models.SlugField("اسلاگ", max_length=220, unique=True, allow_unicode=True, blank=True)
    sku = models.CharField("کد محصول", max_length=40, blank=True)
    category = models.ForeignKey(
        Category, verbose_name="دسته‌بندی", on_delete=models.PROTECT, related_name="products"
    )
    gender = models.CharField("مناسب برای", max_length=10, choices=GENDER_CHOICES, default="unisex")
    short_description = models.CharField("توضیح کوتاه", max_length=300, blank=True)
    description = models.TextField("توضیحات کامل", blank=True)
    material = models.CharField("جنس", max_length=150, blank=True)
    care = models.CharField("نحوه نگهداری", max_length=250, blank=True)
    price = models.PositiveIntegerField("قیمت (تومان)")
    discount_price = models.PositiveIntegerField("قیمت با تخفیف (تومان)", null=True, blank=True)
    stock = models.PositiveIntegerField(
        "موجودی (برای محصولات بدون تنوع)", default=0,
        help_text="اگر محصول سایز/رنگ دارد، موجودی هر تنوع جداگانه ثبت می‌شود.",
    )
    image = models.ImageField("تصویر اصلی", upload_to="products/", blank=True)
    is_active = models.BooleanField("نمایش در سایت", default=True)
    is_featured = models.BooleanField("محصول ویژه", default=False)
    views = models.PositiveIntegerField("بازدید", default=0)
    sold = models.PositiveIntegerField("تعداد فروش", default=0)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = make_slug(Product, self.name, self.pk)
        if self.discount_price and self.discount_price >= self.price:
            self.discount_price = None
        super().save(*args, **kwargs)
        if not self.sku:
            self.sku = f"MRN-{self.pk:04d}"
            Product.objects.filter(pk=self.pk).update(sku=self.sku)

    def get_absolute_url(self):
        return reverse("shop:product", args=[self.pk, self.slug])

    @property
    def final_price(self):
        return self.discount_price or self.price

    @property
    def discount_percent(self):
        if self.discount_price:
            return round(100 - (self.discount_price * 100 / self.price))
        return 0

    @property
    def has_variants(self):
        return len(self.variants.all()) > 0

    @property
    def total_stock(self):
        if self.has_variants:
            return sum(v.stock for v in self.variants.all())
        return self.stock

    @property
    def in_stock(self):
        return self.total_stock > 0

    @property
    def is_new(self):
        from django.utils import timezone

        return (timezone.now() - self.created_at).days <= 14

    def sizes(self):
        return list(dict.fromkeys(v.size for v in self.variants.all() if v.size))

    def colors(self):
        seen, out = set(), []
        for v in self.variants.all():
            if v.color and v.color not in seen:
                seen.add(v.color)
                out.append((v.color, v.color_hex))
        return out


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("تصویر", upload_to="products/gallery/")
    alt = models.CharField("متن جایگزین", max_length=150, blank=True)
    order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "تصویر محصول"
        verbose_name_plural = "گالری تصاویر"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField("سایز", max_length=30, blank=True)
    color = models.CharField("رنگ", max_length=40, blank=True)
    color_hex = models.CharField("کد رنگ", max_length=7, blank=True, default="#000000")
    stock = models.PositiveIntegerField("موجودی", default=0)
    extra_price = models.IntegerField("اختلاف قیمت (تومان)", default=0)

    class Meta:
        ordering = ["id"]
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع‌ها (سایز / رنگ)"

    def __str__(self):
        return self.label or "پیش‌فرض"

    @property
    def label(self):
        parts = []
        if self.color:
            parts.append(f"رنگ: {self.color}")
        if self.size:
            parts.append(f"سایز: {self.size}")
        return " | ".join(parts)


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wished_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]
        verbose_name = "علاقه‌مندی"
        verbose_name_plural = "علاقه‌مندی‌ها"
