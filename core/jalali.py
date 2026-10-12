from datetime import date, datetime

from django.utils import timezone

MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]
WEEKDAYS = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def to_fa_digits(value):
    return str(value).translate(FA_DIGITS)


def to_en_digits(value):
    return str(value).translate(EN_DIGITS)


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100)
        + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    )
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def jalali(value, fmt="date"):
    if not value:
        return ""
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        d = value
    elif isinstance(value, date):
        d = value
    else:
        return value
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    if fmt == "long":
        out = f"{WEEKDAYS[d.weekday()]} {jd} {MONTHS[jm - 1]} {jy}"
    elif fmt == "short":
        out = f"{jd} {MONTHS[jm - 1]}"
    else:
        out = f"{jy}/{jm:02d}/{jd:02d}"
    if fmt in ("datetime", "long") and isinstance(d, datetime):
        out += f" - {d.hour:02d}:{d.minute:02d}"
    return to_fa_digits(out)
