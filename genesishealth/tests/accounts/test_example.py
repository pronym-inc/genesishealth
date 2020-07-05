from django.test import TestCase

from genesishealth.apps.gdrives.models import GDrive


class TestExampleTestCase(TestCase):
    def test_math(self):
        device = GDrive.objects.create(
            meid="123456789",
            device_id="987654321"
        )
        self.assertEqual(device.meid, "1234567890")
