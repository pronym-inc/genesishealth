"""A command for making a device and user for the end_to_end2 test command."""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.gdrives.models import GDriveTransmissionLogEntry, GDrive


class Command(BaseCommand):
    def handle(self, **options) -> None:
        meid_base = "E2E_DEMO"
        counter = 0
        meid: str
        while True:
            meid = f"{meid_base}_{counter}"
            try:
                GDrive.objects.get(meid=meid)
            except GDrive.DoesNotExist:
                break
            counter += 1
        username_base = "e2e_user"
        counter = 0
        while True:
            username = f"{username_base}_{counter}"
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                break
            counter += 1
        email = f"{username}@test.com"
        patient = PatientProfile.objects.create_user(
            username,
            email,
            email_password=False
        )
        device: GDrive = GDrive.objects.create(meid=meid, device_id=meid, is_verizon_testing_device=True)
        device.register(patient)

        print(f"Created new user: {patient} with device {meid}")
