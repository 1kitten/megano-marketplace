from django.utils import timezone
from app_basket.models import Cart
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from pydantic.error_wrappers import ValidationError


class Image(models.Model):
    """Модель картинок."""

    file = models.FileField(upload_to="static/assets/img/icons/", verbose_name="файл")
    title = models.CharField(max_length=150, verbose_name="наименование")

    class Meta:
        verbose_name = "Картинка"
        verbose_name_plural = "Картинки"

    def __str__(self):
        return f"{self.pk}. {self.title}"


class Category(MPTTModel):
    """Модель категории товаров."""

    title = models.CharField(max_length=150, verbose_name="наименование")
    icon = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="иконка категории",
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        verbose_name="родительская категория",
    )
    slug = models.SlugField(unique=True, verbose_name="url")
    is_active = models.BooleanField(default=True, verbose_name="активная категория")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    class MPTTMeta:
        order_insertion_by = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("categories_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        """Сброс кеша после изменения или добавления категории."""
        if cache.get("Categories"):
            cache.delete("Categories")
        super().save()

    def delete(self, *args, **kwargs):
        """Сброс кеша после удаления категории."""
        if cache.get("Categories"):
            cache.delete("Categories")
        super().delete()


class Tag(models.Model):
    """
    Модель тэгов.
    """

    title = models.CharField(max_length=100, verbose_name="название")

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

    def __str__(self):
        return self.title


class Product(models.Model):
    """
    Модель продуктов.
    """

    title = models.CharField(max_length=150, verbose_name="название")
    description = models.TextField(max_length=1000, verbose_name="описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="дата создания")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
        verbose_name="категория",
    )
    tags = models.ManyToManyField(
        Tag, related_name="products", db_index=True, verbose_name="тэги"
    )
    icon = models.ForeignKey(
        Image,
        related_name="products",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="изображение продукта",
    )
    media = models.ManyToManyField(Image, verbose_name="медиафайлы продукта")
    characters = models.JSONField(verbose_name="характеристики")
    is_active = models.BooleanField(default=False, verbose_name='активность')

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return self.title

    def best_offer(self):
        return self.offers.first()


class ProductGroup(models.Model):
    """
    Модель группы товаров.
    """

    name = models.CharField(max_length=100, verbose_name="название")
    products = models.ManyToManyField(
        Product, related_name="product_groups", verbose_name="продукты"
    )

    class Meta:
        verbose_name = "Группа товаров"
        verbose_name_plural = "Группы товаров"

    def __str__(self):
        return self.name


class Offer(models.Model):
    """
    Модель предложений.
    """

    seller = models.ForeignKey(
        "app_users.Seller",
        on_delete=models.PROTECT,
        related_name="offers",
        db_index=True,
        verbose_name="продавец",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="offers",
        db_index=True,
        verbose_name="продукт",
    )
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="цена")
    quantity = models.PositiveIntegerField(default=0, verbose_name="количество")
    is_active = models.BooleanField(default=True, verbose_name="актуальность")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="дата создания")
    is_delivery_free = models.BooleanField(
        default=False, verbose_name="бесплатная доставка"
    )
    total_views = models.PositiveIntegerField(
        default=0, verbose_name="количество просмотров"
    )

    class Meta:
        verbose_name = "Предложение"
        verbose_name_plural = "Предложения"
        ordering = ["price"]

    def __str__(self):
        return f"{self.product} from {self.seller}"


class SetOfProducts(models.Model):
    """
    Модель наборов товаров.
    """

    name = models.CharField(max_length=100, verbose_name="название")
    product_groups = models.ManyToManyField(
        ProductGroup, related_name="set_of_products", verbose_name="группы товаров"
    )

    class Meta:
        verbose_name = "Набор товаров"
        verbose_name_plural = "Наборы товаров"

    def product_group(self):
        return ', '.join([group.name for group in self.product_groups.all()])

    def __str__(self):
        return self.name


class Discount(models.Model):
    """
    Модель скидок.
    """

    product = models.OneToOneField(
        Product,
        on_delete=models.PROTECT,
        related_name="discounts",
        db_index=True,
        verbose_name="продукт",
        null=True, blank=True,
    )
    # set_of_products = models.ForeignKey(
    #     SetOfProducts,
    #     on_delete=models.PROTECT,
    #     related_name="discounts",
    #     db_index=True,
    #     verbose_name="набор товаров",
    #     null=True, blank=True,
    # )
    is_percent = models.BooleanField(verbose_name="в процентах")
    size = models.PositiveIntegerField(verbose_name="размер")
    start_date = models.DateTimeField(verbose_name="дата начала", null=True, blank=True,)
    end_date = models.DateTimeField(verbose_name="дата окончания", null=True, blank=True,)
    description = models.TextField(max_length=1000, verbose_name="описание")
    is_active = models.BooleanField(default=True, verbose_name="актуальность")
    is_priority = models.BooleanField(default=False, verbose_name="приоритет")

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"

    def __str__(self):
        return f"{self.size}"

    def save(self, *args, **kwargs):
        current_time = timezone.now()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Дата начала не может быть больше даты окончания")
        if self.end_date and self.end_date <= timezone.now():
            self.is_active = False
        super().save(*args, **kwargs)


class SetDiscount(models.Model):
    """
    Модель скидок на наборы товаров.
    """
    set_of_products = models.ForeignKey(
        SetOfProducts, on_delete=models.PROTECT,
        related_name='set_discounts', db_index=True, verbose_name='Наборы товаров', null=True)

    is_percent = models.BooleanField(verbose_name="в процентах", default=False)
    size = models.PositiveIntegerField(verbose_name="размер", null=True)
    start_date = models.DateTimeField(verbose_name="дата начала", null=True, blank=True)
    end_date = models.DateTimeField(verbose_name="дата окончания", null=True, blank=True)
    description = models.TextField(max_length=1000, verbose_name="описание", null=True)
    is_active = models.BooleanField(default=True, verbose_name="актуальность")
    is_priority = models.BooleanField(default=False, verbose_name="приоритет")

    class Meta:
        verbose_name = "Скидка на набор"
        verbose_name_plural = "Скидки на наборы"

    def __str__(self):
        return f"Скидка {self.size} на набор {self.set_of_products}"


class CartDiscount(models.Model):
    """
    Модель скидки на корзину покупок.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.PROTECT,
        related_name="discounts",
        db_index=True,
        verbose_name="корзина",
        unique=True
    )
    min_order_sum = models.PositiveIntegerField(
        verbose_name="минимальная сумма заказа", null=True, blank=True
    )
    min_quantity = models.PositiveIntegerField(
        verbose_name="минимальное количество товаров", null=True, blank=True
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="скидка"
    )
    is_percent = models.BooleanField(verbose_name="в процентах")
    start_date = models.DateTimeField(verbose_name="дата начала")
    end_date = models.DateTimeField(verbose_name="дата окончания")
    description = models.TextField(max_length=1000, verbose_name="описание")
    is_active = models.BooleanField(default=True, verbose_name="актуальность")

    class Meta:
        verbose_name = "Скидка на корзину"
        verbose_name_plural = "Скидки на корзину"

    def __str__(self):
        return f"{self.discount}"


class Banner(models.Model):
    """Модель баннеров."""

    title = models.CharField(max_length=30, verbose_name="наименование")
    primary_text = models.CharField(
        max_length=10, null=True, blank=True, verbose_name="главное"
    )
    description = models.TextField(max_length=250, verbose_name="описание")
    file = models.ForeignKey(Image, on_delete=models.CASCADE, verbose_name="медиа файл")
    is_active = models.BooleanField(default=True, verbose_name="активность")
    link = models.URLField(verbose_name="ссылка")

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"

    def __str__(self):
        return self.title

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        """Сброс кеша при изменении или добавлении баннера."""
        if cache.get("Banners"):
            cache.delete("Banners")
        super().save()

    def delete(self, using=None, keep_parents=False):
        """Сброс кеша при удалении баннера."""
        if cache.get("Banners"):
            cache.delete("Banners")
        super().delete()


class Review(models.Model):
    profile = models.ForeignKey(
        "app_users.Profile", on_delete=models.CASCADE, related_name="reviews"
    )
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveIntegerField(
        verbose_name="Рейтинг", help_text="Введите рейтинг от 1 до 5",
    )
    text = models.TextField(
        verbose_name="Текст отзыва",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата создания отзыва",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Отображать ли этот отзыв на сайте",
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile.user.username} - {self.offer.product}"


class WatchedProduct(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="пользователь"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name="продукт", db_index=True
    )
    view_date = models.DateTimeField(auto_now_add=True, verbose_name="дата просмотра")

    class Meta:
        ordering = ["view_date"]


