# Generated by Django 3.2.18 on 2023-03-27 17:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_merch", "0009_review"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="offer",
            options={
                "ordering": ["price"],
                "verbose_name": "Предложение",
                "verbose_name_plural": "Предложения",
            },
        ),
        migrations.AddField(
            model_name="offer",
            name="is_delivery_free",
            field=models.BooleanField(
                default=False, verbose_name="бесплатная доставка"
            ),
        ),
    ]
