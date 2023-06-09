# Generated by Django 3.2.18 on 2023-05-04 19:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_users", "0008_auto_20230504_1843"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="order_status",
            field=models.CharField(
                choices=[("delivered", "Доставлен"), ("is_delivering", "Доставляется")],
                max_length=20,
                null=True,
                verbose_name="статус доставки",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="payment",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="orders",
                to="app_users.payment",
                verbose_name="тип оплаты",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[("paid", "Оплачен"), ("not_paid", "Не оплачен")],
                max_length=20,
                verbose_name="статус оплаты",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="credit_card",
            field=models.CharField(max_length=8, null=True, verbose_name="номер счета"),
        ),
    ]
