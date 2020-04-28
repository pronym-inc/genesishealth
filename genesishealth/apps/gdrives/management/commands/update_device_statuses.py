from django.core.management.base import BaseCommand

from genesishealth.apps.gdrives.models import GDrive


class Command(BaseCommand):
    def handle(self, **options):
        for device in GDrive.objects.all():
            if device.patient is not None:
                if (device.patient.patient_profile.demo_patient or
                        device.patient.patient_profile.is_scalability_user):
                    device.status = GDrive.DEVICE_STATUS_DEMO
                else:
                    device.status = GDrive.DEVICE_STATUS_ASSIGNED
            elif device.unassigned_patients.count() > 0:
                device.status = GDrive.DEVICE_STATUS_UNASSIGNED
            else:
                device.status = GDrive.DEVICE_STATUS_NEW
            device.save()
