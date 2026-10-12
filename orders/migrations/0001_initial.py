import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shop', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True, verbose_name='کد تخفیف')),
                ('percent', models.PositiveIntegerField(default=0, verbose_name='درصد تخفیف')),
                ('amount', models.PositiveIntegerField(default=0, verbose_name='مبلغ ثابت تخفیف (تومان)')),
                ('max_discount', models.PositiveIntegerField(default=0, verbose_name='سقف تخفیف (تومان) - صفر یعنی بدون سقف')),
                ('min_total', models.PositiveIntegerField(default=0, verbose_name='حداقل مبلغ سفارش (تومان)')),
                ('usage_limit', models.PositiveIntegerField(default=0, verbose_name='سقف دفعات استفاده - صفر یعنی نامحدود')),
                ('used', models.PositiveIntegerField(default=0, verbose_name='دفعات استفاده\u200cشده')),
                ('valid_until', models.DateTimeField(blank=True, null=True, verbose_name='معتبر تا')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'کد تخفیف',
                'verbose_name_plural': 'کدهای تخفیف',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(editable=False, max_length=12, unique=True, verbose_name='کد سفارش')),
                ('status', models.CharField(choices=[('pending', 'پیش\u200cسفارش - در انتظار پرداخت'), ('paid', 'پرداخت تایید شد'), ('preparing', 'در حال آماده\u200cسازی'), ('shipped', 'ارسال شد'), ('delivered', 'تحویل داده شد'), ('cancelled', 'لغو شده')], db_index=True, default='pending', max_length=12, verbose_name='وضعیت')),
                ('full_name', models.CharField(max_length=120, verbose_name='نام و نام خانوادگی گیرنده')),
                ('phone', models.CharField(max_length=15, verbose_name='موبایل گیرنده')),
                ('province', models.CharField(max_length=50, verbose_name='استان')),
                ('city', models.CharField(max_length=50, verbose_name='شهر')),
                ('address', models.TextField(verbose_name='آدرس کامل')),
                ('postal_code', models.CharField(max_length=10, verbose_name='کد پستی')),
                ('note', models.TextField(blank=True, verbose_name='توضیحات سفارش')),
                ('shipping_method', models.CharField(choices=[('post', 'پست پیشتاز'), ('tipax', 'تیپاکس'), ('courier', 'پیک (فقط تهران)')], default='post', max_length=10, verbose_name='روش ارسال')),
                ('subtotal', models.PositiveIntegerField(default=0, verbose_name='جمع اقلام')),
                ('discount', models.PositiveIntegerField(default=0, verbose_name='تخفیف')),
                ('shipping_cost', models.PositiveIntegerField(default=0, verbose_name='هزینه ارسال')),
                ('total', models.PositiveIntegerField(default=0, verbose_name='مبلغ قابل پرداخت')),
                ('receipt', models.ImageField(blank=True, upload_to='receipts/', verbose_name='تصویر رسید پرداخت')),
                ('tracking_code', models.CharField(blank=True, max_length=60, verbose_name='کد رهگیری مرسوله')),
                ('admin_note', models.TextField(blank=True, verbose_name='یادداشت ادمین (برای مشتری نمایش داده می\u200cشود)')),
                ('private_note', models.TextField(blank=True, verbose_name='یادداشت داخلی (فقط ادمین)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='آخرین تغییر')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ تایید پرداخت')),
                ('shipped_at', models.DateTimeField(blank=True, null=True, verbose_name='تاریخ ارسال')),
                ('coupon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.coupon', verbose_name='کد تخفیف')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'سفارش',
                'verbose_name_plural': 'سفارش\u200cها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200, verbose_name='نام محصول')),
                ('variant_label', models.CharField(blank=True, max_length=120, verbose_name='مشخصات')),
                ('unit_price', models.PositiveIntegerField(verbose_name='قیمت واحد')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='تعداد')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.product')),
                ('variant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.productvariant')),
            ],
            options={
                'verbose_name': 'قلم سفارش',
                'verbose_name_plural': 'اقلام سفارش',
            },
        ),
        migrations.CreateModel(
            name='OrderStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'پیش\u200cسفارش - در انتظار پرداخت'), ('paid', 'پرداخت تایید شد'), ('preparing', 'در حال آماده\u200cسازی'), ('shipped', 'ارسال شد'), ('delivered', 'تحویل داده شد'), ('cancelled', 'لغو شده')], max_length=12)),
                ('note', models.CharField(blank=True, max_length=250)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='orders.order')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
