#!/usr/bin/env python
# -*- coding: utf8 -*-

from app_users.models import Buyer
from django.db import models



class Cart(models.Model):
    """
    Модель корзины покупок
    """

    buyer = models.ForeignKey(
        Buyer,
        null=True,
        on_delete=models.PROTECT,
        related_name="cart",
        verbose_name="покупатель",
    )

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        if self.buyer is not None:
            return f"Cart {self.buyer.profile.user.username}"
        else:
            return f"Cart anonymususer"

    def get_total_quantity(self):
        """
        Возвращает общее количество товаров в корзине.
        """
        return sum(item.quantity for item in self.cart_item.all())


class CartItem(models.Model):
    """
    Модель товара в корзине
    """

    offer = models.ForeignKey(
        "app_merch.Offer",
        on_delete=models.CASCADE,
        related_name="cart_item",
        verbose_name="предложение",
    )
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="cart_item", verbose_name="корзина"
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name="количество")

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"

    def __str__(self):
        if self.cart.buyer is None:
            return f"{self.offer.product.title} from Anonymous user"
        return (
            f"{self.offer.product.title} from {self.cart.buyer.profile.user.username}"
        )

    def get_total_price(self):
        """
        Возвращает общую стоимость данного товара в корзине.
        """
        return self.offer.price * self.quantity
