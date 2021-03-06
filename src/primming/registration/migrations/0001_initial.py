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
            name="DataAttributeType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True, help_text="Name of the data-**** attribute", max_length=100
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DynamicForm",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "display_name",
                    models.CharField(
                        blank=True,
                        help_text="Name used to render the form, if blank `name` will be used instead.",
                        max_length=100,
                        null=True,
                    ),
                ),
                ("default", models.BooleanField(default=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="FieldDefinition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        help_text="Internal name for the field, e.g. 'age'",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "widget",
                    models.SmallIntegerField(
                        choices=[
                            (0, "Auto"),
                            (1, "Radio Buttons"),
                            (2, "Conditional Multi Field"),
                            (3, "Multiple Choice"),
                        ],
                        default=0,
                        help_text="how to render the field",
                    ),
                ),
                (
                    "display_name",
                    models.CharField(
                        blank=True,
                        help_text="Name used to render the form, if blank `name` will be used instead.",
                        max_length=200,
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FieldSetOrder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "position",
                    models.SmallIntegerField(
                        default=0, help_text="the position of thefieldset in the form"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Person",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("uuid", models.CharField(max_length=40, unique=True)),
                (
                    "created",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                (
                    "updated",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ValueMatch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "value_type",
                    models.SmallIntegerField(
                        choices=[
                            (1, "Boolean"),
                            (2, "Integer"),
                            (3, "Float"),
                            (4, "String"),
                            (5, "EMail"),
                        ],
                        db_index=True,
                        default=2,
                    ),
                ),
                (
                    "value_bool",
                    models.BooleanField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_int",
                    models.IntegerField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_float",
                    models.FloatField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_string",
                    models.CharField(
                        blank=True, db_index=True, default=None, max_length=255, null=True
                    ),
                ),
                (
                    "value_max",
                    models.IntegerField(
                        blank=True,
                        default=None,
                        help_text="If the type of the value is a float or integer then this is the maximum value.If it is a string, then it is the maximum length. Ignored for boolean types.",
                        null=True,
                    ),
                ),
                (
                    "value_min",
                    models.IntegerField(
                        blank=True,
                        default=None,
                        help_text="If the type of the value is a float or integer then this is the minimum value.If it is a string, then it is the minimum length. Ignored for boolean types.",
                        null=True,
                    ),
                ),
                (
                    "display_name",
                    models.CharField(
                        blank=True,
                        help_text="Name used to render the field value (e.g. in a select box)",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allowed_values",
                        to="registration.fielddefinition",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="FormFieldSet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "display_name",
                    models.CharField(
                        blank=True,
                        help_text="Name used to render the form, if blank `name` will be used instead.",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "forms",
                    models.ManyToManyField(
                        related_name="fieldsets",
                        through="registration.FieldSetOrder",
                        to="registration.DynamicForm",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="fieldsetorder",
            name="fieldset",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="registration.formfieldset"
            ),
        ),
        migrations.AddField(
            model_name="fieldsetorder",
            name="form",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="registration.dynamicform"
            ),
        ),
        migrations.CreateModel(
            name="FieldDefinitionOrder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "position",
                    models.SmallIntegerField(
                        default=0, help_text="the position of thefield in the row"
                    ),
                ),
                (
                    "row",
                    models.SmallIntegerField(
                        default=0,
                        help_text="the row number of witch to render thefield in. Null means it's own row each",
                        null=True,
                    ),
                ),
                (
                    "optional",
                    models.BooleanField(
                        default=False,
                        help_text="If the field is requiredto be filled in by formsrendered with this attribute definition",
                    ),
                ),
                (
                    "definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.fielddefinition",
                    ),
                ),
                (
                    "fieldset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="registration.formfieldset"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="fielddefinition",
            name="fieldsets",
            field=models.ManyToManyField(
                through="registration.FieldDefinitionOrder", to="registration.FormFieldSet"
            ),
        ),
        migrations.CreateModel(
            name="DefaultValue",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "value_type",
                    models.SmallIntegerField(
                        choices=[
                            (1, "Boolean"),
                            (2, "Integer"),
                            (3, "Float"),
                            (4, "String"),
                            (5, "EMail"),
                        ],
                        db_index=True,
                        default=2,
                    ),
                ),
                (
                    "value_bool",
                    models.BooleanField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_int",
                    models.IntegerField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_float",
                    models.FloatField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_string",
                    models.CharField(
                        blank=True, db_index=True, default=None, max_length=255, null=True
                    ),
                ),
                (
                    "value_max",
                    models.IntegerField(
                        blank=True,
                        default=None,
                        help_text="If the type of the value is a float or integer then this is the maximum value.If it is a string, then it is the maximum length. Ignored for boolean types.",
                        null=True,
                    ),
                ),
                (
                    "value_min",
                    models.IntegerField(
                        blank=True,
                        default=None,
                        help_text="If the type of the value is a float or integer then this is the minimum value.If it is a string, then it is the minimum length. Ignored for boolean types.",
                        null=True,
                    ),
                ),
                (
                    "field_definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.fielddefinition",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="DataAttribute",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "value",
                    models.CharField(
                        db_index=True, help_text="Name of the HTML class", max_length=100
                    ),
                ),
                (
                    "field_definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.fielddefinition",
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.dataattributetype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PersonalAttribute",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "value_type",
                    models.SmallIntegerField(
                        choices=[
                            (1, "Boolean"),
                            (2, "Integer"),
                            (3, "Float"),
                            (4, "String"),
                            (5, "EMail"),
                        ],
                        db_index=True,
                        default=2,
                    ),
                ),
                (
                    "value_bool",
                    models.BooleanField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_int",
                    models.IntegerField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_float",
                    models.FloatField(blank=True, db_index=True, default=None, null=True),
                ),
                (
                    "value_string",
                    models.CharField(
                        blank=True, db_index=True, default=None, max_length=255, null=True
                    ),
                ),
                (
                    "value_max",
                    models.IntegerField(
                        blank=True,
                        default=None,
                        help_text="If the type of the value is a float or integer then this is the maximum value.If it is a string, then it is the maximum length. Ignored for boolean types.",
                        null=True,
                    ),
                ),
                (
                    "value_min",
                    models.IntegerField(
                        blank=True,
                        default=None,
                        help_text="If the type of the value is a float or integer then this is the minimum value.If it is a string, then it is the minimum length. Ignored for boolean types.",
                        null=True,
                    ),
                ),
                ("name", models.CharField(db_index=True, max_length=100)),
                (
                    "created",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                (
                    "updated",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                (
                    "position",
                    models.IntegerField(
                        db_index=True,
                        default=0,
                        help_text="for multi-value fields,the position within",
                    ),
                ),
                (
                    "person",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attributes",
                        to="registration.person",
                    ),
                ),
            ],
            options={
                "unique_together": {("name", "person", "position")},
            },
        ),
    ]
