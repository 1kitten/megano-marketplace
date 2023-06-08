from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import add_to_cart, get_cart, remove_from_cart, change_cart

app_name = "app_basket"

urlpatterns = [
    path('', get_cart, name='cart'),
    path('add/', add_to_cart, name='add_to_cart'),
    path('remove/', remove_from_cart, name='remove_from_cart'),
    path('change/', change_cart, name='change_cart'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

