from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("موبایل", max_length=15, blank=True)
    province = models.CharField("استان", max_length=50, blank=True)
    city = models.CharField("شهر", max_length=50, blank=True)
    address = models.TextField("آدرس", blank=True)
    postal_code = models.CharField("کد پستی", max_length=10, blank=True)

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
