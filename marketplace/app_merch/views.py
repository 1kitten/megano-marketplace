from django.utils import timezone

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .comparison_service import comparison_service
from .import_service import ImportProductsService
from app_settings.models import SiteSettings
from app_users.models import DeliveryType, PaymentType, Seller, Order
from django.core.cache import cache
from django.db.models import Count, Max, Min, QuerySet
from django.shortcuts import get_object_or_404, redirect, render
import os
from marketplace.settings import BASE_DIR
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, View, TemplateView
from django.views.generic.edit import FormView
from mptt.querysets import TreeQuerySet
from . import review_service
from .discount_service import DiscountService
from .forms import (OrderDeliveryDataForm, OrderUserDataForm,
                    ReviewForm, PaymentForm, ProductImportForm)
from .models import Banner, Category, Discount, Offer, Product, Review, Tag
from .viewed_products import watched_products_service
from app_basket.cart import CartService
from app_basket.models import Cart
from .order_service import OrderCreation
from .payment_service import is_active_orders
from .tasks import send_request_to_payment_service, make_an_products_importation, send_log_file_to_email


class IndexView(ListView):
    """Вью класс для главной страницы MEGANO."""

    template_name = "index.html"
    context_object_name = "products"
    model = Product

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        banners_cache_time = SiteSettings.load().banners_cache_time

        if not banners_cache_time:
            banners_cache_time = 10

        banners = Banner.objects.filter(is_active=True).order_by('?')[:3]
        semi_banners = Banner.objects.filter(is_active=True)[:3]

        context["banners"] = cache.get_or_set(
            "Banners",
            banners,
            banners_cache_time * 60,
        )

        context["semi_banners"] = cache.get_or_set(
            "Semi_banners",
            semi_banners,
            banners_cache_time * 60
        )

        return context


class CategoryView(ListView):
    """Вью класс получения активных категорий товаров."""

    template_name = "base.html"
    context_object_name = "categories"

    def get_queryset(self):
        """Получаем доступные категории и кешируем их на 1 день."""
        time_to_cache = SiteSettings.load().time_to_cache
        if not time_to_cache:
            time_to_cache = 1

        return cache.get_or_set(
            f"Categories",
            Category.objects.filter(is_active=True),
            time_to_cache * 60 * 60 * 24,
        )


class AllDiscountView(ListView):
    """View для получения всех активных скидок."""

    template_name = "products/all_product_discounts.html"
    context_object_name = "all_discounts"

    def get_queryset(self):
        """Получаем все доступные скидки и кешируем их на 1 день."""
        time_to_cache = SiteSettings.load().time_to_cache
        if not time_to_cache:
            time_to_cache = 1
        current_time = timezone.now()

        return cache.get_or_set(
            f"Discounts",
            Product.objects.filter(discounts__is_active=True,
                                   discounts__start_date__lte=current_time,
                                   discounts__end_date__gte=current_time,),
            time_to_cache * 60 * 60 * 24,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_time = timezone.now()
        products = Product.objects.filter(discounts__is_active=True).order_by('-discounts__is_priority')
        discount_service = DiscountService()
        product_info_list = []
        for product in products:
            icon_url = product.icon.file.url if product.icon else None
            offers = Offer.objects.filter(product=product)

            (
                offers_with_discount,
                offers_without_discount,
            ) = discount_service.get_offers_with_and_without_discount(offers)

            average_with_discount = discount_service.calculate_average_with_discount(
                offers_with_discount, offers_without_discount
            )

            average_price = discount_service.calculate_average_price(offers)
            product_info = {
                "product": product,
                "icon_url": icon_url,
                "average_price": average_price,
                "average_with_discount": average_with_discount,
            }
            review_count = review_service.review_count(product)
            product_info['review_count'] = review_count
            product_info_list.append(product_info)
        context["product_info_list"] = product_info_list

        return context


class PriorityDiscountView(ListView):
    """View для получения приоритетных скидок."""

    template_name = "products/priorities_discounts.html"
    context_object_name = "priorities_discounts"

    def get_queryset(self):
        """Получаем приоритетные скидки и кешируем их на 1 день."""
        time_to_cache = SiteSettings.load().time_to_cache
        if not time_to_cache:
            time_to_cache = 1

        return cache.get_or_set(
            f"Priorities_discounts",
            Product.objects.filter(discounts__is_priority=True),
            time_to_cache * 60 * 60 * 24,
        )


class CatalogView(ListView):
    """Вью класс для получения списка товаров и отображения их в каталоге."""

    template_name = "catalog.html"
    context_object_name = "products"
    paginate_by = 8

    def get_queryset(self):
        """
        Получение списка товаров по фильтру и сортировке.
        Список кешируется на 1 день.
        """

        if cache.get('products'):
            queryset = cache.get('products')
        else:
            queryset: QuerySet = Product.objects.filter(is_active=True, offers__is_active=True)

        time_to_cache: int = SiteSettings.load().time_to_cache
        if not time_to_cache:
            time_to_cache = 1

        price_range: str = self.request.GET.get("price")
        title: str = self.request.GET.get("title")
        in_stock: str = self.request.GET.get("in_stock")
        delivery_free: str = self.request.GET.get("delivery_free")
        slug: str = self.request.GET.get("cat")
        tag = self.request.GET.get("tag")

        price_sort: str = self.request.GET.get("price_sort")
        created_at_sort: str = self.request.GET.get("created_at_sort")
        reviews_sort: str = self.request.GET.get("reviews_sort")
        views_sort: str = self.request.GET.get("views_sort")

        if slug and slug != "all":
            category: Category = Category.objects.get(slug=slug)
            sub_categories: TreeQuerySet = category.get_descendants(include_self=True)

            queryset: QuerySet = queryset.select_related("category").filter(
                category__in=sub_categories
            )
        if price_range:
            min_price, max_price = price_range.split(";")[0], price_range.split(";")[1]
            queryset: QuerySet = queryset.filter(
                offers__price__range=(min_price, max_price)
            )
        if title:
            queryset: QuerySet = queryset.filter(title__icontains=title)
        if in_stock:
            queryset: QuerySet = queryset.filter(offers__quantity__gt=0)
        if delivery_free:
            queryset: QuerySet = queryset.filter(offers__is_delivery_free=True)
        if tag:
            queryset: QuerySet = queryset.filter(tags__pk=tag)

        queryset = queryset.values(
            "pk", "category__title", "icon__file", "title", "discounts"
        ).annotate(min_price=Min("offers__price"))

        if price_sort in ("-min_price", "min_price"):
            queryset: QuerySet = queryset.order_by(price_sort)
        if created_at_sort in ("-created_at", "created_at"):
            queryset: QuerySet = queryset.order_by(created_at_sort)
        if reviews_sort in ("desc", "asc"):
            queryset: QuerySet = queryset.annotate(
                review_amount=Count("offers__reviews")
            )
            if reviews_sort == "desc":
                queryset: QuerySet = queryset.order_by("-review_amount")
            else:
                queryset: QuerySet = queryset.order_by("review_amount")
        if views_sort in ("desc", "asc"):
            if views_sort == "desc":
                queryset: QuerySet = queryset.order_by("-offers__total_views")
            else:
                queryset: QuerySet = queryset.order_by("offers__total_views")

        cache.set('products', queryset, time_to_cache * 60 * 60 * 24)
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        Получение контекста для корректного вывода отфильтрованных товаров.
        Контекст наполняется информацией касательно: тегов, макс. и мин. цены,
        категории, наименовании товара, нахождении товара в наличии, различной сортировки.
        Данные о минимальной и максимальной цене добавляются в сессию для
        последующего получения значения из неё.
        """
        context = super().get_context_data(**kwargs)

        context["tags"] = Tag.objects.all()[:5]

        price_range: str = self.request.GET.get("price")
        category: str = self.request.GET.get("cat")
        title: str = self.request.GET.get("title")
        in_stock: str = self.request.GET.get("in_stock")
        delivery_free: str = self.request.GET.get("delivery_free")

        price_sort: str = self.request.GET.get("price_sort")
        created_at_sort: str = self.request.GET.get("created_at_sort")
        reviews_sort: str = self.request.GET.get("reviews_sort")
        views_sort: str = self.request.GET.get("views_sort")

        min_price = self.object_list.aggregate(Min("offers__price"))[
            "offers__price__min"
        ]
        max_price = self.object_list.aggregate(Max("offers__price"))[
            "offers__price__max"
        ]

        if not self.request.session.get("min_price") or not self.request.session.get(
            "max_price"
        ):
            self.request.session["min_price"] = str(min_price)
            self.request.session["max_price"] = str(max_price)
        else:
            session_min_price = self.request.session.get("min_price", min_price)
            session_max_price = self.request.session.get("max_price", min_price)

            if str(min_price) > session_min_price:
                min_price = session_min_price

            if str(max_price) < session_max_price:
                max_price = session_max_price

            if session_min_price == "None" and session_max_price == "None":
                min_price = self.object_list.aggregate(Min("offers__price"))[
                    "offers__price__min"
                ]
                max_price = self.object_list.aggregate(Max("offers__price"))[
                    "offers__price__max"
                ]

        if price_range:
            curr_min_price, curr_max_price = (
                price_range.split(";")[0],
                price_range.split(";")[1],
            )
            context["curr_min_price"], context["curr_max_price"] = (
                curr_min_price,
                curr_max_price,
            )

        context["min_price"], context["max_price"] = min_price, max_price

        if category and category != "all":
            context["category"] = category
        if title:
            context["title"] = title
        if in_stock:
            context["in_stock"] = True
        if delivery_free:
            context["delivery_free"] = True

        if price_sort:
            context["price_sort"] = price_sort
        if created_at_sort:
            context["created_at_sort"] = created_at_sort
        if reviews_sort:
            context["reviews_sort"] = reviews_sort
        if views_sort:
            context["views_sort"] = views_sort

        if price_sort or created_at_sort or reviews_sort or views_sort:
            context["any_sort"] = True

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        watched_products_service.add_product(request=request, product=self.get_object())
        return super(ProductDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context["icon_url"] = product.icon.file.url if product.icon else None
        context["media"] = product.media.all()

        offers = Offer.objects.filter(product=self.object)

        discount_service = DiscountService()

        average_price = discount_service.calculate_average_price(offers)
        context["average_price"] = average_price

        (
            offers_with_discount,
            offers_without_discount,
        ) = discount_service.get_offers_with_and_without_discount(offers)

        average_with_discount = discount_service.calculate_average_with_discount(
            offers_with_discount, offers_without_discount
        )
        context["average_with_discount"] = average_with_discount

        price_difference = discount_service.calculate_price_difference(
            average_price, average_with_discount
        )
        percentage_difference = discount_service.calculate_percentage_difference(
            price_difference, average_price
        )
        context["percentage_difference"] = percentage_difference

        offers_combined = (
            discount_service.combine_offers_with_discount_and_without_discount(
                offers_with_discount, offers_without_discount
            )
        )

        context["offers_combined"] = offers_combined

        reviews = Review.objects.filter(offer__product=self.object, is_active=True)
        context["reviews"] = reviews
        review_count = review_service.review_count(product)
        context["review_count"] = review_count

        sellers = Seller.objects.filter(
            profile__in=[offer.seller.profile for offer in offers]
        )
        context["sellers"] = sellers

        if self.request.user.is_authenticated:
            form = ReviewForm()
            context["form"] = form
        return context

    def post(self, request, *args, **kwargs):
        """логика для добавления отзыва к товару"""
        product = self.get_object()
        return review_service.new_review(request, product)


class OrderUserDataView(View):
    """View для оформления заказа. 1-ый шаг заполнения, информация о пользователе."""

    def get(self, *args, **kwargs):
        self.request.session["step"] = 1
        form = OrderUserDataForm(request=self.request)
        context = {
            "cart_items": CartService(self.request).get_cart_item_list(),
            "form": form,
        }

        return render(self.request, "orders/order_user_data.html", context=context)

    def post(self, *args, **kwargs):
        form = OrderUserDataForm(self.request.POST)
        context = {
            "cart_items": CartService(self.request).get_cart_item_list(),
            "form": form,
        }

        if any(up in self.request.POST for up in ("password", "passwordRetry")):
            self.request.session["user_register_data"] = dict(self.request.POST)
            return redirect("app_users:register")

        if form.is_valid():
            self.request.session["user_data"] = dict(self.request.POST)
            self.request.session["step"] = 2

            OrderCreation.create_new_order(self.request.user.profile)

            return redirect("pages:order-step-2")

        if self.request.session.get("user_data"):
            self.request.session.pop("user_data")

        return render(self.request, "orders/order_user_data.html", context=context)


class OrderDeliveryView(View):
    """View для оформления заказа. 2-ый шаг заполнения, способ доставки."""

    def get(self, *args, **kwargs):
        self.request.session["step"] = 2
        return render(
            self.request,
            "orders/order_delivery.html",
            context={
                "delivery_type": DeliveryType.objects.all(),
                "form": OrderDeliveryDataForm(request=self.request),
            },
        )

    def post(self, *args, **kwargs):
        form = OrderDeliveryDataForm(self.request.POST)

        if not form.is_valid():
            return render(
                self.request,
                "orders/order_delivery.html",
                context={"delivery_type": DeliveryType.objects.all(), "form": form},
            )

        self.request.session["user_data"].update(
            {"delivery_data": dict(self.request.POST)}
        )
        self.request.session["step"] = 3

        full_address = {
            "city": self.request.POST.get("city"),
            "address": self.request.POST.get("address"),
        }

        OrderCreation.add_delivery_data_to_order(
            buyer=self.request.user.profile.buyer,
            delivery_type=self.request.POST.get("delivery"),
            address=full_address,
        )

        return redirect("pages:order-step-3")


class OrderPaymentView(View):
    """View для оформления заказа. 3-ый шаг заполнения, способ оплаты."""

    def get(self, *args, **kwargs):
        self.request.session["step"] = 3
        return render(
            self.request,
            "orders/order_payment.html",
            context={"payment_type": PaymentType.objects.filter(is_active=True)},
        )

    def post(self, *args, **kwargs):
        self.request.session["user_data"].update(
            {"payment_data": dict(self.request.POST)}
        )

        OrderCreation.add_payment_data_to_order(
            buyer=self.request.user.profile.buyer,
            payment_type=self.request.POST.get("pay"),
        )

        self.request.session["step"] = 4
        return redirect("pages:order-step-4")


class OrderPurchaseView(View):
    """View для оформления заказа. 4-ый шаг, проверка введённых данных."""

    def get(self, *args, **kwargs):
        self.request.session["step"] = 4
        cart = CartService(self.request)
        context = {
            "cart_items": cart.get_cart_item_list(),
            "total_price": DiscountService().get_total_price_cart(cart=cart.cart.pk)
        }
        return render(self.request, "orders/order_purchase.html", context=context)

    @staticmethod
    def post(*args, **kwargs):
        return redirect('pages:payment-view')


class DiscountListView(ListView):
    model = Discount
    template_name = "discounts/list_discounts.html"
    context_object_name = "discounts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_datetime = timezone.now()
        context["current_datetime"] = current_datetime
        products = Product.objects.filter(discounts__is_active=True).order_by('-discounts__is_priority')
        # discount_service = DiscountService()
        product_info_list = []
        for product in products:
            icon_url = product.icon.file.url if product.icon else None
            product_info = {
                "product": product,
                "icon_url": icon_url,
            }
            product_info_list.append(product_info)
        context["product_info_list"] = product_info_list

        return context


class DiscountDetailView(DetailView):
    model = Discount
    template_name = "discounts/discount_detail.html"
    context_object_name = "discount"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        discount = self.get_object()
        context["icon_url"] = discount.product.icon.file.url if discount.product.icon else None
        product = discount.product
        context["media"] = product.media.all()

        offers = Offer.objects.filter(product=product)
        discount_service = DiscountService()

        (
            offers_with_discount,
            offers_without_discount,
        ) = discount_service.get_offers_with_and_without_discount(offers)

        average_with_discount = discount_service.calculate_average_with_discount(
            offers_with_discount, offers_without_discount
        )

        average_price = discount_service.calculate_average_price(offers)
        context["average_price"] = average_price
        context["average_with_discount"] = average_with_discount

        price_difference = discount_service.calculate_price_difference(
            average_price, average_with_discount
        )
        percentage_difference = discount_service.calculate_percentage_difference(
            price_difference, average_price
        )

        print(average_price, average_with_discount, percentage_difference)
        context["percentage_difference"] = percentage_difference

        return context

    @staticmethod
    def post(*args, **kwargs):
        return redirect('pages:payment-view')


class PaymentView(LoginRequiredMixin, View):
    """ View для проведения оплаты заказа. """

    login_url = reverse_lazy('app_users:login')

    @is_active_orders
    def get(self, *args, **kwargs):
        return render(self.request, 'orders/payment.html', context={'form': PaymentForm})

    def post(self, *args, **kwargs):
        form = PaymentForm(self.request.POST)
        cart = Cart.objects.filter(buyer=self.request.user.profile.buyer).first()
        order = Order.objects.get(buyer=self.request.user.profile.buyer, payment_status='not_paid')
        amount = DiscountService().get_total_price_cart(cart=cart) if cart else order.total_price(order)

        if form.is_valid():
            result = send_request_to_payment_service.delay(
                username=self.request.user.username,
                order_id=order.pk,
                card_number=form.cleaned_data['numerol'],
                amount=str(amount)
            ).get()

            self.request.session['pay_result'] = result
            self.request.session['order_id'] = order.pk
            result_status = result['status'] if isinstance(result, dict) else result

            OrderCreation.complete_order(
                order=order,
                cart=cart,
                cart_items=CartService(self.request).get_cart_item_list(),
                status=result_status
            )

            return render(self.request, 'orders/payment_progress.html')
        return render(self.request, 'orders/payment.html', context={'form': form})


class ComparisonView(TemplateView):
    template_name = 'products/comparison.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comparison_list: QuerySet = comparison_service.get_comparison_list(request=self.request)
        context['comparison_list'] = comparison_list
        if comparison_list:
            if all([product.category_id == comparison_list.first().category_id for product in comparison_list]):
                context["match"] = True
                characters_list = []
                for product in comparison_list:
                    characters_list.append(product.characters)
                for main_character_key, main_character_value in characters_list[0].items():
                    for character_key, character_value in main_character_value.items():
                        if all([product_characters[main_character_key][character_key] == characters_list[0][main_character_key][character_key]
                                for product_characters in characters_list]
                               ):
                            for product_characters in characters_list:
                                product_characters[main_character_key][character_key] = {
                                    "value": product_characters[main_character_key][character_key],
                                    "class": "comparis"
                                }
                        else:
                            for product_characters in characters_list:
                                product_characters[main_character_key][character_key] = {
                                    "value": product_characters[main_character_key][character_key],
                                    "class": ""
                                }
            else:
                context["match"] = False
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('product', False):
            product = Product.objects.get(id=request.POST.get('product'))
            comparison_service.remove_from_comparison_list(request=request, product=product)
        return redirect(request.path_info)


@staff_member_required
def import_products(request):
    """ View для импортирования товаров. """

    if request.method == 'POST':
        form = ProductImportForm(request.POST, request.FILES)
        context = {'form': form}
        if form.is_valid():
            json_files = request.FILES.getlist('json_file')
            for file in json_files:
                filepath = os.path.join(BASE_DIR, 'imports', 'waiting', str(file))
                result = make_an_products_importation.delay(filepath=filepath).get()
                context['success'] = 'True' if result else 'False'

            result = send_log_file_to_email.delay(dst_email=request.POST.get('email')).get()
            context['email_sent'] = 'True' if result else 'False'

        return render(request, 'products/import-products.html', context)
    else:
        form = ProductImportForm()
        return render(request, 'products/import-products.html', {'form': form})


def add_to_comparison_list(request, *args, **kwargs):
    product = Product.objects.get(id=request.GET.get('product'))
    comparison_service.add_to_comparison_list(request=request, product=product)
    return redirect(request.META.get('HTTP_REFERER'))


def remove_from_comparison_list(request, *args, **kwargs):
    product = Product.objects.get(id=request.GET.get('product'))
    comparison_service.remove_from_comparison_list(request=request, product=product)
    return redirect(request.META.get('HTTP_REFERER'))


def clear_comparison_list(request, *args, **kwargs):
    comparison_service.clear_comparison_list(request)
    return redirect(request.META.get('HTTP_REFERER'))
