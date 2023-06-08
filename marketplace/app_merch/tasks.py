from typing import Union

from app_merch.payment_service import pay_for_the_order
from marketplace.celery import app
from app_merch.import_service import ImportProductsService


@app.task
def send_request_to_payment_service(
    username: str, order_id: int, card_number: str, amount: float
) -> Union[dict, str]:
    """
    Задача, которая будет добавлена в очередь на выполнение.
    Отправляет запрос на оплату заказа.
    """
    response = pay_for_the_order(username, order_id, card_number, amount)
    return response


@app.task
def make_an_products_importation(
    filepath: str
) -> bool:
    """
    Задача, которая будет добавлена в очередь на выполнение.
    Вызывает метод, парсящий JSON файл с информацией о товаре
    для последующего добавления.
    """
    result = ImportProductsService().import_products(filepath=filepath)
    return result


@app.task
def send_log_file_to_email(dst_email: str) -> bool:
    """
    Задача, которая будет добавлена в очередь на выполнение.
    Вызывает метод, отправляющий лог файл на переданный E-mail.
    """
    result = ImportProductsService().send_log(dst_email)
    return result
