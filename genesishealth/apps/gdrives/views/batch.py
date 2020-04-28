from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from genesishealth.apps.gdrives.forms import (
    BatchAssignDeviceForm, BatchAssignDeviceAPIPartnerForm,
    BatchAssignToRxPartnerForm, BatchInspectGDriveForm,
    BatchMarkFailedDeliveryForm, BatchRecoverReadingsForm,
    BatchReworkGDriveForm, BatchUnassignDeviceForm, BatchUnassignRxPartnerForm,
    BatchUpdateGDriveStatusForm)
from genesishealth.apps.gdrives.models import GDrive
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.request import admin_user, check_user_type
from genesishealth.apps.utils.views import (
    generic_form, generic_delete_form)


@user_passes_test(admin_user)
def batch_assign(request):
    return generic_form(
        request,
        form_class=BatchAssignDeviceForm,
        page_title='Assign Devices to a Group',
        system_message="The devices have been assigned.",
        batch=True,
        batch_queryset=GDrive.objects.all())


@user_passes_test(admin_user)
def batch_unassign(request):
    return generic_form(
        request,
        form_class=BatchUnassignDeviceForm,
        go_back_until=['manage-devices', 'manage-groups-devices'],
        batch=True,
        only_batch_input=True,
        batch_queryset=GDrive.objects.all())


@user_passes_test(lambda u: check_user_type(u, ['Admin', 'Professional']))
def batch_delete(request):
    if request.user.is_admin():
        batch_queryset = GDrive.objects.all()
    else:
        batch_queryset = request.user.professional_profile.\
            parent_group.gdrives.all()

    return generic_delete_form(
        request,
        system_message='The selected devices have been deleted.',
        batch=True,
        batch_queryset=batch_queryset
    )


@user_passes_test(admin_user)
def batch_assign_apipartner(request):
    return generic_form(
        request,
        form_class=BatchAssignDeviceAPIPartnerForm,
        page_title='Assign Devices to a API Partner',
        system_message="The devices have been assigned.",
        batch=True,
        batch_queryset=GDrive.objects.all())


@user_passes_test(admin_user)
def batch_recover_readings(request):
    return generic_form(
        request,
        form_class=BatchRecoverReadingsForm,
        page_title='Recover Readings',
        system_message="The readings have been recovered.",
        batch=True,
        batch_queryset=GDrive.objects.all())


@user_passes_test(admin_user)
def batch_update_device_status(request):
    return generic_form(
        request,
        form_class=BatchUpdateGDriveStatusForm,
        page_title='Update Device Status',
        system_message="The devices have been updated.",
        batch=True,
        batch_queryset=GDrive.objects.all())


@user_passes_test(admin_user)
def batch_rework_devices(request):
    breadcrumbs = [
        Breadcrumb('Non-Conforming Devices',
                   reverse('gdrives:non-conforming-devices'))
    ]
    return generic_form(
        request,
        form_class=BatchReworkGDriveForm,
        form_kwargs={'requester': request.user},
        page_title='Rework Devices',
        breadcrumbs=breadcrumbs,
        system_message="The devices have been reworked.",
        batch=True,
        batch_queryset=GDrive.objects.filter(
            status=GDrive.DEVICE_STATUS_REPAIRABLE))


@user_passes_test(admin_user)
def batch_assign_to_rx_partner(request):
    breadcrumbs = [
        Breadcrumb('Available Devices',
                   reverse('gdrives:available'))
    ]
    statuses = (GDrive.DEVICE_STATUS_AVAILABLE,
                GDrive.DEVICE_STATUS_ASSIGNED)
    return generic_form(
        request,
        form_class=BatchAssignToRxPartnerForm,
        page_title='Assign Devices to Rx Partner',
        breadcrumbs=breadcrumbs,
        system_message="The devices have been assigned.",
        batch=True,
        batch_queryset=GDrive.objects.filter(
            status__in=statuses))


@user_passes_test(admin_user)
def batch_unassign_from_rx_partner(request):
    breadcrumbs = [
        Breadcrumb('Partner Devices',
                   reverse('gdrives:partner-devices'))
    ]
    return generic_form(
        request,
        form_class=BatchUnassignRxPartnerForm,
        page_title='Unassign Devices from Rx Partner',
        breadcrumbs=breadcrumbs,
        system_message="The devices have been unassigned.",
        batch=True,
        only_batch_input=True,
        batch_queryset=GDrive.objects.all())


@user_passes_test(admin_user)
def batch_inspect_reworked_devices(request):
    breadcrumbs = [
        Breadcrumb('Reworked Devices',
                   reverse('gdrives:reworked-devices'))
    ]
    return generic_form(
        request,
        form_class=BatchInspectGDriveForm,
        form_kwargs={'requester': request.user},
        page_title='Inspect Devices',
        breadcrumbs=breadcrumbs,
        system_message="The devices have been marked available.",
        batch=True,
        batch_queryset=GDrive.objects.filter(
            status=GDrive.DEVICE_STATUS_REWORKED))


@user_passes_test(admin_user)
def batch_mark_delivery_failed(request):
    return generic_form(
        request,
        form_class=BatchMarkFailedDeliveryForm,
        page_title='Mark Devices With Failed Delivery',
        system_message="The devices have been updated.",
        batch=True,
        only_batch_input=True,
        form_template='gdrives/mark_failed_delivery.html',
        batch_queryset=GDrive.objects.filter(
            status=GDrive.DEVICE_STATUS_ASSIGNED))
