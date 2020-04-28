from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from genesishealth.apps.utils.request import (
    patient_user, professional_or_patient_user, professional_user)
from genesishealth.apps.reports.views.main import aggregate_readings
from genesishealth.apps.accounts.models import ProfessionalProfile
from genesishealth.apps.utils.func import utcnow


class DashboardView(TemplateView):
    is_public = False
    template_name = 'dashboard_base.html'

    def get_context_data(self, **kwargs):
        data = super(DashboardView, self).get_context_data(**kwargs)
        data['is_public'] = self.is_public
        return data


public = DashboardView.as_view(is_public=True)
index = login_required(DashboardView.as_view(is_public=False))


@csrf_exempt
@login_required
@user_passes_test(professional_or_patient_user)
def home(request):
    if request.user.is_patient():
        return patient_home(request)
    else:
        return caregiver_home(request)


@login_required
@user_passes_test(patient_user)
def patient_home(request):
    c = {}
    last_three_readings = request.user.glucose_readings.order_by(
        '-reading_datetime_utc')
    if last_three_readings.count() > 3:
        last_three_readings = last_three_readings[:3]
    c['last_three_readings'] = last_three_readings
    last_fourteen_day_readings = request.user.glucose_readings.filter(
        reading_datetime_utc__gte=utcnow() - timedelta(days=14))
    c['aggregates'] = aggregate_readings(
        request.user, last_fourteen_day_readings, days=14)
    last_reading = request.user.patient_profile.get_last_reading()
    if not last_reading:
        c['reading_status'] = 'no_readings'
    elif (last_reading.reading_datetime_utc + timedelta(days=14)) < utcnow():
        c['reading_status'] = 'outdated'
    else:
        c['reading_status'] = 'ok'

    c['number_of_logins_last_six_months'] = request.user.patient_profile\
        .logins_since(utcnow() - relativedelta(months=6)).count()

    return render(request, 'dashboard/patient_home.html', c)


@csrf_exempt
@login_required
@user_passes_test(professional_user)
def caregiver_home(request):
    c = {}
    c['out_of_range_patients'] = request.user.professional_profile\
        .get_out_of_range_patients()
    c['out_of_compliance_patients'] = request.user.professional_profile\
        .get_out_of_compliance_patients()

    return render(request, 'dashboard/professional_caregiver_home.html', c)


@csrf_exempt
@user_passes_test(professional_user)
def professional_admin_home(request):
    # AND them together so we only get the ones in both sets.
    logged_in_users = (
        ProfessionalProfile.get_logged_in_users() &
        request.user.professional_profile.parent_group.get_professionals())

    devices_in_need_of_attention = 0
    c = {
        'logged_in_users': logged_in_users,
        'devices_in_need_of_attention': devices_in_need_of_attention
    }

    return render(request, 'dashboard/professional_admin_home.html', c)
