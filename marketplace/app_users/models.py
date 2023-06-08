from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import Sum, F

User._meta.get_field("email")._unique = False


class Profile(models.Model):
    """
    Модель профиля пользователя.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="profile",
        db_index=True,
        verbose_name="пользователь",
    )
    full_name = models.CharField(max_length=150, verbose_name="полное имя")
    phone_number = models.CharField(
        max_length=50, verbose_name="номер телефона", unique=True
    )
    address = models.CharField(max_length=255, verbose_name="адрес")
    avatar = models.ForeignKey(
        "app_merch.Image",
        on_delete=models.SET_NULL,
        related_name="profile",
        blank=True,
        null=True,
        verbose_name="аватар",
    )

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return self.full_name


class Seller(models.Model):
    """
    Модель продавца.
    """

    profile = models.OneToOneField(
        Profile,
        on_delete=models.PROTECT,
        related_name="seller",
        db_index=True,
        verbose_name="профиль",
    )
    title = models.CharField(max_length=100, verbose_name="название")
    description = models.TextField(max_length=1000, verbose_name="описание")

    class Meta:
        verbose_name = "Продавец"
        verbose_name_plural = "Продавцы"

    def __str__(self):
        return self.title

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        """
        Сброс кеша при изменении продавца.
        """
        if cache.get(f"Seller {self.pk} top products"):
            cache.delete(f"Seller {self.pk} top products")
        super().save()

    def delete(self, using=None, keep_parents=False):
        """
        Сброс кеша при удалении продавца.
        """
        if cache.get(f"Seller {self.pk} top products"):
            cache.delete(f"Seller {self.pk} top products")
        super().delete()


class Buyer(models.Model):
    """
    Модель покупателя.
    """

    profile = models.OneToOneField(
        Profile,
        null=True,
        on_delete=models.PROTECT,
        related_name="buyer",
        db_index=True,
        verbose_name="покупатель",
    )
    views = models.ManyToManyField(
        "app_merch.Product", verbose_name="история просмотров"
    )

    class Meta:
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"

    def __str__(self):
        return f"{self.profile}"


class ComparisonList(models.Model):
    """
    Модель для списка сравнения продуктов.
    """

    profile = models.OneToOneField(
        Buyer,
        null=True,
        on_delete=models.PROTECT,
        related_name="compare",
        db_index=True,
        verbose_name="владелец списка",
    )
    offer = models.ForeignKey(
        "app_merch.Offer",
        null=True,
        on_delete=models.PROTECT,
        related_name="offer",
        db_index=True,
        verbose_name="список для сравнения",
    )

    class Meta:
        verbose_name = "Список сравнения"
        verbose_name_plural = "Списки сравнения"

    def add_to_list(self):
        pass

    def remove_from_list(self):
        pass

    def return_list(self):
        pass

    def return_amount_in_list(self):
        pass

    def __str__(self):
        return f"Список сравнения {self.profile}"


class PaymentType(models.Model):
    """Модель типа оплаты."""

    title = models.CharField(max_length=100, verbose_name="вид оплаты")
    is_active = models.BooleanField(default=True, verbose_name="активен")

    class Meta:
        verbose_name = "вид оплаты"
        verbose_name_plural = "виды оплаты"

    def __str__(self):
        return self.title


class Payment(models.Model):
    buyer = models.ForeignKey(
        Buyer,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="покупатель",
    )
    payment_type = models.ForeignKey(
        PaymentType,
        on_delete=models.PROTECT,
        related_name="payment",
        verbose_name="тип оплаты",
    )
    credit_card = models.CharField(max_length=8, verbose_name="номер счета", null=True)

    class Meta:
        verbose_name = "Тип оплаты"
        verbose_name_plural = "Типы оплаты"

    def __str__(self):
        return self.payment_type.title


class DeliveryType(models.Model):
    type = models.CharField(max_length=100, verbose_name="тип")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="цена")

    class Meta:
        verbose_name = "Тип доставки"
        verbose_name_plural = "Типы доставок"

    def __str__(self):
        return self.type


class Order(models.Model):
    PAYMENT_STATUS_CHOISES = {
        ("not_paid", "Не оплачен"),
        ("paid", "Оплачен"),
    }

    ORDER_STATUS_CHOISES = {
        ("awaiting_payment", "Ожидает оплаты"),
        ("is_delivering", "Доставляется"),
        ("delivered", "Доставлен"),
    }

    buyer = models.ForeignKey(
        Buyer,
        on_delete=models.PROTECT,
        related_name="orders",
        db_index=True,
        verbose_name="покупатель",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="тип оплаты",
        null=True,
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOISES, verbose_name="статус оплаты"
    )
    address = models.JSONField(verbose_name="адрес", null=True)
    delivery_type = models.ForeignKey(
        DeliveryType,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="тип доставки",
        null=True,
    )
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="дата заказа")
    departure_date = models.DateTimeField(
        null=True, blank=True, verbose_name="дата отправки"
    )
    delivery_date = models.DateTimeField(
        null=True, blank=True, verbose_name="дата доставки"
    )
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOISES,
        verbose_name="статус доставки",
        null=True,
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ {self.id} от {self.order_date}"

    @staticmethod
    def total_price(order):
        return order.annotate(
            price=Sum(F("order_items__offer__price") * F("order_items__quantity"))
        )


class OrderItem(models.Model):
    offer = models.ForeignKey(
        "app_merch.Offer",
        on_delete=models.PROTECT,
        related_name="order_items",
        db_index=True,
        verbose_name="предложение",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="order_items",
        db_index=True,
        verbose_name="заказ",
    )
    quantity = models.PositiveIntegerField(verbose_name="количество")

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"
