import csv

from dateutil.parser import parse

from pytz import UTC

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from genesishealth.apps.accounts.models.profile_patient import (
    PatientCommunication, PatientCommunicationNote)
from genesishealth.apps.dropdowns.models import (
    CommunicationStatus, CommunicationCategory, CommunicationSubcategory)
from genesishealth.apps.products.models import ProductType


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('single_call_log_file', type=str)
        parser.add_argument('multiple_call_log_file', type=str)

    def handle(self, *args, **options):
        single_call_log_file = options['single_call_log_file']
        multiple_call_log_file = options['multiple_call_log_file']
        tz = get_default_timezone()
        meter_product = ProductType.objects.filter(is_device=True)[0]
        with open(single_call_log_file, 'rbU') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            # Skip header
            next(reader)
            for row in reader:
                patient = User.objects.filter(
                    patient_profile__isnull=False).get(pk=row[0])
                subject = row[1]
                category_name = row[2]
                subcategory_name = row[3]
                description = row[4]
                notes = row[5]
                replaced_meter = bool(row[6])
                qi_category = row[7].lower()
                try:
                    added_by = User.objects.filter(is_staff=True).get(
                        username=row[8])
                except User.DoesNotExist:
                    added_by = None
                datetime_added = tz.localize(parse(row[9])).astimezone(UTC)
                if row[10] == 'TRUE':
                    status = CommunicationStatus.objects.get(is_closed=True)
                else:
                    status = CommunicationStatus.objects.filter(
                        is_closed=False)[0]
                datetime_closed = tz.localize(
                    parse(row[11])).astimezone(UTC)
                try:
                    closed_by = User.objects.filter(is_staff=True).get(
                        username=row[12])
                except User.DoesNotExist:
                    closed_by = None
                category, _ = CommunicationCategory.objects.get_or_create(
                    name=category_name)
                subcategory, _ = \
                    CommunicationSubcategory.objects.get_or_create(
                        name=subcategory_name)
                subcategory.category.add(category)
                comm = PatientCommunication.objects.create(
                    patient=patient,
                    subject=subject,
                    description=description,
                    category=category,
                    subcategory=subcategory,
                    status=status,
                    added_by=added_by,
                    datetime_updated=datetime_closed,
                    last_updated_by=closed_by)
                comm.datetime_added = datetime_added
                comm.save()
                # Create note
                note = PatientCommunicationNote.objects.create(
                    communication=comm,
                    quality_improvement_category=qi_category,
                    added_by=closed_by,
                    content=notes,
                    change_status_to=status,
                    has_replacements=replaced_meter)
                note.datetime_added = datetime_closed
                note.save()
                if replaced_meter:
                    note.replacements.add(meter_product)

        with open(multiple_call_log_file, 'rbU') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            comm = None
            next(reader)
            for row in reader:
                idx = int(row[0])
                patient = User.objects.filter(
                    patient_profile__isnull=False).get(pk=row[1])
                subject = row[2]
                category_name = row[3]
                subcategory_name = row[4]
                description = row[5]
                notes = row[6]
                replaced_meter = bool(row[7])
                qi_category = row[8].lower()
                try:
                    added_by = User.objects.filter(is_staff=True).get(
                        username=row[9])
                except User.DoesNotExist:
                    added_by = None
                datetime_added = tz.localize(parse(row[10])).astimezone(UTC)
                if row[11] == 'Closed':
                    status = CommunicationStatus.objects.get(is_closed=True)
                else:
                    status, _ = CommunicationStatus.objects.get_or_create(
                        name=row[11])
                datetime_closed = tz.localize(
                    parse(row[12])).astimezone(UTC)
                try:
                    closed_by = User.objects.filter(is_staff=True).get(
                        username=row[13])
                except User.DoesNotExist:
                    closed_by = None
                category, _ = CommunicationCategory.objects.get_or_create(
                    name=category_name)
                subcategory, _ = \
                    CommunicationSubcategory.objects.get_or_create(
                        name=subcategory_name)
                subcategory.category.add(category)
                if idx == 1:
                    comm = PatientCommunication.objects.create(
                        patient=patient,
                        subject=subject,
                        description=description,
                        category=category,
                        subcategory=subcategory,
                        status=status,
                        added_by=added_by,
                        datetime_updated=datetime_closed,
                        last_updated_by=closed_by)
                    comm.datetime_added = datetime_added
                    comm.save()
                # Create note
                note = PatientCommunicationNote.objects.create(
                    communication=comm,
                    quality_improvement_category=qi_category,
                    added_by=closed_by,
                    content=notes,
                    change_status_to=status,
                    has_replacements=replaced_meter)
                note.datetime_added = datetime_closed
                note.save()
                if replaced_meter:
                    note.replacements.add(meter_product)
