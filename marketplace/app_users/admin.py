from django.contrib import admin

from .models import (Buyer, DeliveryType, Order, OrderItem, Payment,
                     PaymentType, Profile, Seller)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "full_name",
    ]
    search_fields = [
        "full_name",
    ]


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
    ]
    search_fields = [
        "title",
    ]


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ["profile"]
    search_fields = ["profile"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["buyer", "order_date"]
    search_fields = ["buyer"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "offer", "quantity"]
    search_fields = ["order"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["buyer", "payment_type"]
    search_fields = ["buyer"]


@admin.register(DeliveryType)
class DeliveryTypeAdmin(admin.ModelAdmin):
    list_display = ["type"]
    search_fields = ["type"]


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ["pk", "title"]
    list_filter = ["is_active"]
