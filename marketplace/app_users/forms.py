import re

from django.core.exceptions import ValidationError

from app_merch.models import Image
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm, UserChangeForm,
                                       UserCreationForm)
from django.contrib.auth.models import User
from django.forms.widgets import FileInput

from .models import Profile


class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "ФИО"}),
    )
    phone_number = forms.CharField(
        max_length=50,
        required=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "Телефон"}),
    )
    address = forms.CharField(
        max_length=255,
        required=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "Адрес"}),
    )
    avatar = forms.FileField(widget=FileInput(attrs={'hidden': '1'}), required=False, label="Аватар")

    password1 = forms.CharField(
        label="",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Пароль",
                "minlength": 8,
            }
        ),
        help_text="Пароль должен содержать не менее 8 символов и быть сложным",
    )
    password2 = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Подтверждение пароля",
                "minlength": 8,
            }
        ),
        help_text="Введите пароль еще раз для подтверждения",
    )
    username = forms.CharField(
        max_length=50,
        required=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "Логин"}),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "full_name",
            "phone_number",
            "address",
            "avatar",
        ]
        labels = {
            "username": "Имя пользователя",
            "email": "",
        }
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "E-mail"}),
        }


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254, required=True, label="",
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '********'}), required=True, label=""
    )

    class Meta:
        model = User
        fields = ["username", "password"]
        labels = {
            "username": "Имя пользователя",
            "password": "Пароль",
        }


class UserPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254, required=True, label="Email")

    class Meta:
        model = User
        fields = ["email"]
        labels = {
            "email": "Email",
        }


class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput, required=True, label="Новый пароль"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput, required=True, label="Подтверждение нового пароля"
    )

    class Meta:
        model = User
        fields = ["new_password1", "new_password2"]
        labels = {
            "new_password1": "Новый пароль",
            "new_password2": "Подтверждение нового пароля",
        }


class UserUpdateForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email",)
        widgets = {
            "email": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "id": "mail",
                    "name": "mail",
                    "data-validate": "require",
                }
            ),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "full_name",
            "phone_number",
        )
        widgets = {
            "phone_number": forms.TextInput(
                attrs={"class": "form-input", "id": "phone", "name": "phone", 'placeholder': '+7(___) ___-____'}
            ),
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "id": "name",
                    "name": "name",
                    "data-validate": "require",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__( *args, **kwargs)

    def clean_phone(self):
        phone = self.cleaned_data.get("phone_number")
        if not re.findall(r"^(\(\d{3}\)\s?\d{3}-\d{4})$", phone):
            raise ValidationError("Номер телефона должен иметь формат (000) 000-0000")
        return


class UpdatePasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "id": "password",
                "name": "password",
                "placeholder": "Тут можно изменить пароль",
            }
        ),
        strip=False,
    )
    new_password2 = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "id": "passwordReply",
                "name": "passwordReply",
                "placeholder": "Введите пароль повторно",
            }
        ),
    )


class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = "__all__"
        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "class": "Profile-file form-input",
                    "id": "avatar",
                    "name": "avatar",
                    "data-validate": "onlyImgAvatar",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(AvatarUpdateForm, self).__init__(*args, **kwargs)
        self.fields["file"].required = False
        self.fields["title"].required = False

    def clean_file(self):
        file = self.cleaned_data.get("file", False)
        if file:
            if file.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Размер файла не должен превышать 2 МБ")
            return file
        else:
            raise forms.ValidationError("Не удалось загрузить файл")

    def save(self, username, commit=True):
        instance = super().save(commit=False)
        instance.file.title = f"Аватар {username}"
        if commit:
            instance.save()
        return instance
