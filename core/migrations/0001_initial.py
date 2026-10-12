from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120, verbose_name='عنوان')),
                ('subtitle', models.CharField(blank=True, max_length=250, verbose_name='زیرعنوان')),
                ('image', models.ImageField(blank=True, upload_to='banners/', verbose_name='تصویر')),
                ('button_text', models.CharField(blank=True, default='مشاهده', max_length=40, verbose_name='متن دکمه')),
                ('link', models.CharField(blank=True, default='/shop/', max_length=250, verbose_name='لینک')),
                ('theme', models.CharField(choices=[('sand', 'شنی'), ('dark', 'تیره'), ('rose', 'رز'), ('olive', 'زیتونی'), ('sky', 'آسمانی')], default='sand', max_length=20, verbose_name='رنگ زمینه')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ترتیب')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
            ],
            options={
                'verbose_name': 'بنر',
                'verbose_name_plural': 'بنرها',
                'ordering': ['order', '-id'],
            },
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='نام')),
                ('phone', models.CharField(max_length=50, verbose_name='تماس')),
                ('subject', models.CharField(blank=True, max_length=150, verbose_name='موضوع')),
                ('message', models.TextField(verbose_name='پیام')),
                ('is_read', models.BooleanField(default=False, verbose_name='خوانده شده')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'پیام تماس',
                'verbose_name_plural': 'پیام\u200cهای تماس',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SiteSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(default='میرانا', max_length=100, verbose_name='نام سایت')),
                ('site_name_en', models.CharField(default='MIRANA', max_length=100, verbose_name='نام لاتین')),
                ('slogan', models.CharField(default='پوشاک و اکسسوری با امضای میرانا', max_length=200, verbose_name='شعار')),
                ('announcement', models.CharField(blank=True, default='ارسال رایگان برای سفارش\u200cهای بالای ۲ میلیون تومان 🚚', max_length=250, verbose_name='نوار اعلان بالای سایت')),
                ('telegram_id', models.CharField(default='mirana_admin', max_length=100, verbose_name='آیدی تلگرام ادمین (بدون @)')),
                ('rubika_id', models.CharField(default='mirana_admin', max_length=100, verbose_name='آیدی روبیکا ادمین (بدون @)')),
                ('telegram_channel', models.CharField(blank=True, default='mirana_shop', max_length=100, verbose_name='آیدی کانال تلگرام')),
                ('rubika_channel', models.CharField(blank=True, default='mirana_shop', max_length=100, verbose_name='آیدی کانال روبیکا')),
                ('instagram_id', models.CharField(blank=True, max_length=100, verbose_name='آیدی اینستاگرام')),
                ('phone', models.CharField(blank=True, default='۰۹۱۲۰۰۰۰۰۰۰', max_length=50, verbose_name='تلفن پشتیبانی')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='ایمیل')),
                ('address', models.CharField(blank=True, default='تهران', max_length=300, verbose_name='آدرس فروشگاه')),
                ('working_hours', models.CharField(blank=True, default='همه\u200cروزه ۱۰ تا ۲۲', max_length=120, verbose_name='ساعت پاسخگویی')),
                ('card_number', models.CharField(blank=True, default='6037-0000-0000-0000', max_length=30, verbose_name='شماره کارت')),
                ('card_holder', models.CharField(blank=True, default='میرانا', max_length=100, verbose_name='به نام')),
                ('sheba', models.CharField(blank=True, max_length=40, verbose_name='شماره شبا')),
                ('shipping_cost', models.PositiveIntegerField(default=70000, verbose_name='هزینه ارسال (تومان)')),
                ('free_shipping_over', models.PositiveIntegerField(default=2000000, verbose_name='ارسال رایگان برای خرید بالای (تومان) - صفر یعنی غیرفعال')),
                ('order_hold_hours', models.PositiveIntegerField(default=24, verbose_name='مهلت ارسال رسید پرداخت (ساعت)')),
                ('about', models.TextField(default='میرانا یک برند پوشاک ایرانی است که با تکیه بر طراحی مینیمال، پارچه\u200cهای باکیفیت و دوخت دقیق، لباس و اکسسوری روزمره را برای سبک زندگی امروز می\u200cسازد.', verbose_name='درباره ما')),
                ('footer_text', models.CharField(blank=True, default='تمامی حقوق برای برند میرانا محفوظ است.', max_length=300, verbose_name='متن فوتر')),
            ],
            options={
                'verbose_name': 'تنظیمات سایت',
                'verbose_name_plural': 'تنظیمات سایت',
            },
        ),
    ]
