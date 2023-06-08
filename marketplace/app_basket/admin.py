# -*- coding: utf8 -*-

from django.contrib import admin

from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Регистрация модели корзины в админ панели"""

    search_fields = ["buyer"]
    list_display = ["buyer"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Регистрация модели товара в корзине в админ панели"""

    search_fields = ["offer", "cart"]
    list_display = ["offer", "cart", "quantity"]
