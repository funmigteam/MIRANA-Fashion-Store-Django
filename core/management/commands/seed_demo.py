import io
import math
import random

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core.models import Banner, SiteSetting
from orders.models import Coupon
from shop.models import Category, Product, ProductImage, ProductVariant

PALETTES = [
    ("#efe4d6", "#d9c3a7", "#7c4b2a"), ("#e8ebe0", "#c5cbb0", "#4d5338"), ("#f4e1de", "#e2b8b1", "#8a3f37"),
    ("#e2eaf1", "#bccfdf", "#2d4d6b"), ("#ece8f3", "#cfc4e3", "#4b3a78"), ("#f2ece4", "#ddd2c3", "#2a2420"),
]


def _shape(d, kind, cx, cy, s, fill):
    if kind == "tshirt":
        d.polygon([(cx-0.55*s, cy-0.55*s), (cx-0.2*s, cy-0.7*s), (cx-0.1*s, cy-0.6*s), (cx+0.1*s, cy-0.6*s), (cx+0.2*s, cy-0.7*s),
                   (cx+0.55*s, cy-0.55*s), (cx+0.75*s, cy-0.2*s), (cx+0.45*s, cy-0.08*s), (cx+0.42*s, cy+0.75*s),
                   (cx-0.42*s, cy+0.75*s), (cx-0.45*s, cy-0.08*s), (cx-0.75*s, cy-0.2*s)], fill=fill)
    elif kind == "coat":
        d.polygon([(cx-0.5*s, cy-0.7*s), (cx-0.12*s, cy-0.78*s), (cx, cy-0.3*s), (cx+0.12*s, cy-0.78*s), (cx+0.5*s, cy-0.7*s),
                   (cx+0.72*s, cy+0.6*s), (cx+0.5*s, cy+0.62*s), (cx+0.48*s, cy+0.95*s), (cx-0.48*s, cy+0.95*s),
                   (cx-0.5*s, cy+0.62*s), (cx-0.72*s, cy+0.6*s)], fill=fill)
        d.line([(cx, cy-0.3*s), (cx, cy+0.95*s)], fill=(255, 255, 255, 90), width=4)
    elif kind == "pants":
        d.polygon([(cx-0.4*s, cy-0.8*s), (cx+0.4*s, cy-0.8*s), (cx+0.48*s, cy+0.95*s), (cx+0.1*s, cy+0.95*s),
                   (cx, cy-0.2*s), (cx-0.1*s, cy+0.95*s), (cx-0.48*s, cy+0.95*s)], fill=fill)
    elif kind == "dress":
        d.polygon([(cx-0.2*s, cy-0.8*s), (cx+0.2*s, cy-0.8*s), (cx+0.28*s, cy-0.2*s), (cx+0.7*s, cy+0.9*s),
                   (cx-0.7*s, cy+0.9*s), (cx-0.28*s, cy-0.2*s)], fill=fill)
    elif kind == "bag":
        d.rounded_rectangle([cx-0.6*s, cy-0.25*s, cx+0.6*s, cy+0.7*s], radius=int(0.12*s), fill=fill)
        d.arc([cx-0.35*s, cy-0.75*s, cx+0.35*s, cy+0.05*s], 180, 360, fill=fill, width=int(0.09*s))
    elif kind == "hat":
        d.ellipse([cx-0.85*s, cy+0.1*s, cx+0.85*s, cy+0.45*s], fill=fill)
        d.chord([cx-0.48*s, cy-0.6*s, cx+0.48*s, cy+0.6*s], 180, 360, fill=fill)
    elif kind == "scarf":
        d.polygon([(cx-0.7*s, cy-0.6*s), (cx+0.7*s, cy-0.6*s), (cx, cy+0.9*s)], fill=fill)
    elif kind == "shoe":
        d.polygon([(cx-0.8*s, cy+0.35*s), (cx-0.75*s, cy-0.3*s), (cx-0.35*s, cy-0.3*s), (cx-0.1*s, cy),
                   (cx+0.6*s, cy+0.12*s), (cx+0.85*s, cy+0.35*s)], fill=fill)
        d.rectangle([cx-0.8*s, cy+0.35*s, cx+0.85*s, cy+0.48*s], fill=(255, 255, 255, 200))
    elif kind == "watch":
        d.rounded_rectangle([cx-0.18*s, cy-0.9*s, cx+0.18*s, cy+0.9*s], radius=int(0.08*s), fill=fill)
        d.ellipse([cx-0.38*s, cy-0.38*s, cx+0.38*s, cy+0.38*s], fill=fill)
        d.ellipse([cx-0.3*s, cy-0.3*s, cx+0.3*s, cy+0.3*s], fill=(255, 255, 255, 230))
        d.line([(cx, cy), (cx, cy-0.2*s)], fill=fill, width=5)
        d.line([(cx, cy), (cx+0.14*s, cy)], fill=fill, width=5)
    elif kind == "glasses":
        for dx in (-0.42, 0.42):
            d.ellipse([cx+(dx-0.32)*s, cy-0.25*s, cx+(dx+0.32)*s, cy+0.25*s], outline=fill, width=int(0.07*s))
        d.arc([cx-0.15*s, cy-0.15*s, cx+0.15*s, cy+0.1*s], 200, 340, fill=fill, width=int(0.05*s))
    elif kind == "jewel":
        d.arc([cx-0.6*s, cy-0.8*s, cx+0.6*s, cy+0.4*s], 0, 180, fill=fill, width=6)
        d.polygon([(cx, cy+0.4*s), (cx-0.18*s, cy+0.62*s), (cx, cy+0.9*s), (cx+0.18*s, cy+0.62*s)], fill=fill)
    else:
        d.rounded_rectangle([cx-0.9*s, cy-0.12*s, cx+0.9*s, cy+0.12*s], radius=10, fill=fill)
        d.rectangle([cx-0.2*s, cy-0.22*s, cx+0.2*s, cy+0.22*s], outline=(255, 255, 255, 220), width=6)


def make_image(kind, palette_i, color=None, w=800, h=1000, variant=0):
    bg1, bg2, ink = PALETTES[palette_i % len(PALETTES)]
    img = Image.new("RGB", (w, h), bg1)
    d = ImageDraw.Draw(img)
    top, bot = Image.new("RGB", (1, 1), bg1).getpixel((0, 0)), Image.new("RGB", (1, 1), bg2).getpixel((0, 0))
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    r = 330 if variant == 0 else 260
    d.ellipse([w/2 - r, h/2 - r - 40, w/2 + r, h/2 + r - 40], fill=tuple(min(255, c + 14) for c in top))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([w/2 - 230, h - 230, w/2 + 230, h - 190], fill=(0, 0, 0, 55))
    img.paste(sh.filter(ImageFilter.GaussianBlur(18)), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    fill = color or ink
    if isinstance(fill, str):
        fill = tuple(int(fill.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    s = 300 if variant == 0 else 250
    _shape(ld, kind, w/2, h/2 - 30 + (variant * 30), s, fill)
    img.paste(layer, (0, 0), layer)
    try:
        font = ImageFont.truetype("Helvetica", 30)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(img)
    text = "M I R A N A"
    tw = d.textlength(text, font=font)
    d.text(((w - tw) / 2, h - 90), text, fill=ink, font=font)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=86)
    return ContentFile(buf.getvalue())


CATEGORIES = [
    ("پوشاک زنانه", "مانتو، پیراهن و شلوار زنانه", ["مانتو", "پیراهن و بلوز", "شلوار زنانه"]),
    ("پوشاک مردانه", "تی‌شرت، پیراهن و شلوار مردانه", ["تی‌شرت و پولو", "پیراهن مردانه", "شلوار مردانه"]),
    ("کیف و کفش", "کیف دستی، کوله و کفش", ["کیف", "کفش"]),
    ("اکسسوری", "شال، کلاه، کمربند، عینک و ساعت", ["شال و روسری", "کلاه", "کمربند", "عینک", "ساعت"]),
    ("زیورآلات", "گردنبند، دستبند و گوشواره", []),
]

COLORS = [("مشکی", "#1c1c1c"), ("کرم", "#e6d8c3"), ("سرمه‌ای", "#1f2a44"), ("زیتونی", "#6b7151"),
          ("قهوه‌ای", "#7c4b2a"), ("طوسی", "#8d8d8d"), ("سفید", "#f5f5f5"), ("رز", "#c98b84")]

PRODUCTS = [
    ("مانتو کتان بلند آیلین", "مانتو", "coat", "women", 1890000, "S M L XL", 3, "کتان ۱۰۰٪"),
    ("مانتو کرپ جلوباز نیلا", "مانتو", "coat", "women", 1650000, "S M L XL", 2, "کرپ مازراتی"),
    ("پیراهن لینن ساحلی", "پیراهن و بلوز", "dress", "women", 1250000, "S M L", 3, "لینن"),
    ("بلوز ساتن یقه‌دار رها", "پیراهن و بلوز", "tshirt", "women", 890000, "S M L XL", 3, "ساتن ابریشم"),
    ("شلوار پالازو مازراتی", "شلوار زنانه", "pants", "women", 980000, "36 38 40 42", 3, "مازراتی"),
    ("شلوار جین مام استایل", "شلوار زنانه", "pants", "women", 1150000, "36 38 40 42 44", 2, "جین کش"),
    ("تی‌شرت اورسایز پنبه‌ای", "تی‌شرت و پولو", "tshirt", "men", 490000, "M L XL XXL", 4, "پنبه ۱۰۰٪ ترک"),
    ("پولوشرت پیکه کلاسیک", "تی‌شرت و پولو", "tshirt", "men", 690000, "M L XL", 3, "پیکه"),
    ("پیراهن آکسفورد آستین بلند", "پیراهن مردانه", "tshirt", "men", 1090000, "M L XL XXL", 3, "آکسفورد"),
    ("شلوار کتان اسلش", "شلوار مردانه", "pants", "men", 1190000, "30 32 34 36", 3, "کتان کش"),
    ("کاپشن پافر سبک", "پوشاک مردانه", "coat", "unisex", 2850000, "M L XL", 2, "پلی‌استر ضدآب"),
    ("کیف دوشی چرم مینیمال", "کیف", "bag", "women", 1450000, "", 3, "چرم طبیعی"),
    ("کوله پشتی روزمره", "کیف", "bag", "unisex", 1290000, "", 2, "کتان واکس‌خورده"),
    ("کفش اسنیکر سفید", "کفش", "shoe", "unisex", 1750000, "38 39 40 41 42 43 44", 2, "چرم مصنوعی"),
    ("کفش لوفر چرم", "کفش", "shoe", "men", 1980000, "40 41 42 43 44", 2, "چرم طبیعی"),
    ("شال نخی ساده", "شال و روسری", "scarf", "women", 390000, "", 5, "نخ"),
    ("روسری ابریشم طرح‌دار", "شال و روسری", "scarf", "women", 690000, "", 3, "ابریشم"),
    ("کلاه بیسبال کتان", "کلاه", "hat", "unisex", 320000, "", 4, "کتان"),
    ("کلاه بافت زمستانی", "کلاه", "hat", "unisex", 280000, "", 3, "اکریلیک"),
    ("کمربند چرم کلاسیک", "کمربند", "belt", "men", 450000, "", 2, "چرم طبیعی"),
    ("عینک آفتابی گربه‌ای", "عینک", "glasses", "women", 790000, "", 2, "استات"),
    ("ساعت مچی مینیمال", "ساعت", "watch", "unisex", 2350000, "", 2, "استیل ضدزنگ"),
    ("گردنبند استیل طلایی", "زیورآلات", "jewel", "women", 420000, "", 1, "استیل با روکش طلا"),
    ("دستبند چرم بافت", "زیورآلات", "jewel", "unisex", 260000, "", 2, "چرم"),
]


class Command(BaseCommand):
    help = "ساخت داده نمونه (دسته‌ها، محصولات، اسلایدر، کد تخفیف و کاربر ادمین)"

    def add_arguments(self, parser):
        parser.add_argument("--admin-user", default="admin")
        parser.add_argument("--admin-pass", default="admin1234")
        parser.add_argument("--no-products", action="store_true")

    def handle(self, *args, **opts):
        random.seed(7)
        SiteSetting.load()

        u, created = User.objects.get_or_create(username=opts["admin_user"], defaults={"first_name": "مدیر", "last_name": "میرانا"})
        if created:
            u.set_password(opts["admin_pass"])
        u.is_staff = u.is_superuser = True
        u.save()
        self.stdout.write(self.style.SUCCESS(f"ادمین: {opts['admin_user']} / " + (opts["admin_pass"] if created else "(رمز قبلی)")))

        cat_map = {}
        for i, (name, desc, subs) in enumerate(CATEGORIES):
            c, _ = Category.objects.get_or_create(name=name, parent=None, defaults={"description": desc, "order": i})
            if not c.image:
                kind = {"پوشاک زنانه": "dress", "پوشاک مردانه": "tshirt", "کیف و کفش": "bag", "اکسسوری": "hat"}.get(name, "jewel")
                c.image.save(f"cat-{i}.jpg", make_image(kind, i, w=600, h=800), save=True)
            cat_map[name] = c
            for j, sname in enumerate(subs):
                sc, _ = Category.objects.get_or_create(name=sname, parent=c, defaults={"order": j})
                cat_map[sname] = sc

        if not Banner.objects.exists():
            Banner.objects.create(title="کالکشن پاییزه میرانا", subtitle="لایه‌های گرم، رنگ‌های خاکی و دوخت دقیق؛ برای روزهای خنک پاییز.", button_text="خرید کالکشن", link="/shop/", theme="sand", order=0)
            Banner.objects.create(title="تا ۳۰٪ تخفیف ویژه", subtitle="فرصت محدود برای منتخبی از پرفروش‌ترین محصولات میرانا.", button_text="مشاهده تخفیف‌ها", link="/shop/?sale=1", theme="dark", order=1)
            Banner.objects.create(title="اکسسوری، امضای استایل شما", subtitle="شال، کلاه، کیف و زیورآلات برای تکمیل هر استایل.", button_text="مشاهده اکسسوری", link="/category/اکسسوری/", theme="rose", order=2)

        Coupon.objects.get_or_create(code="MIRANA10", defaults={"percent": 10, "max_discount": 300000})
        Coupon.objects.get_or_create(code="WELCOME", defaults={"amount": 100000, "min_total": 800000})

        if opts["no_products"] or Product.objects.exists():
            self.stdout.write("محصولات قبلاً ساخته شده‌اند؛ رد شد.")
            return

        for idx, (name, cat, kind, gender, price, sizes, ncolors, material) in enumerate(PRODUCTS):
            colors = random.sample(COLORS, ncolors)
            discount = None
            if idx % 4 == 1:
                discount = int(price * random.choice([0.7, 0.8, 0.85]) / 10000) * 10000
            p = Product(
                name=name, category=cat_map[cat], gender=gender, price=price, discount_price=discount,
                short_description=f"{name} از کالکشن جدید میرانا؛ طراحی مینیمال با کیفیت دوخت عالی.",
                description=(
                    f"{name} یکی از محصولات محبوب برند میراناست.\n\n"
                    "• طراحی مینیمال و قابل ست با استایل‌های مختلف\n• دوخت دقیق و تمیز\n"
                    f"• جنس: {material}\n• تولید ایران با کنترل کیفیت میرانا"
                ),
                material=material, care="شستشو با آب سرد، اتو با حرارت ملایم، از سفیدکننده استفاده نشود.",
                is_featured=idx % 3 == 0, stock=0 if (sizes or ncolors > 1) else random.randint(4, 20),
            )
            p.image.save(f"p{idx}.jpg", make_image(kind, idx, colors[0][1]), save=False)
            p.save()
            for g in range(1, min(3, len(colors) + 1)):
                c = colors[g] if g < len(colors) else colors[0]
                ProductImage.objects.create(product=p, order=g, image=ContentFile(make_image(kind, idx + g, c[1], variant=1).read(), name=f"p{idx}-{g}.jpg"))
            size_list = sizes.split() if sizes else [""]
            if sizes or ncolors > 1:
                for cname, chex in colors:
                    for s in size_list:
                        ProductVariant.objects.create(product=p, color=cname, color_hex=chex, size=s, stock=random.choice([0, 2, 4, 6, 8, 10, 12]))
            Product.objects.filter(pk=p.pk).update(
                created_at=timezone.now() - timezone.timedelta(days=idx * 2),
                views=random.randint(20, 900), sold=random.randint(0, 60),
            )
        self.stdout.write(self.style.SUCCESS(f"{len(PRODUCTS)} محصول نمونه ساخته شد ✓"))
