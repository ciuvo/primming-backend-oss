# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
from django.contrib import admin

from primming.admin import admin_site
from primming.registration.models import DataAttribute
from primming.registration.models import DataAttributeType
from primming.registration.models import DefaultValue
from primming.registration.models import DynamicForm
from primming.registration.models import FieldDefinition
from primming.registration.models import FieldDefinitionOrder
from primming.registration.models import FieldSetOrder
from primming.registration.models import FormFieldSet
from primming.registration.models import Person
from primming.registration.models import PersonalAttribute
from primming.registration.models import ValueMatch


class FormFieldSetInline(admin.TabularInline):
    model = FieldSetOrder
    extra = 1
    ordering = ["position"]


class DynamicFormAdmin(admin.ModelAdmin):
    inlines = [FormFieldSetInline]
    list_filter = ("default",)
    list_display = ("name", "default")
    search_fields = ("name",)


admin_site.register(DynamicForm, DynamicFormAdmin)


class FieldDefinitionInline(admin.TabularInline):
    model = FieldDefinitionOrder
    extra = 1
    ordering = ["row", "position"]
    fields = ("row", "position", "optional", "definition")


class FormFieldSetAdmin(admin.ModelAdmin):
    inlines = [FieldDefinitionInline]
    search_fields = ("name", "forms__name")
    list_display = ("name", "display_name")

    def form_name(self, obj):
        return obj.form.name


admin_site.register(FormFieldSet, FormFieldSetAdmin)


class DataAttributeInline(admin.TabularInline):
    model = DataAttribute
    extra = 0


class ValueMatchInline(admin.TabularInline):
    model = ValueMatch
    extra = 0


class FieldDefinitionAdmin(admin.ModelAdmin):
    inlines = [ValueMatchInline, DataAttributeInline]
    search_fields = ("name", "formfieldsets__name", "formfieldsets__form__name")
    list_display = ("id", "name", "display_name", "widget")

    def has_value_check(self, obj):
        return obj.allowed_values.count() > 0


admin_site.register(FieldDefinition, FieldDefinitionAdmin)


class PersonalAttributeInline(admin.TabularInline):
    model = PersonalAttribute
    extra = 0
    ordering = ["name"]
    readonly_fields = ("name", "value")
    fields = ("name", "value")


class PersonAdmin(admin.ModelAdmin):
    inlines = [PersonalAttributeInline]
    search_fields = ("uuid", "attributes__value_string", "created")
    list_display = ("uuid", "attributes", "created")
    readonly_fields = ("uuid", "created", "updated")

    def attributes(self, person):
        return ", ".join(
            ["{}: {}".format(attr.name, attr.value) for attr in person.attributes.all()]
        )


admin_site.register(Person, PersonAdmin)


class DataAttributeTypeAdmin(admin.ModelAdmin):

    list_display = ("name",)
    fields = ("name",)


admin_site.register(DataAttributeType, DataAttributeTypeAdmin)


class DefaultValueAdmin(admin.ModelAdmin):
    pass


admin_site.register(DefaultValue, DefaultValueAdmin)
