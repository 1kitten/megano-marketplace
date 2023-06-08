from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django_mptt_admin.admin import DjangoMpttAdmin

from .models import (Banner, Category, Discount, Image, Offer, Product,
                     SetOfProducts, ProductGroup, Tag, SetDiscount, CartDiscount)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """Регистрация модели картинок в админ панели."""

    search_fields = ["title"]
    list_display = ["file", "title"]


@admin.register(Category)
class CategoryAdmin(DjangoMpttAdmin):
    """Регистрация модели категорий в админ панели."""

    prepopulated_fields = {"slug": ("title",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = [
        "title",
    ]
    list_display = [
        "title",
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = [
        "title",
    ]
    list_display = [
        "title",
        "category",
    ]


@admin.register(SetOfProducts)
class SetOfProductsAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]
    list_display = [
        "name", 'product_group'
    ]

@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
    ]
    list_display = [
        "name",
    ]


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    search_fields = [
        "seller",
        "product",
    ]
    list_display = [
        "seller",
        "product",
        "quantity",
        "price",
        "is_active",
    ]
    list_filter = [
        "is_active",
    ]


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ["id", "product",  "start_date", "end_date", "short_description"]
    list_filter = [
        "end_date",
    ]

    def short_description(self, obj):
        if len(obj.description) > 20:
            return f"{obj.description[:20]}..."
        return obj.description


@admin.register(SetDiscount)
class SetDiscountAdmin(admin.ModelAdmin):
    list_display = ["id", "set_of_products", 'size', "is_percent", 'start_date', "end_date", "is_active" ]
    list_filter = ["is_active"]

@admin.register(CartDiscount)
class CartDiscountAdmin(admin.ModelAdmin):
    list_display = ["id", "cart", 'min_order_sum', "min_quantity", "is_percent", "discount", 'start_date', "end_date", "description", "is_active" ]
    list_filter = ["is_active"]


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Регистрация модели баннера в админ-панели."""

    list_display = ["title", "primary_text", "short_description", "is_active", "link"]
    list_filter = ["is_active"]
    search_fields = ["title", "description"]

    def short_description(self, obj):
        return truncatechars(obj.description, 50)
