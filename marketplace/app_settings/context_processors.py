from .models import SiteSettings


def settings(request):
    """Контекст процессор инициализирующий глобальные настройки."""
    return {"settings": SiteSettings.load()}
