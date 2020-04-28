import json
from time import mktime
from datetime import time, datetime, timedelta
import pytz

from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.urls import reverse

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.readings.models import (
    GlucoseReading, GlucoseReadingNote)
from genesishealth.apps.reports.forms import (
    ReportForm, DisplayLogbookForm, GlucoseReadingEntryForm)
from genesishealth.apps.reports.misc import (
    LogbookDay)
from genesishealth.apps.utils.request import professional_user, debug_response
from genesishealth.apps.utils.func import convert_date_to_utc_datetime, utcnow


@login_required
def logbook(request):
    try:
        form = DisplayLogbookForm(request.GET)
        assert form.is_valid(), repr(form.errors)
        data = form.cleaned_data

        patient = data.get('patient')
        if request.user.is_patient():
            assert request.user == patient
        elif request.user.is_professional():
            assert patient in request.user.professional_profile.get_patients()

    except AssertionError as e:
        return debug_response(e)

    days = LogbookDay.generate_logbook_days(**data)

    return render(
        request,
        'reports/logbook/day.json',
        {'days': days, 'timezone': patient.patient_profile.timezone_name},
        content_type='application/javascript'
    )


@login_required
def logbook_entry(request, entry_id):
    try:
        instance = GlucoseReading.objects.get(pk=entry_id)
    except GlucoseReading.DoesNotExist as e:
        return debug_response(e)

    form = GlucoseReadingEntryForm(
        requester=request.user, instance=instance)

    form_url = reverse('reports:ajax-logbook-entry-update',
                       kwargs={'entry_id': entry_id})

    return render(request, 'reports/logbook/entry.html',
                  {'instance': instance, 'form': form, 'form_url': form_url})


@require_POST
@login_required
def logbook_entry_update(request, entry_id):
    try:
        instance = GlucoseReading.objects.get(pk=entry_id)
    except GlucoseReading.DoesNotExist as e:
        return debug_response(e)

    form = GlucoseReadingEntryForm(
        request.POST, instance=instance, requester=request.user)
    success = form.is_valid()
    c = {'success': success}
    if success:
        form.save()
    else:
        c['errors'] = form.errors
    return HttpResponse(json.dumps(c), content_type='application/json')


@require_POST
@login_required
def logbook_get_notes_for_period(request):
    try:
        for i in ('start_time', 'end_time', 'patient_id'):
            assert request.POST.get(i)
        patient_id = int(request.POST.get('patient_id'))
        if request.user.is_admin():
            patient = PatientProfile.myghr_patients.get_users().get(
                pk=patient_id)
        elif request.user.is_professional():
            patient = request.user.get_profile().get_patients().get(
                pk=patient_id)
        else:
            assert request.user.pk == patient_id
            patient = request.user
    except (AssertionError, User.DoesNotExist) as e:
        return debug_response(e)

    format = "%Y-%m-%d %I:%M %p"
    timezone = patient.patient_profile.timezone
    local_start_datetime = timezone.localize(datetime.strptime(
        request.POST.get('start_time'), format))
    local_end_datetime = timezone.localize(datetime.strptime(
        request.POST.get('end_time'), format))

    start_datetime = local_start_datetime.astimezone(pytz.utc)
    end_datetime = local_end_datetime.astimezone(pytz.utc)
    entries = patient.glucose_readings.filter(
        reading_datetime_utc__range=(start_datetime, end_datetime))
    notes = GlucoseReadingNote.objects.filter(entry__in=entries)

    return render(request, 'reports/logbook/notes.html', {'notes': notes})


@login_required
def test_history_data(request, patient_id):
    try:
        if request.user.is_professional():
            patient = request.user.professional_profile.get_patients().get(
                pk=patient_id)
        elif request.user.is_patient():
            assert request.user.id == int(patient_id)
            patient = request.user
        else:
            patient = PatientProfile.myghr_patients.get_users().get(
                pk=patient_id)
    except (AssertionError, User.DoesNotExist) as e:
        return debug_response(e)

    form = ReportForm(request.GET)
    if not form.is_valid():
        return HttpResponse(status=500)
    timezone = patient.patient_profile.timezone
    local_start_datetime = timezone.localize(datetime.combine(
        form.get_date("start_date"), time()))
    local_end_datetime = timezone.localize(datetime.combine(
        form.get_date("end_date"), time())).astimezone(pytz.utc)
    # Offset it to get all readings for that day
    local_end_datetime += (timedelta(days=1) - timedelta(microseconds=1))

    start_datetime = local_start_datetime.astimezone(pytz.utc)
    end_datetime = local_end_datetime.astimezone(pytz.utc)

    readings = GlucoseReading.objects.filter(
        patient=patient,
        reading_datetime_utc__range=[start_datetime, end_datetime])
    readings = readings.exclude(measure_type="TEST mode").order_by(
        "reading_datetime_utc")

    if form.cleaned_data.get('type') == ReportForm.REPORT_TYPE_CHOICE_PREMEAL:
        readings = readings.filter(
            measure_type=GlucoseReading.MEASURE_TYPE_BEFORE)
        glucose_goal = (
            patient.healthinformation.safe_zone_minimum,
            patient.healthinformation.premeal_glucose_goal_minimum,
            patient.healthinformation.premeal_glucose_goal_maximum,
            patient.healthinformation.safe_zone_maximum)
    elif (form.cleaned_data.get('type') ==
            ReportForm.REPORT_TYPE_CHOICE_POSTMEAL):
        readings = readings.filter(
            measure_type=GlucoseReading.MEASURE_TYPE_AFTER)
        glucose_goal = (
            patient.healthinformation.safe_zone_minimum,
            patient.healthinformation.postmeal_glucose_goal_minimum,
            patient.healthinformation.postmeal_glucose_goal_maximum,
            patient.healthinformation.safe_zone_maximum)
    else:
        glucose_goal = (
            patient.healthinformation.safe_zone_minimum,
            patient.healthinformation.premeal_glucose_goal_minimum,
            patient.healthinformation.postmeal_glucose_goal_maximum,
            patient.healthinformation.safe_zone_maximum)

    chart_data = {
        "readings": [],
        "glucose_goal": glucose_goal,
        "patient_name": patient.get_full_name(),
        "date_range": "%s - %s" % (
            local_start_datetime.strftime('%m/%d/%y'),
            (local_end_datetime - timedelta(days=1)).strftime('%m/%d/%y'))
    }
    dates = [(start_datetime + timedelta(days=i)) for i
             in range((end_datetime - start_datetime).days)]
    # If viewing another report, send along the viewer's name.
    if request.user.is_professional():
        name = request.user.get_full_name()
        if request.user.professional_profile.parent_group:
            name += ' from %s' % request.user.professional_profile.parent_group
        name += ' (User: %s' % request.user.username
        chart_data['professional_name'] = name

    for r in readings:
        chart_data["readings"].append({
            "name": "Glucose value",
            "datetime": r.reading_datetime.strftime("%m/%d %I:%M %p"),
            "y": r.glucose_value,
            'x': int(mktime(r.reading_datetime.timetuple())) * 1000
        })

    for d in dates:
        chart_data['readings'].append({
            'name': None,
            'datetime': d.strftime("%m/%d %I:%M %p"),
            "y": None,
            "x": int(mktime(d.timetuple())) * 1000
        })

    return HttpResponse(json.dumps(chart_data),
                        content_type="application/json")


@login_required
def trend_report_average_data(request, patient_id):
    try:
        if request.user.is_professional():
            patient = request.user.professional_profile.get_patients().get(
                pk=patient_id)
        elif request.user.is_patient():
            assert request.user.id == int(patient_id)
            patient = request.user
        else:
            patient = PatientProfile.myghr_patients.get_users().get(
                pk=patient_id)
    except (AssertionError, User.DoesNotExist) as e:
        return debug_response(e)

    form = ReportForm(request.GET)
    if not form.is_valid():
        return HttpResponse(repr(form.errors), status=500)
    timezone = patient.patient_profile.timezone
    local_start_datetime = timezone.localize(datetime.combine(
        form.get_date("start_date"), time()))
    local_end_datetime = timezone.localize(datetime.combine(
        form.get_date("end_date"), time())).astimezone(pytz.utc)
    # Offset it to get all readings for that day
    local_end_datetime += (timedelta(days=1) - timedelta(microseconds=1))

    start_datetime = local_start_datetime.astimezone(pytz.utc)
    end_datetime = local_end_datetime.astimezone(pytz.utc)
    readings = GlucoseReading.objects.filter(
        patient=patient,
        reading_datetime_utc__range=[start_datetime, end_datetime])
    readings = readings.exclude(measure_type="TEST mode").order_by(
        "reading_datetime_utc")
    if form.cleaned_data.get('type') == 'premeal':
        readings = readings.filter(
            measure_type=GlucoseReading.MEASURE_TYPE_BEFORE)
        glucose_goal = (
            patient.healthinformation.premeal_glucose_goal_minimum,
            patient.healthinformation.premeal_glucose_goal_maximum)
    elif form.cleaned_data.get('type') == 'postmeal':
        readings = readings.filter(
            measure_type=GlucoseReading.MEASURE_TYPE_AFTER)
        glucose_goal = (
            patient.healthinformation.postmeal_glucose_goal_minimum,
            patient.healthinformation.postmeal_glucose_goal_maximum)
    else:
        glucose_goal = (
            patient.healthinformation.premeal_glucose_goal_minimum,
            patient.healthinformation.postmeal_glucose_goal_maximum)
    total_readings = readings.count()
    bottom, top = glucose_goal

    chart_data = {
        "above_count": 0,
        "below_count": 0,
        "within_count": 0,
        "hypo_count": 0,
        "hyper_count": 0,
        "glucose_goal": "%s-%s" % (bottom, top),
        "patient_name": patient.get_full_name(),
        "date_range": "%s - %s" % (
            local_start_datetime.strftime('%m/%d/%y'),
            (local_end_datetime - timedelta(days=1)).strftime('%m/%d/%y'))
    }
    # If viewing another report, send along the viewer's name.
    if request.user.is_professional():
        chart_data['professional_name'] = '%s (%s) (User: %s)' % (
            request.user.get_full_name(),
            request.user.professional_profile.parent_group,
            request.user.username)

    for r in readings:
        if r.glucose_value > top:
            chart_data["above_count"] += 1
            if r.glucose_value > patient.healthinformation.safe_zone_maximum:
                chart_data['hyper_count'] += 1
        elif r.glucose_value < bottom:
            chart_data["below_count"] += 1
            if r.glucose_value < patient.healthinformation.safe_zone_minimum:
                chart_data['hypo_count'] += 1
        elif bottom <= r.glucose_value <= top:
            chart_data["within_count"] += 1

    chart_data["above_percentage"] = "%.2f" % (total_readings != 0 and ((
        float(chart_data["above_count"]) / float(total_readings)) * 100) or 0)
    chart_data["below_percentage"] = "%.2f" % (total_readings != 0 and ((
        float(chart_data["below_count"]) / float(total_readings)) * 100) or 0)
    chart_data["within_percentage"] = "%.2f" % (total_readings != 0 and ((
        float(chart_data["within_count"]) / float(total_readings)) * 100) or 0)
    chart_data['hypo_percentage'] = "%.2f" % (total_readings != 0 and ((
        float(chart_data["hypo_count"]) / float(total_readings)) * 100) or 0)
    chart_data['hyper_percentage'] = "%.2f" % (total_readings != 0 and ((
        float(chart_data["hyper_count"]) / float(total_readings)) * 100) or 0)

    return HttpResponse(json.dumps(chart_data),
                        content_type="application/json")


@user_passes_test(professional_user)
def compliance_data(request, user_id):
    try:
        patient = request.user.professional_profile.get_patients().get(
            pk=user_id)
    except User.DoesNotExist as e:
        return debug_response(e)

    today = utcnow().astimezone(request.user.professional_profile.timezone)
    readings = []
    labels = []

    for i in range(7, 0, -1):
        timezone = request.user.professional_profile.timezone
        cur_datetime = convert_date_to_utc_datetime(
            today - timedelta(days=i), timezone)
        end_datetime = cur_datetime + timedelta(days=1)
        readings.append(patient.glucose_readings.filter(
            reading_datetime_utc__range=(
                cur_datetime, end_datetime)).count())
        labels.append(cur_datetime.strftime('%a'))

    data = {
        'labels': labels,
        'readings': readings,
        'patient_name': patient.get_full_name(),
        'professional_name': request.user.get_full_name()
    }
    data['date_range'] = '%s - %s' % (
        (today - timedelta(days=7)).strftime('%m/%d/%y'),
        (today - timedelta(days=1)).strftime('%m/%d/%y'))
    return HttpResponse(json.dumps(data), content_type="application/json")
