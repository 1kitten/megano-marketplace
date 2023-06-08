import re

from django import forms
from django.core.validators import ValidationError

from .models import Offer, Review


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[('', '---')] + [(str(i), str(i)) for i in range(1, 6)],
        widget=forms.Select(attrs={"class": "rating"}),
        label="Рейтинг",
    )

    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.Select(attrs={"class": "rating", "placeholder": "Выберите рейтинг"}),
            "text": forms.Textarea(attrs={"rows": 5}),
        }


class OrderUserDataForm(forms.Form):
    """Форма для первого шага оформления заказа."""

    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input"}),
        label="ФИО",
        error_messages={"required": 'Поле "ФИО" обязательно для заполнения'},
    )
    phone = forms.CharField(required=True, widget=forms.TextInput(
        attrs={
            'class': 'form-input',
            'placeholder': '+7(___) ___-____'
        }),
        label='Телефон',
        error_messages={
            'invalid': 'Введите корректный Телефон',
            'required': 'Поле "Телефон" обязательно для заполнения'
        }
    )
    mail = forms.EmailField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-input'}),
        label='E-mail',
        error_messages={
            'invalid': 'Введите корректный E-mail',
            'required': 'Поле "E-mail" обязательно для заполнения'
        }
    )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not re.findall(r"^(\(\d{3}\)\s?\d{3}-\d{4})$", phone):
            raise ValidationError("Номер телефона должен иметь формат (000) 000-0000")
        return

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if not self.request:
            return

        self.user_data = self.request.session.get("user_data")
        if self.request.user.is_authenticated:
            name = (
                self.user_data.get("name")[0]
                if self.user_data
                else self.request.user.profile.full_name
            )
            phone = (
                self.user_data.get("phone")[0]
                if self.user_data
                else self.request.user.profile.phone_number
            )
            mail = (
                self.user_data.get("mail")[0]
                if self.user_data
                else self.request.user.email
            )

            self.fields["name"].initial = name
            self.fields["phone"].initial = phone
            self.fields["mail"].initial = mail


class OrderDeliveryDataForm(forms.Form):
    """Форма для второго шага оформления заказа."""

    city = forms.CharField(max_length=100, required=True, widget=forms.TextInput(
        attrs={
            'class': 'form-input',
            'data-validate': 'require'
        }),
        label='Город',
        error_messages={
            'required': 'Поле "Город" обязательно для заполнения'
        }
    )
    address = forms.CharField(max_length=500, required=True, widget=forms.Textarea(
        attrs={
            'class': 'form-textarea',
            'data-validate': 'require'
        }),
        label='Адрес',
        error_messages={
            'required': 'Поле "Адрес" обязательно для заполнения'
        }
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if not self.request:
            return

        self.delivery_data = self.request.session.get("user_data")
        if self.delivery_data:
            self.delivery_data = self.delivery_data.get("delivery_data")

        if self.delivery_data:
            city = self.delivery_data.get("city")[0] if self.delivery_data else ""
            address = self.delivery_data.get("address")[0] if self.delivery_data else ""

            self.fields['city'].initial = city
            self.fields['address'].initial = address


class PaymentForm(forms.Form):
    """ Форма ввода номера карты для оплаты заказа. """

    numerol = forms.CharField(max_length=9, required=True, widget=forms.TextInput(
        attrs={
            'class': 'form-input Payment-bill',
            'data-validate': 'require pay',
            'placeholder': '9999 9999',
            'data-mask': '9999 9999'
        }),
        label='Номер счёта',
        error_messages={
            'required': 'Это поле обязательно для заполнения.',
            'invalid': 'Номер карты состоит из 8 цифр.'
        }
    )


class ProductImportForm(forms.Form):
    """ Форма загрузки csv файла импорта товаров. """

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'E-mail'}), label=''
    )
    json_file = forms.FileField(
        label='', widget=forms.ClearableFileInput(attrs={"multiple": True, "class": "Import-form-file-input"})
    )
