from django.db import models

from .singleton_model import SingletonModel


class SiteSettings(SingletonModel):
    """Модель глобальных настроек сайта."""

    time_to_cache = models.PositiveIntegerField(
        default=0, verbose_name="Время кеширования"
    )
    banners_cache_time = models.PositiveIntegerField(
        default=0, verbose_name="Время кеширования баннеров"
    )
    top_seller_products_cache_time = models.PositiveIntegerField(
        default=0, verbose_name="Время кеширования топ 10 продуктов продавца"
    )

    def __str__(self):
        return "Настройки"
