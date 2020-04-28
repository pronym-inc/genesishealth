from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.accounts.models.admin_user import AdminProfile
from genesishealth.apps.gdrives.models import GDrive


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--admin-confirm', action='store_true')

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['admin-confirm']:
            raise Exception("Must supply --admin-confirm flag.")

        try:
            User.objects.get(username="admin")
        except User.DoesNotExist:
            my_user = User(username="admin", email="admin@test.com")
            my_user.set_password("password123")
            my_user.save()
            AdminProfile.objects.create(user=my_user, is_super_user=True)

        # Create a test device

        fake_meid = 'TEST000012345678'

        try:
            GDrive.objects.get(meid=fake_meid)
        except GDrive.DoesNotExist:
            test_device = GDrive.objects.create(
                is_verizon_testing_device=True,
                meid=fake_meid,
                device_id='AAAA000012345678'
            )
            # Create a patient for it.
            user = PatientProfile.myghr_patients.create_user(
                "Gregg", "Keithley", "password123", "gregg@pronym.com")
            test_device.register(user)
