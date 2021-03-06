# Generated by Django 3.2.3 on 2021-06-14 14:56

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Browser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(db_index=True, max_length=50)),
                ("version", models.CharField(blank=True, db_index=True, max_length=20)),
            ],
            options={
                "unique_together": {("name", "version")},
            },
        ),
        migrations.CreateModel(
            name="Device",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(db_index=True, max_length=50)),
                ("brand", models.CharField(db_index=True, max_length=50)),
                ("version", models.CharField(blank=True, db_index=True, max_length=20)),
            ],
            options={
                "unique_together": {("name", "brand", "version")},
            },
        ),
        migrations.CreateModel(
            name="OperatingSystem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(db_index=True, max_length=50)),
                ("version", models.CharField(blank=True, db_index=True, max_length=20)),
            ],
            options={
                "unique_together": {("name", "version")},
            },
        ),
        migrations.CreateModel(
            name="Page",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=30, unique=True)),
                ("url", models.URLField()),
                ("enabled", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="UserAgent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "browser",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="pricewatcher.browser"
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="pricewatcher.device"
                    ),
                ),
                (
                    "os",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="pricewatcher.operatingsystem",
                    ),
                ),
            ],
            options={
                "unique_together": {("browser", "device", "os")},
            },
        ),
        migrations.CreateModel(
            name="PriceSample",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                ("price", models.IntegerField()),
                ("currency", models.CharField(max_length=3)),
                ("uuid", models.CharField(db_index=True, max_length=40)),
                (
                    "agent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="pricewatcher.useragent",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="pricewatcher.page"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PageList",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=30, unique=True)),
                (
                    "default",
                    models.BooleanField(blank=True, default=False, null=True, unique=True),
                ),
                ("pages", models.ManyToManyField(related_name="lists", to="pricewatcher.Page")),
            ],
        ),
    ]
