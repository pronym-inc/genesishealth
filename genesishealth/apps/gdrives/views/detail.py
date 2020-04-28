from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from genesishealth.apps.gdrives.breadcrumbs import get_device_breadcrumbs
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.utils.class_views import (
    GenesisAboveTableButton, GenesisDetailView, GenesisBaseDetailPane)
from genesishealth.apps.utils.request import check_user_type


test = user_passes_test(
    lambda u: check_user_type(u, ['Admin']))


class DeviceSnapshotPane(GenesisBaseDetailPane):
    template_name = 'gdrives/detail_panes/snapshot.html'
    pane_title = 'Details'


class PatientInfoPane(GenesisBaseDetailPane):
    template_name = 'gdrives/detail_panes/patient.html'
    pane_title = 'Patient Information'


class ProcessPane(GenesisBaseDetailPane):
    template_name = 'gdrives/detail_panes/process.html'
    pane_title = 'GHT Processes'


class ComplaintPane(GenesisBaseDetailPane):
    template_name = 'gdrives/detail_panes/complaint.html'
    pane_title = 'Complaint'


class GetDeviceMixin(object):
    def get_device(self):
        if not hasattr(self, '_device'):
            self._device = GDrive.objects.get(pk=self.kwargs['device_id'])
        return self._device


class DeviceDetailView(GenesisDetailView, GetDeviceMixin):
    pane_classes = (
        DeviceSnapshotPane, PatientInfoPane, ProcessPane, ComplaintPane
    )

    def get_breadcrumbs(self):
        device = self.get_device()
        return get_device_breadcrumbs(device, self.request.user, False)

    def get_buttons(self):
        device = self.get_device()
        buttons = [
            GenesisAboveTableButton(
                'Edit Details',
                reverse('gdrives:edit', args=[device.pk])
            ),
            GenesisAboveTableButton(
                'Recover Readings',
                reverse('gdrives:recover-readings', args=[device.pk])
            )
        ]
        if device.status == GDrive.DEVICE_STATUS_REPAIRABLE:
            buttons.append(GenesisAboveTableButton(
                'Rework',
                reverse('gdrives:rework-device', args=[device.pk])
            ))
        buttons.append(
            GenesisAboveTableButton(
                'Network Status',
                ''
            )
        )
        if device.is_inspectable():
            buttons.append(
                GenesisAboveTableButton(
                    'Inspect',
                    reverse('gdrives:inspect-device',
                            args=[device.pk])
                )
            )
        buttons.append(
            GenesisAboveTableButton(
                'Complaints',
                reverse('gdrives:complaints', args=[device.pk])
            )

        )
        if device.non_conformities.count() > 0:
            buttons.append(
                GenesisAboveTableButton(
                    'Non-Conformity Report',
                    reverse('gdrives:non-conformity-report-pdf',
                            args=[device.pk]),
                    prefix=''
                )
            )

        return buttons

    def get_page_title(self):
        return 'Manage Device {0}'.format(self.get_device().meid)

    def get_pane_context(self):
        device = self.get_device()
        previous_readings = device.readings.order_by(
            '-reading_datetime_utc')[:3]
        if device.complaints.count() > 0:
            last_complaint = device.complaints.order_by('-datetime_added')[0]
        else:
            last_complaint = None
        return {
            'device': device,
            'previous_readings': previous_readings,
            'last_complaint': last_complaint
        }
detail = test(DeviceDetailView.as_view())
