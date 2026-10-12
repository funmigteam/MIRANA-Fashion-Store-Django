import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='نام')),
                ('slug', models.SlugField(allow_unicode=True, blank=True, max_length=120, unique=True, verbose_name='اسلاگ')),
                ('description', models.CharField(blank=True, max_length=250, verbose_name='توضیح کوتاه')),
                ('image', models.ImageField(blank=True, upload_to='categories/', verbose_name='تصویر')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ترتیب')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='shop.category', verbose_name='دسته والد')),
            ],
            options={
                'verbose_name': 'دسته\u200cبندی',
                'verbose_name_plural': 'دسته\u200cبندی\u200cها',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='نام محصول')),
                ('slug', models.SlugField(allow_unicode=True, blank=True, max_length=220, unique=True, verbose_name='اسلاگ')),
                ('sku', models.CharField(blank=True, max_length=40, verbose_name='کد محصول')),
                ('gender', models.CharField(choices=[('unisex', 'همه'), ('women', 'زنانه'), ('men', 'مردانه'), ('kids', 'بچگانه')], default='unisex', max_length=10, verbose_name='مناسب برای')),
                ('short_description', models.CharField(blank=True, max_length=300, verbose_name='توضیح کوتاه')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات کامل')),
                ('material', models.CharField(blank=True, max_length=150, verbose_name='جنس')),
                ('care', models.CharField(blank=True, max_length=250, verbose_name='نحوه نگهداری')),
                ('price', models.PositiveIntegerField(verbose_name='قیمت (تومان)')),
                ('discount_price', models.PositiveIntegerField(blank=True, null=True, verbose_name='قیمت با تخفیف (تومان)')),
                ('stock', models.PositiveIntegerField(default=0, help_text='اگر محصول سایز/رنگ دارد، موجودی هر تنوع جداگانه ثبت می\u200cشود.', verbose_name='موجودی (برای محصولات بدون تنوع)')),
                ('image', models.ImageField(blank=True, upload_to='products/', verbose_name='تصویر اصلی')),
                ('is_active', models.BooleanField(default=True, verbose_name='نمایش در سایت')),
                ('is_featured', models.BooleanField(default=False, verbose_name='محصول ویژه')),
                ('views', models.PositiveIntegerField(default=0, verbose_name='بازدید')),
                ('sold', models.PositiveIntegerField(default=0, verbose_name='تعداد فروش')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='shop.category', verbose_name='دسته\u200cبندی')),
            ],
            options={
                'verbose_name': 'محصول',
                'verbose_name_plural': 'محصولات',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/gallery/', verbose_name='تصویر')),
                ('alt', models.CharField(blank=True, max_length=150, verbose_name='متن جایگزین')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ترتیب')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='shop.product')),
            ],
            options={
                'verbose_name': 'تصویر محصول',
                'verbose_name_plural': 'گالری تصاویر',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.CharField(blank=True, max_length=30, verbose_name='سایز')),
                ('color', models.CharField(blank=True, max_length=40, verbose_name='رنگ')),
                ('color_hex', models.CharField(blank=True, default='#000000', max_length=7, verbose_name='کد رنگ')),
                ('stock', models.PositiveIntegerField(default=0, verbose_name='موجودی')),
                ('extra_price', models.IntegerField(default=0, verbose_name='اختلاف قیمت (تومان)')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='shop.product')),
            ],
            options={
                'verbose_name': 'تنوع محصول',
                'verbose_name_plural': 'تنوع\u200cها (سایز / رنگ)',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wished_by', to='shop.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'علاقه\u200cمندی',
                'verbose_name_plural': 'علاقه\u200cمندی\u200cها',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'product')},
            },
        ),
    ]
