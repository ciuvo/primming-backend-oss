# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import logging

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.views.generic import TemplateView

from primming.registration.forms import CrispyDynamicForm
from primming.registration.models import DynamicForm
from primming.registration.models import Person

log = logging.getLogger(__name__)


class RegistrationFormView(FormView):
    template_name = "registration/form.html"
    success_url = reverse_lazy("registration_success")
    form_class = CrispyDynamicForm

    def _prepare_view(self, **kwargs):
        self.uuid = kwargs["uuid"]
        if "form_name" in kwargs:
            self.dynamic_form = get_object_or_404(DynamicForm, name=kwargs["form_name"])
        else:
            self.dynamic_form = get_object_or_404(DynamicForm, default=True)

    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the form."""
        self._prepare_view(**kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle POST requests."""
        self._prepare_view(**kwargs)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.dynamic_form.display_name_or_name()
        return context

    def form_valid(self, form):
        """If the form is valid, redirect to the supplied URL."""
        try:
            Person.save_from_dynamic_form(self.dynamic_form, form, self.uuid)
        except (ValueError, ValidationError) as e:
            log.error("Form validation failed: %s", e)
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_initial(self):
        """load the initial data if the person exists"""
        data = super().get_initial()
        data.update(Person.load_data_for_dynamic_form(self.dynamic_form, self.uuid))
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["dynamic_form"] = DynamicForm.objects.filter(default=True).first()
        return kwargs


class RegistrationSuccessView(TemplateView):
    template_name = "registration/success.html"
