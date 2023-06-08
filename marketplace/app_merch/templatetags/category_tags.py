from app_merch.models import Category
from app_settings.models import SiteSettings
from django import template
from django.core.cache import cache

register = template.Library()


@register.simple_tag()
def get_categories():
    """Тег для получения категорий."""
    time_to_cache = SiteSettings.load().time_to_cache

    if not time_to_cache:
        time_to_cache = 1

    return cache.get_or_set(
        "Categories",
        Category.objects.filter(is_active=True),
        time_to_cache * 60 * 60 * 24,
    )
