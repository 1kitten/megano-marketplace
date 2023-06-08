from functools import wraps
from typing import Callable
from typing import Union

import requests
from django.shortcuts import redirect
from requests.exceptions import ConnectionError, Timeout

from marketplace.settings import PURCHASE_URL


def pay_for_the_order(
    username: str, order_id: int, card_number: str, amount: float
) -> Union[dict, str]:
    """
    Функция отправки запроса на оплату заказа.
    В ответе получаем JSON со статусом оплаты.
    """
    try:
        response = requests.post(
            url=PURCHASE_URL,
            json={
                "username": username,
                "order_id": order_id,
                "card_number": card_number,
                "amount": amount,
            },
            timeout=10,
        )
        return response.json()
    except (ConnectionError, Timeout):
        return "Error: No connection or timeout."


def is_active_orders(view_func: Callable) -> Callable:
    """ Проверка наличия у пользователя активных заказов. """

    @wraps(view_func)
    def wrapper(view, *args, **kwargs) -> Callable:
        session = dict(view.request.session).get('user_data')
        active_order = (
            view.request.user.profile.buyer.orders.filter(
                order_status='not-paid'
            )
        )

        if not session or active_order:
            return redirect('pages:order-step-1')

        response = view_func(view, *args, **kwargs)
        return response

    return wrapper
