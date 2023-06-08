from pydantic import BaseModel


class PaymentInformation(BaseModel):
    """Схема информации о пользователе."""

    username: str
    order_id: int
    card_number: str
    amount: float
