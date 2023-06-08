from app_basket.models import Cart, CartItem
from app_merch.models import Offer
from app_merch.viewed_products import watched_products_service
from app_settings.models import SiteSettings
from .forms import (AvatarUpdateForm, ProfileUpdateForm,
                    UpdatePasswordForm, UserLoginForm,
                    UserPasswordResetForm, UserRegisterForm,
                    UserSetPasswordForm, UserUpdateForm)
from app_users.models import Order, OrderItem, Seller
from django.contrib.auth import login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView, PasswordResetCompleteView)
from django.core.cache import cache
from django.db.models import F, Min, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DetailView, ListView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import views as auth_views
from django.contrib import messages
from sql_util.aggregates import SubquerySum
from django.contrib.sites.shortcuts import get_current_site
from .models import Buyer, Profile


class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("pages:index")

    def form_valid(self, form):
        username = form.get_user()
        cart_id = self.request.session.get("cart_id")
        cart_username = Cart.objects.filter(
            buyer__profile__user__username=username
        ).first()
        if not cart_username:
            Cart.objects.filter(id=int(cart_id)).update(
                buyer=Buyer.objects.create(
                    profile=Profile.objects.get(user__username=username)
                )
            )
        if cart_username:
            cartitems_anonymoususer = CartItem.objects.filter(cart=int(cart_id))
            cartitems_username = CartItem.objects.filter(cart=cart_username.id)
            cartitems_username_offer_ids_list = [
                cartitem.offer.id for cartitem in cartitems_username
            ]
            for cartitem in cartitems_anonymoususer:
                if cartitem.offer.id not in cartitems_username_offer_ids_list:
                    cartitem.cart = cart_username
                    cartitem.save()

        auth_login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("app_users:login")


class CustomPasswordResetView(PasswordResetView):
    form_class = UserPasswordResetForm
    template_name = "users/password_reset.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("app_users:password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.filter(email=email).first()
        if user is not None:
            current_site = get_current_site(self.request)
            subject = 'Password Reset Requested'
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = self.request.build_absolute_uri(
                reverse('app_users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            message = render_to_string('users/password_reset_email.html', {
                'user': user,
                'domain': current_site.domain,
                'reset_url': reset_url,
            })
            send_mail(subject, message, 'your_email@mail.ru', [email])

        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = UserSetPasswordForm
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("app_users:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


class CustomRegisterView(CreateView):
    model = Profile
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("pages:index-page")

    def form_valid(self, form):
        user = form.save()
        Profile.objects.create(
            user=user,
            full_name=form.cleaned_data.get("full_name"),
            phone_number=form.cleaned_data.get("phone_number"),
            address=form.cleaned_data.get("address"),
            avatar=form.cleaned_data.get("avatar"),
        )
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        user_data = self.request.session.get('user_register_data')
        if user_data:
            initial['full_name'] = user_data['name'][0]
            initial['phone_number'] = user_data['phone'][0]
            initial['email'] = user_data['mail'][0]
            initial['password1'] = user_data['password'][0]
            initial['password2'] = user_data['passwordReply'][0]
        return initial


class SellerView(DetailView):
    model = Seller
    template_name = "seller.html"
    context_object_name = "seller"

    def get_object(self, queryset=None):
        time_to_cache = SiteSettings.load().time_to_cache
        if not time_to_cache:
            time_to_cache = 1

        return cache.get_or_set(
            f"Seller {self.kwargs.get('pk')}",
            super(SellerView, self).get_object(queryset=None),
            time_to_cache * 60 * 60 * 24,
        )

    def get_context_data(self, **kwargs):
        context = super(SellerView, self).get_context_data(**kwargs)
        top_seller_products_cache_time = (
            SiteSettings.load().top_seller_products_cache_time
        )

        if not top_seller_products_cache_time:
            top_seller_products_cache_time = 1
        context["offers"] = cache.get_or_set(
            f"Seller {kwargs.get('pk')} top products",
            Offer.objects.filter(seller=self.get_object())
            .annotate(sales=Sum("order_items__quantity"))
            .order_by("-sales")[:10],
            top_seller_products_cache_time * 60 * 60,
        )
        return context


class AccountView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/account.html"
    context_object_name = "user"
    slug_url_kwarg = "username"
    slug_field = "username"

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        last_order = (
            Order.objects.filter(buyer=self.request.user.profile.buyer)
            .order_by("order_date")
            .last()
        )
        if last_order:
            context["last_order"] = last_order
            context["last_order_cost"] = sum(
                item.offer.price * item.quantity
                for item in OrderItem.objects.filter(order=last_order)
            )
        watched_products = watched_products_service.get_watched_products(
            user=self.request.user, count=3
        ).annotate(min_price=Min("product__offers__price"))
        context["watched_products"] = watched_products
        return context


class ProfileEditView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "users/profile.html"
    context_object_name = "user_form"
    slug_url_kwarg = "username"
    slug_field = "username"

    def get_context_data(self, **kwargs):
        context = super(ProfileEditView, self).get_context_data(**kwargs)
        context["profile_form"] = ProfileUpdateForm(instance=self.request.user.profile)
        context["user_form"] = UserUpdateForm(instance=self.request.user)
        context["password_form"] = UpdatePasswordForm(self.request.user)
        context["avatar_form"] = AvatarUpdateForm()
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if not request.POST["new_password1"] == request.POST["new_password1"] == "":
            password_form = UpdatePasswordForm(request.user, request.POST)
        else:
            password_form = UpdatePasswordForm(request.user)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save()
            avatar_form = AvatarUpdateForm(request.POST, request.FILES)
            if avatar_form.is_valid():
                avatar = avatar_form.save(username=request.user.username)
                profile.avatar = avatar
                profile.save()
            if password_form.is_valid():
                user = password_form.save()
                auth_login(request, user)
            return redirect("app_users:profile_edit", kwargs.get("username"))
        context = {
            "user_form": user_form,
            "profile_form": profile_form,
            "password_form": UpdatePasswordForm(request.user),
        }
        return render(request, "users/profile.html", context)


class OrdersHistoryView(LoginRequiredMixin, ListView):
    model = Order
    context_object_name = "orders"
    template_name = "users/historyorder.html"
    ordering = "-order_date"

    def get_queryset(self):
        queryset = super(OrdersHistoryView, self).get_queryset()
        queryset = queryset.filter(buyer=self.request.user.profile.buyer).annotate(
            price=Sum(F("order_items__offer__price") * F("order_items__quantity"))
        )
        return queryset


class ViewsHistoryView(LoginRequiredMixin, DetailView):
    model = User
    context_object_name = "buyer"
    template_name = "users/historyview.html"
    slug_url_kwarg = "username"
    slug_field = "username"

    def get_context_data(self, **kwargs):
        context = super(ViewsHistoryView, self).get_context_data(**kwargs)
        watched_products = watched_products_service.get_watched_products(
            user=self.request.user
        ).annotate(min_price=Min("product__offers__price"))
        context["watched_products"] = watched_products
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    context_object_name = "order"
    template_name = "users/oneorder.html"

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context["order_items"] = OrderItem.objects.filter(
            order=self.get_object()
        ).annotate(price=F("offer__price") * F("quantity"))
        context["order_cost"] = sum(
            item.offer.price * item.quantity
            for item in OrderItem.objects.filter(order=self.get_object())
        )
        return context
