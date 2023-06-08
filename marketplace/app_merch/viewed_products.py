from datetime import datetime
from django.db.models import QuerySet
from django.utils.timezone import now
from .models import Product, WatchedProduct


class WatchedProductsService:
    products_amount = 20

    def add_product(self, request, product):
        if request.user.is_authenticated:
            watched_products = self.get_watched_products(user=request.user)
            if self.has_product(watched_products=watched_products, product=product):
                watched_product = watched_products.get(product=product)
                watched_product.view_date = now()
                watched_product.save()
            else:
                if (
                    self.count_watched_products(watched_products=watched_products)
                    == self.products_amount
                ):
                    self.remove_product(watched_products=watched_products)
                WatchedProduct.objects.create(user=request.user, product=product)
        else:
            if "watched_products" not in request.session:
                request.session["watched_products"] = {product.id: now().isoformat()}
            else:
                watched_products = request.session["watched_products"]
                if product.id in watched_products.keys():
                    watched_products[product.id] = now().isoformat()
                else:
                    if len(watched_products) == self.products_amount:
                        watched_products.pop(
                            min(watched_products, key=watched_products.get)
                        )
                    watched_products.update({product.id: now().isoformat()})

    @staticmethod
    def remove_product(watched_products):
        product = watched_products.last()
        product.delete()

    @staticmethod
    def has_product(watched_products, product) -> bool:
        return watched_products.filter(product=product).exists()

    @staticmethod
    def get_watched_products(user, count=None) -> QuerySet:
        queryset = WatchedProduct.objects.filter(user=user).order_by("-view_date")
        if count:
            queryset = queryset[:3]
        return queryset

    @staticmethod
    def count_watched_products(watched_products) -> int:
        return watched_products.count()

    @staticmethod
    def create_watched_products(request):
        for product_id, view_date in request.session["watched_products"]:
            product = Product.objects.get(id=product_id)
            WatchedProduct.objects.create(
                user=request.user, product=product, view_date=datetime.fromisoformat(view_date)
            )


watched_products_service = WatchedProductsService()
