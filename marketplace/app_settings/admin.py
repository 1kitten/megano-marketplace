from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SettingsAdmin(admin.ModelAdmin):
    """Регистрация глобальных настроек в админ-панели."""

    pass
