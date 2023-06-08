from random import choice

from database import add_user_payment_information, get_database
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from schemas import PaymentInformation

app = FastAPI()
DATABASE = get_database()
collection = DATABASE["user_payments_1"]

PAYMENT_ERRORS: tuple = (
    "Not enough money",
    "Card declined",
    "Service is unreachable",
    "Bank not supported",
)


async def validate_card_number(card_number: str) -> bool:
    """Функция валидации карты."""

    user_card_number: str = card_number.replace(" ", "")
    if len(user_card_number) == 8:
        try:
            int_card_number: int = int(user_card_number)
        except ValueError:
            return False
        else:
            if int_card_number % 2 == 0 and user_card_number[-1] != "0":
                return True
    return False


@app.post("/api/v1/purchase/")
async def make_payment(payment_information: PaymentInformation) -> JSONResponse:
    """
    Эндпоинт для проведения оплаты.
    Если карта не проходит валидацию, платёж отклоняется со случайной ошибкой.
    """

    if not await validate_card_number(payment_information.card_number):
        return JSONResponse(
            status_code=403,
            content={"status": "error", "message": choice(PAYMENT_ERRORS)},
        )

    add_user_payment_information(payment_information, collection)

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Order {} was successfully purchased.".format(
                payment_information.order_id
            ),
        },
    )
