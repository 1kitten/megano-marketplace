from decimal import Decimal
from itertools import chain
from typing import List


from django.db.models import Avg, Count, Max, Q
from django.utils import timezone

from .models import Discount, Offer, Product, SetDiscount, SetOfProducts, ProductGroup
from django.db.models import F


class DiscountService:
    def calculate_average_price(self, offers):
        """
        Метод для расчета средней цены на основе списка предложений.
        """

        return offers.aggregate(Avg("price"))["price__avg"]

    def calculate_price_with_discount(self, offer, discount):
        """
        Метод для расчета цены с учетом скидки на основе предложения и скидки.
        """
        offer_price_with_discount = (
            offer.price * (1 - Decimal(discount.size) / 100)
            if discount.is_percent
            else offer.price - discount.size
        )
        return offer_price_with_discount

    def get_offers_with_and_without_discount(self, offers):
        """
        Метод для получения списка предложений со скидками и без скидок на основе списка предложений.
        """
        current_time = timezone.now()
        offers_with_discount, offers_without_discount = [], []
        for offer in offers:
            discounts = Discount.objects.filter(
                product=offer.product,
                is_active=True,
            )
            if discounts.exists():
                discount = discounts.first()
                offer_price_with_discount = self.calculate_price_with_discount(
                    offer, discount
                )
                offers_with_discount.append((offer, offer_price_with_discount))
            else:
                offers_without_discount.append((offer, offer.price))

        return offers_with_discount, offers_without_discount

    def calculate_average_with_discount(
        self, offers_with_discount, offers_without_discount
    ):
        """
        Метод для расчета средней цены с учетом скидок на основе списка предложений со скидками и без скидок.
        """
        total_price = 0
        count = 0
        for offer, price_with_discount in offers_with_discount:
            total_price += price_with_discount
            count += 1
        for offer, price in offers_without_discount:
            total_price += price
            count += 1
        return total_price / count if count >= 1 else total_price

    def calculate_price_difference(self, average_price, average_with_discount):
        """
        Метод для расчета разницы в цене между средней ценой и средней ценой с учетом скидок.
        """
        return average_price - average_with_discount

    def calculate_percentage_difference(self, price_difference, average_price):
        """
        Метод для расчета процентной разницы в цене между средней ценой и средней ценой с учетом скидок.
        """
        return (price_difference / average_price) * 100 if average_price != 0 else 0

    def combine_offers_with_discount_and_without_discount(
        self, offers_with_discount, offers_without_discount
    ):
        """
        Метод для объединения списка предложений со скидками и без скидок и их сортировки по цене с учетом скидок.
        """
        offers_combined = offers_with_discount + offers_without_discount
        return sorted(offers_combined, key=lambda x: x[1])


    def get_data_from_cart(self, offers_from_cart):
        """
        Получаем список товаров из корзины.
        Каждый элемент списка - это словарь с данными, которые включают id, offer-объект, цену c учетом скидки на продукт (если таковая имеется),
        количество в корзине, стоимость с учетом количества
        """
        offers_from_cart_with_discount, offers_from_cart_without_discount = self.get_offers_with_and_without_discount(offers_from_cart)
        combined_offers_from_cart = offers_from_cart_with_discount + offers_from_cart_without_discount
        cart_data = [{a: b for a, b in zip(['id', 'offer', 'price', 'quantity', 'total_price'],
                                   [item[0].item_pk, item[0], item[1], item[0].amount, item[0].amount * item[1]])}
             for item in combined_offers_from_cart]
        return cart_data

    def get_total_price_cart(self, cart):
        """
        Получаем общую стоимость корзины с учетом скидок на продукты
        """
        offers_from_cart = Offer.objects.filter(cart_item__cart=cart).annotate(amount=F('cart_item__quantity'),
                                                                                    item_pk=F('cart_item__id'))
        data_from_cart = self.get_data_from_cart(offers_from_cart)
        summ = Decimal(sum((item['total_price'] for item in data_from_cart))).quantize(Decimal('1.00'))

        return summ

    def apply_set_discounts(self, cart):
        """
        Применение скидки на продуктовый набор
        """
        # получаем список наборов продуктов, которые есть в корзине
        sets_of_products_in_cart = SetOfProducts.objects.filter(product_groups__products__in=Product.objects.filter(offers__cart_item__cart=cart).distinct()).distinct()
        # создаем лист данных, куда будем записывать данные по продуктовым наборам в виде {продуктовый набор: сумма скидки}
        set_and_discount = {}
        for set in sets_of_products_in_cart:
            # для каждого продуктового набора определяем группы продуктов
            groups_in_set_of_products = ProductGroup.objects.filter(set_of_products=set)
            # находим продукты, участвующие в группах
            products_in_group = (Product.objects.filter(product_groups=group) for group in groups_in_set_of_products)
            # находим товары из корзины для двух групп
            cart_items_in_group = [cart.cart_item.all().filter(offer__product__in=products) for products in products_in_group]
            # разделяем товары из корзины по двум группам
            first_group, second_group = cart_items_in_group[0], cart_items_in_group[1]
            if first_group.exists() and second_group.exists():
                # если в корзине есть товары из двух групп продуктов, входящих в продуктовый набор, значит он представлен в корзине полноценно
                # и высчитываем сумму скидки
                # для этого по товарам из полноценного продуктового набора получаем данные из корзины и по ним высчитываем их общую стоимость
                data_from_cart = self.get_data_from_cart(Offer.objects.filter(cart_item__in=first_group|second_group).annotate(amount=F('cart_item__quantity'),
                                                                                   item_pk=F('cart_item__id')))
                summ = Decimal(sum((item['total_price'] for item in data_from_cart))).quantize(Decimal('1.00'))
                # получаем объект скидки на наш продуктовый набор при условии его активности и действующих сроков
                current_time = timezone.now()
                set_discount = SetDiscount.objects.filter(set_of_products=set, is_active=True, start_date__lte=current_time, end_date__gte=current_time).first()
                # если скидка действующая высчитываем сумму скидки
                if set_discount:
                    discount_size = set_discount.size
                    if set_discount.is_percent:
                        summ_discount = summ * discount_size / 100
                    else:
                        summ_discount = Decimal(discount_size)
                    # записываем данные в лист данных в виде {продуктовый набор: сумма скидки}
                    set_and_discount.setdefault(set, summ_discount.quantize(Decimal("1.00")))
        # если в корзине оказались полноценные продуктовые наборы с действующими скидками
        if set_and_discount:
            # путем сортировки находим самый "тяжелый" по сумме скидки продуктовый набор
            set_info = tuple(sorted(set_and_discount.items(), key=lambda item: item[1], reverse=True))[0]
            # возвращаем инфу по продуктовому набору и стоимость всей корзины с учетом этой скидки
            return set_info, self.get_total_price_cart(cart) - set_info[1]
        else:
            return None, self.get_total_price_cart(cart)

    def apply_cart_discount(self, cart):
        """
        Применение скидки на корзину покупок к сумме корзины.

        :param cart: Корзина покупок.
        :return: Общая сумма корзины с учетом скидки на корзину, если она есть, иначе общая сумма корзины без скидки.
        """
        current_time = timezone.now()
        discount_amount = 0
        discounts = cart.discounts.filter(
            cart=cart,
            is_active=True,
            start_date__lte=current_time,
            end_date__gt=current_time,
        )
        # Если нет скидок, то возвращаем общую стоимость корзины без учета скидки
        if not discounts:
            return discount_amount, self.get_total_price_cart(cart)

        # Вычисляем общую стоимость товаров в корзине
        total_price = self.get_total_price_cart(cart)
        # Получаем общее количество товаров в корзине
        total_quantity = cart.get_total_quantity()
        # Применяем скидки к общей стоимости корзины
        for discount in discounts:
            # Пропускаем скидки, которые не подходят по минимальной сумме заказа или минимальному количеству товаров
            if discount.min_order_sum and total_price < discount.min_order_sum:
                continue

            if discount.min_quantity and total_quantity < discount.min_quantity:
                continue

            # Рассчитываем величину скидки
            if discount.is_percent:
                discount_amount = total_price * (
                    Decimal(discount.discount) / Decimal("100.0")
                )
            else:
                discount_amount = Decimal(discount.discount)

            # Применяем скидку к общей стоимости товаров в корзине
            total_price -= discount_amount

        # Возвращаем общую стоимость корзины с учетом примененных скидок
        return discount_amount, total_price

    def get_total_price_cart_with_all_discounts(self, cart):
        """
        Метод для получения итоговой стоимости корзины товаров с учетом всех возможных скидок
        """
        discount, total_price_after_cart_discount = self.apply_cart_discount(cart)
        discount_info, total_price_after_set_discount = self.apply_set_discounts(cart)
        if total_price_after_cart_discount < total_price_after_set_discount:
            return total_price_after_cart_discount
        else:
            return total_price_after_set_discount
