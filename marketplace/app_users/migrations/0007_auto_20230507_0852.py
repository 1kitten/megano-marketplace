# Generated by Django 3.2.18 on 2023-05-07 08:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_users", "0006_auto_20230423_0757"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="paymenttype",
            options={
                "verbose_name": "вид оплаты",
                "verbose_name_plural": "виды оплаты",
            },
        ),
        migrations.AlterField(
            model_name="paymenttype",
            name="title",
            field=models.CharField(max_length=100, verbose_name="вид оплаты"),
        ),
    ]
