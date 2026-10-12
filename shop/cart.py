from django.conf import settings


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(settings.CART_SESSION_KEY) or {}

    def _save(self):
        self.session[settings.CART_SESSION_KEY] = self.data
        self.session.modified = True

    @staticmethod
    def key(product_id, variant_id=None):
        return f"{product_id}:{variant_id or 0}"

    def add(self, product, variant=None, qty=1, replace=False):
        k = self.key(product.pk, variant.pk if variant else None)
        current = 0 if replace else self.data.get(k, {}).get("qty", 0)
        stock = variant.stock if variant else product.stock
        new_qty = max(0, min(current + qty, stock))
        if new_qty <= 0:
            self.data.pop(k, None)
        else:
            self.data[k] = {"qty": new_qty}
        self._save()
        return new_qty

    def remove(self, k):
        self.data.pop(k, None)
        self._save()

    def clear(self):
        self.data = {}
        self.session.pop(settings.CART_SESSION_KEY, None)
        self.session.pop("coupon_code", None)
        self.session.modified = True

    def count(self):
        return sum(v.get("qty", 0) for v in self.data.values())

    def items(self):
        from .models import Product, ProductVariant

        out, dirty = [], False
        pids = {int(k.split(":")[0]) for k in self.data}
        vids = {int(k.split(":")[1]) for k in self.data} - {0}
        products = Product.objects.filter(pk__in=pids, is_active=True).in_bulk()
        variants = ProductVariant.objects.filter(pk__in=vids).in_bulk()
        for k, v in list(self.data.items()):
            pid, vid = (int(x) for x in k.split(":"))
            product = products.get(pid)
            variant = variants.get(vid) if vid else None
            if not product or (vid and (not variant or variant.product_id != pid)):
                self.data.pop(k)
                dirty = True
                continue
            stock = variant.stock if variant else product.stock
            qty = min(v["qty"], stock)
            if qty <= 0:
                self.data.pop(k)
                dirty = True
                continue
            if qty != v["qty"]:
                self.data[k]["qty"] = qty
                dirty = True
            unit = product.final_price + (variant.extra_price if variant else 0)
            out.append({
                "key": k, "product": product, "variant": variant, "qty": qty,
                "unit_price": unit, "total": unit * qty, "stock": stock,
            })
        if dirty:
            self._save()
        return out

    def subtotal(self, items=None):
        items = items if items is not None else self.items()
        return sum(i["total"] for i in items)
