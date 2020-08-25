# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

# Standard Library
import datetime
import logging

# Django
from django.http import (
    HttpResponseForbidden,
    HttpResponseRedirect
)
from django.shortcuts import (
    get_object_or_404,
    render
)
from django.urls import reverse
from django.utils.translation import ugettext_lazy
from django.views.generic import DeleteView

# wger
from wger.nutrition.models import (
    LogItem,
    Meal,
    NutritionPlan
)
from wger.utils.generic_views import (
    WgerDeleteMixin,
    WgerPermissionMixin
)


logger = logging.getLogger(__name__)


def overview(request, pk):
    """
    Shows an overview of diary entries for the given plan
    """

    # Check read permission
    plan = get_object_or_404(NutritionPlan, pk=pk)
    user = plan.user
    is_owner = request.user == user

    if not is_owner and not user.userprofile.ro_access:
        return HttpResponseForbidden()

    log_data = []
    planned_calories = plan.get_nutritional_values()['total']['energy']
    for item in plan.get_log_overview():
        log_data.append({'date': item['date'],
                         'planned_calories': planned_calories,
                         'logged_calories': item['energy'],
                         'difference': item['energy'] - planned_calories})

    context = {'plan': plan,
               'show_shariff': is_owner,
               'is_owner': is_owner,
               'log_data': log_data}

    return render(request, 'log/overview.html', context)


def detail(request, pk, year, month, day):
    """
    Shows an overview of the log for the given date
    """

    # Check read permission
    plan = get_object_or_404(NutritionPlan, pk=pk)
    user = plan.user
    is_owner = request.user == user

    if not is_owner and not user.userprofile.ro_access:
        return HttpResponseForbidden()

    try:
        date = datetime.date(year=int(year), month=int(month), day=int(day))
    except ValueError:
        date = datetime.date.today()
        return HttpResponseRedirect(reverse('nutrition:log:detail',
                                            kwargs={'pk': pk,
                                                    'year': date.year,
                                                    'month': date.month,
                                                    'day': date.day}))

    context = {'plan': plan,
               'date': date,
               'show_shariff': is_owner,
               'is_owner': is_owner,
               'log_summary': plan.get_log_summary(date),
               'log_entries': plan.get_log_entries(date),
               'nutritional_data': plan.get_nutritional_values()}

    return render(request, 'log/detail.html', context)


def log_meal(request, meal_pk):
    """
    Copy the requested meal item and logs its nutritional values
    """

    # Check read permission
    meal = get_object_or_404(Meal, pk=meal_pk)
    user = meal.plan.user
    is_owner = request.user == user
    date = datetime.date.today()

    if not is_owner and not user.userprofile.ro_access:
        return HttpResponseForbidden()

    for item in meal.mealitem_set.select_related():
        log_item = LogItem(plan=item.meal.plan,
                           ingredient=item.ingredient,
                           weight_unit=item.weight_unit,
                           amount=item.amount)
        log_item.save()

    return HttpResponseRedirect(reverse('nutrition:log:detail',
                                        kwargs={'pk': meal.plan.pk,
                                                'year': date.year,
                                                'month': date.month,
                                                'day': date.day
                                                }))


class LogDeleteView(WgerDeleteMixin, DeleteView, WgerPermissionMixin):
    """
    Delete a nutrition diary entry
    """
    model = LogItem
    title = ugettext_lazy('Delete?')
    form_action_urlname = 'nutrition:log:delete'
    login_required = True
    fields = ["comment", ]

    def get_success_url(self):
        """
        Return to the nutrition diary detail page
        """
        return reverse('nutrition:log:detail', kwargs={'pk': self.object.plan.pk,
                                                       'year': self.object.datetime.year,
                                                       'month': self.object.datetime.month,
                                                       'day': self.object.datetime.day})
