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
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=15, verbose_name='موبایل')),
                ('province', models.CharField(blank=True, max_length=50, verbose_name='استان')),
                ('city', models.CharField(blank=True, max_length=50, verbose_name='شهر')),
                ('address', models.TextField(blank=True, verbose_name='آدرس')),
                ('postal_code', models.CharField(blank=True, max_length=10, verbose_name='کد پستی')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'پروفایل',
                'verbose_name_plural': 'پروفایل\u200cها',
            },
        ),
    ]
