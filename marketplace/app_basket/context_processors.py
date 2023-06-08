#!/usr/bin/env python
# -*- coding: utf8 -*-
from .cart import CartService
from app_merch.discount_service import DiscountService

def cart(request):
    """Контекст-процессор, инициализирующий сервис корзины товаров и делающий доступным его всем шаблонам"""

    if request.user.is_superuser:
        return {"cart": [], "price": 0}
    else:
        cart = CartService(request)
        ds = DiscountService()
        price = ds.get_total_price_cart(cart.cart)
        price2 = ds.get_total_price_cart_with_all_discounts(cart.cart)
        return {"cart": CartService(request), "price": price, "price_after_discount": price2}
