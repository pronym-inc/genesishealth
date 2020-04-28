from genesishealth.apps.gdrives.models import GDrive


class GetDeviceMixin(object):
    def get_device(self):
        if not hasattr(self, '_device'):
            self._device = GDrive.objects.get(pk=self.kwargs['device_id'])
        return self._device
