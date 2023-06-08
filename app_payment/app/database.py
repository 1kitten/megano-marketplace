from pymongo import MongoClient
from pymongo.collection import Collection

from schemas import PaymentInformation


CONNECTION_STRING: str = "mongodb://user:pass@mongodb"


def get_database():
    """Функция получения клиента MongoDB"""

    client = MongoClient(CONNECTION_STRING)
    return client["user_payments"]


def add_user_payment_information(
    payment_information: PaymentInformation, collection: Collection
) -> None:
    """Функция добавления платежной информации пользователя в MongoDB"""

    collection.insert_one(
        {
            "username": payment_information.username,
            "order_id": payment_information.order_id,
            "card_number": payment_information.card_number,
            "amount": payment_information.amount,
        }
    )
