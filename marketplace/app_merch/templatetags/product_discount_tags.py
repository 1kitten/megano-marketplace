from django import template

from app_merch.discount_service import DiscountService
from app_merch.models import Offer, Discount

register = template.Library()
discount_service = DiscountService()


@register.simple_tag(name='avg_discount_price')
def get_avg_discount_price_of_product(product_id: int) -> float:
    """ Получение средней цены на конкретный товар."""

    offers = Offer.objects.filter(product=product_id).all()
    with_discount, without_discount = discount_service.get_offers_with_and_without_discount(
        offers=offers
    )
    avg_discount_price = discount_service.calculate_average_with_discount(
        offers_with_discount=with_discount, offers_without_discount=without_discount
    )
    return round(avg_discount_price, 2)


@register.simple_tag(name='avg_price')
def get_avg_price_of_product(product_id: int) -> float:
    """ Получение средней цены на товары без учёта скидки. """

    offers = Offer.objects.filter(product=product_id).all()
    return round(discount_service.calculate_average_price(offers=offers), 2)


@register.simple_tag(name='is_discounted')
def product_for_active_discount(product_id: int) -> bool:
    """ Проверка продукта на наличие активной скидки. """

    discounts = Discount.objects.filter(is_active=True, product_id=product_id, size__gt=0)
    return True if discounts else False
