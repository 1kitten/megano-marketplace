#!/usr/bin/env python
# -*- coding: utf8 -*-

from app_merch.models import Offer, Discount
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .cart import CartService
from app_merch.discount_service import DiscountService


def get_cart(request):
    """
    View получения корзины товаров юзера на странице сайта
    """
    cart_user = CartService(request)
    ds = DiscountService()
    # получаем список offers из корзины, каждый объект товара аннотирован полем с количеством этого товара в корзине и id этого товара в корзине
    offers = cart_user.get_cart_item_list()
    data_from_cart = ds.get_data_from_cart(offers)
    discount, total_price_after_cart_discount = ds.apply_cart_discount(cart_user.cart)
    discount_info, total_price_after_set_discount = ds.apply_set_discounts(cart_user.cart)

    if discount == 0 and not discount_info:
        return render(request, "cart.html", context={"cart_user": data_from_cart, "discount_cart": None, "discount": 0, "total_price": total_price_after_cart_discount})
    if total_price_after_cart_discount < total_price_after_set_discount:
        return render(request, "cart.html", context={"cart_user": data_from_cart, "discount_cart": True, "discount": discount, "total_price": total_price_after_cart_discount})
    else:
        return render(request, "cart.html", context={"cart_user": data_from_cart, "discount_cart": False, "discount": discount_info, "total_price": total_price_after_set_discount})



def add_to_cart(request):
    """
    View добавления товара в корзину
    """
    quantity = request.GET.get("amount", 1)
    offer_id = request.GET.get("offer_id")
    offer = Offer.objects.get(id=offer_id)
    cart_user = CartService(request)
    if (cart_user.cart.cart_item.filter(offer=offer).exists() and cart_user.cart.cart_item.filter(offer=offer).all()[0].quantity < offer.quantity
        or not cart_user.cart.cart_item.filter(offer=offer).exists()):
        cart_user.add_offer(offer=offer, quantity=quantity)
    return HttpResponseRedirect(redirect_to=request.META.get("HTTP_REFERER"))


def remove_from_cart(request):
    """
    View удаления товара из корзины
    """
    cartitem_id_delete = request.GET.get("cartitem_id")
    CartService(request).delete_cartitem(cartitem_id=cartitem_id_delete)
    request.session.pop('user_data', None)
    return HttpResponseRedirect(redirect_to=request.META.get('HTTP_REFERER'))

def change_cart(request):
    """
    View изменения количества товара из корзины
    """
    cartitem_id_change = request.POST.get('cartitem_id')
    quantity = request.POST.get('amount')
    CartService(request).change_quantity(cartitem_id=cartitem_id_change, quantity=quantity)
    return HttpResponseRedirect(redirect_to=request.META.get('HTTP_REFERER'))
