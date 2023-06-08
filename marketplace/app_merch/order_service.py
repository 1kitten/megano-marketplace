from datetime import datetime

from django.db import transaction
from django.db.models import QuerySet

from app_basket.models import Cart
from app_users.models import (
    Profile,
    Buyer,
    Order,
    DeliveryType,
    PaymentType,
    Payment,
    OrderItem
)


class OrderCreation:
    """Сервис для работы с заказами."""

    @staticmethod
    def create_new_order(profile: Profile) -> None:
        """Метод создания нового заказа."""

        with transaction.atomic():
            buyer = Buyer.objects.get_or_create(profile=profile)
            Order.objects.get_or_create(
                buyer=buyer[0],
                payment_status="not_paid",
                order_status='awaiting_payment'
            )

    @staticmethod
    def add_delivery_data_to_order(
        buyer: Buyer, delivery_type: str, address: dict
    ) -> None:
        """Метод добавления адреса и типа доставки."""

        with transaction.atomic():
            order = OrderCreation._get_not_paid_order(buyer=buyer)
            OrderCreation.add_delivery_type_to_order(
                delivery_type=delivery_type, order=order
            )
            OrderCreation.add_address_data_to_order(address=address, order=order)

    @staticmethod
    def add_payment_data_to_order(buyer: Buyer, payment_type: str) -> None:
        """Метод добавления информации о способе оплаты в заказ."""

        with transaction.atomic():
            order = OrderCreation._get_not_paid_order(buyer=buyer)
            OrderCreation.add_payment_type_to_order(
                payment_type=payment_type, order=order, buyer=buyer
            )

    @staticmethod
    def add_delivery_type_to_order(delivery_type: str, order: Order) -> None:
        """Метод добавления типа доставки в заказ."""

        order.delivery_type = DeliveryType.objects.get_or_create(type=delivery_type)[0]
        order.save()

    @staticmethod
    def add_address_data_to_order(address: dict, order: Order) -> None:
        """Метод добавленя данных, касательно адреса доставки, в заказ."""

        order.address = address
        order.save()

    @staticmethod
    def add_payment_type_to_order(
        payment_type: str, order: Order, buyer: Buyer
    ) -> None:
        """Метод добавления данных, касательно типа оплаты, в заказ."""

        type_of_payment = PaymentType.objects.filter(title=payment_type).first()
        order.payment = OrderCreation._get_payment(
            buyer=buyer, type_of_payment=type_of_payment
        )
        order.save(update_fields=["payment"])

    @staticmethod
    def _get_payment(buyer: Buyer, type_of_payment: PaymentType) -> Payment:
        """Метод для поиска 'Payment', если такого нет, то создаётся новый."""

        return Payment.objects.get_or_create(buyer=buyer, payment_type=type_of_payment)[
            0
        ]

    @staticmethod
    def _get_not_paid_order(buyer: Buyer) -> Order:
        """Метод получения не оплаченного заказа, если такого нет, то создаётся новый."""

        return Order.objects.get_or_create(buyer=buyer, payment_status='not_paid')[0]

    @staticmethod
    def complete_order(order: Order, cart_items: QuerySet, status: str, cart: Cart = None) -> None:
        """ Метод подтверждения заказа пользователя. """

        with transaction.atomic():
            OrderCreation._change_order_statuses(order=order, status=status)
            OrderCreation._add_items_to_order(order=order, cart_items=cart_items)
            Cart.objects.get(pk=cart.pk).delete()

    @staticmethod
    def _change_order_statuses(order: Order, status: str) -> None:
        """ Метод смены статусов заказа. """

        with transaction.atomic():
            if status == 'success':
                order.payment_status = 'paid'
                order.order_status = 'is_delivering'
                order.departure_date = datetime.now().date()

            order.save()

    @staticmethod
    def _add_items_to_order(order: Order, cart_items: QuerySet) -> None:
        """ Метод добавления товаров в заказ. """

        for i_item in cart_items:
            OrderItem.objects.create(
                order=order,
                offer=i_item,
                quantity=i_item.amount
            )
