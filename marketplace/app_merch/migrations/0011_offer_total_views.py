# Generated by Django 3.2.18 on 2023-03-31 06:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app_merch", "0010_auto_20230327_1732"),
    ]

    operations = [
        migrations.AddField(
            model_name="offer",
            name="total_views",
            field=models.PositiveIntegerField(
                default=0, verbose_name="количество просмотров"
            ),
        ),
    ]
