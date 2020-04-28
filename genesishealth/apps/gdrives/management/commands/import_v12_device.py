import csv

from dateutil.parser import parse

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import get_default_timezone

from genesishealth.apps.gdrives.models import (
    GDriveManufacturerCarton, GDrive, GDriveModuleVersion,
    GDriveFirmwareVersion, GDriveNonConformity,
    GDriveWarehouseCarton)
from genesishealth.apps.dropdowns.models import DeviceProblem

from pytz import UTC


User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('device_detail_file', type=str)

    def parse_datetime(self, time_str):
        if time_str is None:
            return
        tz = get_default_timezone()
        return tz.localize(parse(time_str)).astimezone(UTC)

    def handle(self, *args, **options):
        device_detail_file = options['device_detail_file']
        devices_by_patient = {}
        device_ids = set([])
        non_conforming_ids = set([])
        with open(device_detail_file, 'rbU') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            # Skip headers
            reader.next()
            for row in reader:
                meid = row[1]
                serial_num = row[2]
                # manufacturer = row[3]
                module = row[4]
                lot_num = row[5]
                firmware_name = row[6]
                carton_num = row[7]
                ship_date = self.parse_datetime(row[8])
                is_inspected = row[9] == 'TRUE'
                qa_date = self.parse_datetime(row[10])
                qa_admin_username = row[11]
                is_non_conforming = int(row[12]) == -1
                warehouse_carton_num = row[13]
                non_conformity_name = row[14]
                qa_notes = row[15]
                patient_id = row[16]
                assign_date = self.parse_datetime(row[17])
                wireless_number = row[18]
                vz_status = row[19]
                activated_dt = self.parse_datetime(row[20])
                deactivated_dt = self.parse_datetime(row[21])
                if is_non_conforming:
                    non_conforming_ids.add(meid)
                try:
                    device = GDrive.objects.get(meid=meid)
                except GDrive.DoesNotExist:
                    if not serial_num or serial_num == 'Demo':
                        final_serial = 'A' + serial_num
                    else:
                        final_serial = serial_num
                    try:
                        device = GDrive.objects.create(
                            meid=meid, device_id=final_serial)
                    except:
                        continue
                device_ids.add(device.id)
                if qa_admin_username:
                    qa_admin = User.objects.filter(is_staff=True).get(
                        username=qa_admin_username)
                else:
                    qa_admin = None
                if assign_date:
                    device.datetime_assigned = assign_date
                if patient_id:
                    try:
                        User.objects.filter(
                            patient_profile__isnull=False).get(id=row[16])
                    except User.DoesNotExist:
                        pass
                    else:
                        devices_by_patient.setdefault(patient_id, [])
                        devices_by_patient[patient_id].append(device.id)
                if vz_status == 'Active':
                    new_vz_status = GDrive.DEVICE_NETWORK_STATUS_ACTIVE
                elif vz_status == 'Deactivated':
                    new_vz_status = GDrive.DEVICE_NETWORK_STATUS_DEACTIVATED
                try:
                    manu_carton = GDriveManufacturerCarton.objects.get(
                        number=carton_num)
                except GDriveManufacturerCarton.DoesNotExist:
                    fw, _ = GDriveFirmwareVersion.objects.get_or_create(
                        name=firmware_name)
                    module, _ = GDriveModuleVersion.objects.get_or_create(
                        name=module)
                    manu_carton = GDriveManufacturerCarton.objects.create(
                        number=carton_num,
                        lot_number=lot_num,
                        date_shipped=ship_date,
                        is_inspected=is_inspected,
                        approved_by=qa_admin,
                        approved_datetime=qa_date,
                        firmware_version=fw,
                        module_version=module
                    )
                device.manufacturer_carton = manu_carton
                if activated_dt:
                    device.datetime_activated = activated_dt
                    device.datetime_status_changed = activated_dt
                if deactivated_dt:
                    device.datetime_status_changed = deactivated_dt
                if is_non_conforming:
                    non_conform = GDriveNonConformity.objects.create(
                        added_by=qa_admin,
                        device=device,
                        description=qa_notes,
                        tray_number=''
                    )
                    dp, _ = DeviceProblem.objects.get_or_create(
                        name=non_conformity_name)
                    non_conform.non_conformity_types.add(dp)
                # Create warehouse carton if necc.
                if warehouse_carton_num:
                    wh_carton, _ = GDriveWarehouseCarton.objects.get_or_create(
                        number=warehouse_carton_num)
                    device.warehouse_carton = wh_carton
                device.phone_number = wireless_number
                device.network_status = new_vz_status
                if qa_date:
                    device.datetime_inspected = qa_date
                device.save()

        for patient_id, device_ids in devices_by_patient.items():
            patient = User.objects.filter(
                patient_profile__isnull=False).get(id=patient_id)
            devices = GDrive.objects.filter(id__in=device_ids)
            for device in devices:
                my_dt = device.datetime_assigned
                later_devices = devices\
                    .exclude(
                        pk=device.pk
                    ).filter(
                        datetime_assigned__gt=my_dt
                    ).order_by('datetime_assigned')
                if later_devices.count() == 0:
                    # Then this is current device.
                    if device.patient:
                        if device.patient != patient:
                            print(
                                "Found wrong patient attached to {0}:"
                                " {1} {2}".format(
                                    device, device.patient, patient))
                    else:
                        try:
                            device.register(patient)
                        except Exception as e:
                            print('Device registration failed: {0}'.format(e))
                        else:
                            device.datetime_assigned = my_dt
                else:
                    next_device = later_devices[0]
                    device.unassigned_patients.add(patient)
                    device.datetime_replaced = \
                        next_device.datetime_assigned
                device.save()
        for device in GDrive.objects.filter(meid__in=non_conforming_ids):
            device.status = GDrive.DEVICE_STATUS_REPAIRABLE
            device.save()
        for device in GDrive.objects.exclude(meid__in=non_conforming_ids):
            if device.patient:
                new_status = GDrive.DEVICE_STATUS_ASSIGNED
            elif device.unassigned_patients.count() > 0:
                new_status = GDrive.DEVICE_STATUS_UNASSIGNED
            elif device.datetime_inspected:
                new_status = GDrive.DEVICE_STATUS_AVAILABLE
            else:
                new_status = GDrive.DEVICE_STATUS_NEW
            device.status = new_status
            device.save()
