from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from django import forms
from django.contrib.auth.models import User
from django.forms import widgets
from django.utils.timezone import now

from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.api.models import APIPartner
from genesishealth.apps.dropdowns.models import (
    DeviceProblem, MeterDisposition)
from genesishealth.apps.gdrives.models import (
    GDrive, GDriveFirmwareVersion, GDriveComplaint, GDriveComplaintUpdate,
    GDriveNonConformity, GDriveInspectionRecord, GDriveModuleVersion,
    GDriveReworkRecord, GDriveManufacturerCarton, GDriveWarehouseCarton,
    PharmacyPartner)
from genesishealth.apps.utils.forms import (
    GenesisForm, GenesisModelForm, GenesisBatchForm, GenesisImportForm)
from genesishealth.apps.utils.func import read_csv_file
from genesishealth.apps.utils.widgets import (
    AdditionalModelMultipleChoiceWidget)


class AssignDeviceForm(GenesisForm):
    patient = forms.ModelChoiceField(queryset=None)

    class Meta:
        model = GDrive
        fields = ('patient',)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super(AssignDeviceForm, self).__init__(*args, **kwargs)
        qs = self.fields['patient'].queryset = \
            self.instance.get_available_patients()
        self.fields['patient'].choices = [
            (p.pk, p.get_reversed_name()) for p in qs]

    def save(self):
        patient = self.cleaned_data['patient']
        patient.patient_profile.register_device(self.instance)
        return self.instance


class RecoverReadingsForm(GenesisForm):
    starting_from = forms.DateField(
        help_text="Enter a date in the format MM/DD/YY")

    def __init__(self, *args, **kwargs):
        self.device = kwargs.pop('device')
        super(RecoverReadingsForm, self).__init__(*args, **kwargs)

    def save(self):
        self.device.recover_readings(self.cleaned_data['starting_from'])


class BatchUnassignDeviceForm(GenesisBatchForm):
    def save(self):
        for device in self.batch:
            device.group = None
            device.save()


class BatchAssignDeviceForm(GenesisBatchForm):
    group = forms.ModelChoiceField(queryset=GenesisGroup.objects.all())

    def save(self):
        for device in self.batch:
            device.group = self.cleaned_data.get('group')
            device.save()


class BatchAssignDeviceAPIPartnerForm(GenesisBatchForm):
    partner = forms.ModelChoiceField(queryset=APIPartner.objects.all())

    def save(self):
        for device in self.batch:
            device.partner = self.cleaned_data['partner']
            device.save()


class BatchRecoverReadingsForm(GenesisBatchForm):
    starting_from = forms.DateField(
        help_text="Enter a date in the format MM/DD/YY")

    def save(self):
        starting_from = self.cleaned_data['starting_from']
        for device in self.batch:
            device.recover_readings(starting_from)


class GDriveForm(GenesisModelForm):
    phone_number = forms.CharField(required=False)

    class Meta:
        model = GDrive
        fields = ('meid', 'device_id', 'manufacturer_carton',
                  'phone_number')

    def __init__(self, *args, **kwargs):
        self.initial_group = kwargs.pop('initial_group', None)
        self.patient = kwargs.pop('patient', None)
        super(GDriveForm, self).__init__(*args, **kwargs)
        if not self.is_new:
            self.fields['meid'].widget.attrs['readonly'] = True

    def clean_meid(self):
        if not self.is_new:
            return self.instance.meid
        return self.cleaned_data.get('meid')

    def save(self, commit=True):
        device = super(GDriveForm, self).save(commit=False)
        if self.initial_group:
            device.group = self.initial_group
        if self.patient:
            self.patient.patient_profile.replace_device(device)
        device.save()
        return device


class PatientEditGDriveForm(GDriveForm):
    class Meta(GDriveForm.Meta):
        exclude = ('meid', 'professional', 'created_at', 'patient')


class ImportDevicesForm(GenesisForm):
    group = forms.ModelChoiceField(
        queryset=GenesisGroup.objects.all(), required=False,
        help_text='If provided, all of the devices will be assigned to '
                  'this group.')
    devices = forms.CharField(
        max_length=2048, widget=forms.Textarea(),
        help_text='Provide a list with one device per line in the format '
                  '"<MEID> <serial #>"')

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        super(ImportDevicesForm, self).__init__(*args, **kwargs)
        # If we have a group, set the value of group and hide the input.
        if self.group:
            self.fields['group'].initial = self.group
            self.fields['group'].widget = forms.HiddenInput()

    def clean_devices(self):
        devices = []
        used_meids = []
        used_serials = []
        for line in self.cleaned_data.get('devices').splitlines():
            split = line.split(',')
            leng = len(split)
            if leng != 2:
                raise forms.ValidationError(
                    "Each row must contain an MEID and a serial number, "
                    "separated by a comma.")
            meid, device_id = map(lambda x: x.strip(), split)

            try:
                GDrive.objects.get(meid=meid)
            except GDrive.DoesNotExist:
                if meid in used_meids:
                    raise forms.ValidationError(
                        "All MEIDs must be unique.  %s appears more than once "
                        "in your import data." % meid)
            else:
                raise forms.ValidationError(
                    "All MEIDs must be unique.  %s is already in the system."
                    % meid)

            try:
                GDrive.objects.get(device_id=device_id)
            except GDrive.DoesNotExist:
                if device_id in used_serials:
                    raise forms.ValidationError(
                        "All serial numbers must be unique.  %s appears more "
                        "than once in your import data" % device_id)
            else:
                raise forms.ValidationError(
                    "All serial numbers must be unique.  %s is already "
                    "in the system." % device_id)
            used_meids.append(meid)
            used_serials.append(device_id)
            device_data = {"meid": meid, "device_id": device_id}
            devices.append(device_data)

        return devices

    def clean_group(self):
        # Effectively makes it read-only if group is provided.
        return self.group or self.cleaned_data.get('group')

    def save(self):
        devices = self.cleaned_data.get('devices')
        group = self.cleaned_data.get('group')
        for device in devices:
            kwargs = {'meid': device['meid'], 'device_id': device['device_id']}
            if group:
                kwargs['group'] = group
            dv = GDrive(**kwargs)
            dv.save()


class ManufacturerCartonLineForm(GenesisModelForm):
    firmware_version = forms.ModelChoiceField(
        queryset=GDriveFirmwareVersion.objects.all(), to_field_name='name')
    module_version = forms.ModelChoiceField(
        queryset=GDriveModuleVersion.objects.all(), to_field_name='name')
    date_shipped = forms.DateField(input_formats=['%m/%d/%y'])

    class Meta:
        model = GDriveManufacturerCarton
        fields = ('number', 'firmware_version', 'module_version',
                  'date_shipped', 'lot_number')


class ManufacturerCartonImportForm(GenesisImportForm):
    line_form_class = ManufacturerCartonLineForm
    csv_headers = [
        'number', 'firmware_version', 'module_version', 'date_shipped',
        'lot_number'
    ]


class GDriveLineForm(GenesisModelForm):
    manufacturer_carton = forms.ModelChoiceField(
        queryset=GDriveManufacturerCarton.objects.all(),
        to_field_name='number')

    class Meta:
        model = GDrive
        fields = ('meid', 'device_id', 'manufacturer_carton')


class GDriveImportForm(GenesisImportForm):
    line_form_class = GDriveLineForm
    csv_headers = [
        'meid', 'device_id', 'manufacturer_carton'
    ]


class GDriveAssignLineForm(GenesisForm):
    gdrive = forms.ModelChoiceField(
        queryset=GDrive.objects.filter(
            status=GDrive.DEVICE_STATUS_AVAILABLE), to_field_name='meid')
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(patient_profile__isnull=False))

    def save(self):
        device = self.cleaned_data['gdrive']
        patient = self.cleaned_data['patient']
        old_device = patient.patient_profile.get_device()
        if old_device:
            old_device.unregister()
        device.register(patient)


class GDriveAssignForm(GenesisImportForm):
    line_form_class = GDriveAssignLineForm
    csv_headers = ['gdrive', 'patient']


class GDriveComplaintForm(GenesisModelForm):
    reported_problems = forms.ModelMultipleChoiceField(
        queryset=DeviceProblem.objects.all(),
        widget=AdditionalModelMultipleChoiceWidget)

    class Meta:
        model = GDriveComplaint
        fields = ('reported_problems', 'description',)

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.device = kwargs.pop('device')
        super(GDriveComplaintForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(GDriveComplaintForm, self).save(commit=False)
        if self.is_new:
            instance.added_by = self.requester
            instance.device = self.device
        instance.touch(self.requester)
        if commit:
            instance.save()
            instance.reported_problems.set(self.cleaned_data['reported_problems'])
        return instance


class GDriveInspectionForm(GenesisForm):
    disposition = forms.ModelChoiceField(
        queryset=MeterDisposition.objects.all(),
        required=False,
        empty_label="Available",
        label="New status")
    acknowledgement = forms.BooleanField(required=False)
    non_conformity_types = forms.ModelMultipleChoiceField(
        queryset=DeviceProblem.objects.all(),
        widget=AdditionalModelMultipleChoiceWidget,
        required=False,
        label="Non-conformity types")
    non_conformity_description = forms.CharField(
        widget=widgets.Textarea, required=False,
        label="Non-conformity description")
    tray_number = forms.CharField(required=False, label="Tray number")

    def __init__(self, *args, **kwargs):
        self.device = kwargs.pop('device')
        self.requester = kwargs.pop('requester')
        super(GDriveInspectionForm, self).__init__(*args, **kwargs)
        self.fields['acknowledgement'].help_text = (
            'I, {0} {1}, attest that I tested this meter according to Genesis '
            'Meter Acceptance Testing Procedures.'.format(
                self.requester.first_name, self.requester.last_name))

    def clean(self):
        data = self.cleaned_data
        if data['disposition'] is not None:
            errors = []
            expected_fields = (
                'non_conformity_types', 'non_conformity_description',
                'tray_number')
            for field in expected_fields:
                if not data[field]:
                    errors.append(forms.ValidationError(
                        '{0} is required.'.format(
                            self.fields[field].label)))
            if errors:
                raise forms.ValidationError(errors)
        else:
            if not data['acknowledgement']:
                raise forms.ValidationError(
                    'You must acknowledge the inspection.')
        return data

    def save(self):
        if self.cleaned_data['disposition'] is None:
            self.device.validate(self.requester)
        else:
            self.device.mark_repairable(
                self.cleaned_data['tray_number'],
                self.cleaned_data['disposition'])
            non_conform = GDriveNonConformity.objects.create(
                added_by=self.requester,
                device=self.device,
                description=self.cleaned_data['non_conformity_description'],
                tray_number=self.cleaned_data['tray_number']
            )
            for typ in self.cleaned_data['non_conformity_types']:
                non_conform.non_conformity_types.add(typ)


class GDriveNonConformityForm(GenesisModelForm):
    class Meta:
        model = GDriveNonConformity
        fields = ('non_conformity_types', 'description', 'tray_number')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.device = kwargs.pop('device')
        super(GDriveNonConformityForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(GDriveNonConformityForm, self).save(commit=False)
        instance.added_by = self.requester
        instance.device = self.device
        if commit:
            instance.save()
        return instance


class GDriveInspectionRecordForm(GenesisModelForm):
    acknowledgement = forms.BooleanField()

    class Meta:
        models = GDriveInspectionRecord
        fields = ('acknowledgement',)

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.device = kwargs.pop('device')
        super(GDriveInspectionRecordForm, self).__init__(*args, **kwargs)
        self.fields['acknowledgement'].label = (
            'I, {0} {1}, attest that I tested this meter according to Genesis'
            ' Meter Acceptance Testing Procedures.'.format(
                self.requester.first_name, self.requester.last_name))

    def save(self, commit=True):
        obj = super(GDriveInspectionRecordForm, self).save(commit=False)
        obj.added_by = self.requester
        obj.device = self.device
        if commit:
            obj.save()
        return obj


class GDriveReworkRecordForm(GenesisModelForm):
    new_disposition = forms.ModelChoiceField(
        queryset=MeterDisposition.objects.filter(
            is_problem=True),
        label="New Status")

    class Meta:
        model = GDriveReworkRecord
        fields = ('new_disposition', 'details', 'ready_for_inspection')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.device = kwargs.pop('device')
        super(GDriveReworkRecordForm, self).__init__(*args, **kwargs)
        self.fields['ready_for_inspection'].help_text = (
            'Checking this box will finalize the rework on the device making '
            'it ready for reinspection. Leave unchecked if the rework did not '
            'restore device as New.')

    def save(self, commit=True):
        obj = super(GDriveReworkRecordForm, self).save(commit=False)
        obj.reworked_by = self.requester
        obj.device = self.device
        if self.cleaned_data['ready_for_inspection']:
            self.device.rework()
        self.device.segregation_disposition = \
            self.cleaned_data['new_disposition']
        self.device.save()
        obj.save()
        return obj


class BatchUpdateGDriveStatusForm(GenesisBatchForm):
    new_status = forms.ChoiceField(choices=GDrive.DEVICE_STATUS_CHOICES)

    def save(self):
        new_status = self.cleaned_data['new_status']
        for device in self.batch:
            device.update_status(new_status)
            device.save()


class GDriveManufacturerCartonForm(GenesisModelForm):
    class Meta:
        model = GDriveManufacturerCarton
        fields = ('number', 'lot_number', 'date_shipped',
                  'firmware_version', 'module_version')


class AddGDriveToWarehouseCartonForm(GenesisForm):
    device = forms.ModelChoiceField(
        queryset=GDrive.objects.filter(
            status=GDrive.DEVICE_STATUS_AVAILABLE,
            warehouse_carton__isnull=True),
        to_field_name='meid',
        widget=widgets.TextInput,
        label='Add Device to Carton'
    )


class CreateWarehouseCartonForm(GenesisModelForm):
    class Meta:
        model = GDriveWarehouseCarton
        fields = ('number',)

    def __init__(self, *args, **kwargs):
        self.devices = kwargs.pop('devices', None)
        super(CreateWarehouseCartonForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        carton = super(CreateWarehouseCartonForm, self).save()
        for device in self.devices:
            device.warehouse_carton = carton
            device.save()
        return carton


class InspectManufacturerCartonForm(GenesisForm):
    acknowledgement = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.carton = kwargs.pop('carton')
        super(InspectManufacturerCartonForm, self).__init__(*args, **kwargs)
        self.fields['acknowledgement'].label = (
            'Inspector: {0} {1}'.format(
                self.requester.first_name, self.requester.last_name))

    def save(self, commit=True):
        self.carton.approve(self.requester)


class BatchInspectGDriveForm(GenesisBatchForm):
    acknowledgement = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchInspectGDriveForm, self).__init__(*args, **kwargs)
        self.fields['acknowledgement'].label = (
            'Inspector: {0} {1}'.format(
                self.requester.first_name, self.requester.last_name))

    def save(self, commit=True):
        for device in self.batch:
            device.validate(self.requester)


class BatchReworkGDriveForm(GenesisBatchForm):
    details = forms.CharField(widget=widgets.Textarea)

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(BatchReworkGDriveForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        for device in self.batch:
            device.rework()
            GDriveReworkRecord.objects.create(
                device=device,
                reworked_by=self.requester,
                details=self.cleaned_data['details'])


class BatchMarkFailedDeliveryForm(GenesisBatchForm):
    def save(self):
        for device in self.batch:
            device.mark_failed_delivery()


YES_OR_NO = (
    (True, 'Yes'),
    (False, 'No')
)


class RMAInspectionForm(GenesisModelForm):
    found_problems = forms.ModelMultipleChoiceField(
        queryset=DeviceProblem.objects.all(),
        widget=AdditionalModelMultipleChoiceWidget,
        required=False)
    is_validated = forms.ChoiceField(
        widget=widgets.RadioSelect,
        choices=YES_OR_NO,
        label='Complaint Confirmed')

    class Meta:
        model = GDriveComplaint
        fields = (
            'rma_return_date',
            'found_problems',
            'is_validated',
            'rma_notes')

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        super(RMAInspectionForm, self).__init__(*args, **kwargs)
        for field in ('found_problems', 'rma_notes', 'is_validated'):
            del self.initial[field]

    def save(self, commit=True):
        obj = super(RMAInspectionForm, self).save(commit=False)
        obj.validated_by = self.requester
        obj.touch(self.requester)
        obj.save()
        obj.found_problems.set(self.cleaned_data['found_problems'])
        # Create update object, also.
        update = GDriveComplaintUpdate.objects.create(
            complaint=obj,
            rma_return_date=self.cleaned_data['rma_return_date'],
            is_validated=self.cleaned_data['is_validated'],
            updated_by=self.requester,
            rma_notes=self.cleaned_data['rma_notes']
        )
        update.found_problems.set(self.cleaned_data['found_problems'])
        return obj


class BatchAssignToRxPartnerForm(GenesisBatchForm):
    partner = forms.ModelChoiceField(
        queryset=PharmacyPartner.objects.all())

    def save(self):
        print(self.batch)
        for device in self.batch:
            print(device)
            print(self.cleaned_data['partner'])
            device.set_rx_partner(self.cleaned_data['partner'])


class BatchUnassignRxPartnerForm(GenesisBatchForm):
    def save(self):
        for device in self.batch:
            device.set_rx_partner(None)


class RMASummaryConfigureForm(GenesisForm):
    start_date = forms.DateField()
    end_date = forms.DateField()

    def __init__(self, *args, **kwargs):
        super(RMASummaryConfigureForm, self).__init__(
            *args, **kwargs)
        default_end_date = now().date()
        default_start_date = default_end_date - relativedelta(months=3)
        self.fields['start_date'].initial = default_start_date
        self.fields['end_date'].initial = default_end_date

    def clean(self):
        data = self.cleaned_data
        if data['start_date'] >= data['end_date']:
            raise forms.ValidationError('End date must be after start date.')
        return data


class UpdateCellularStatusForm(GenesisForm):
    new_status = forms.ChoiceField(
        choices=GDrive.DEVICE_NETWORK_STATUS_CHOICES)
    device_list = forms.FileField()

    def clean_device_list(self):
        csv_data = read_csv_file(
            self.cleaned_data['device_list'],
            ('meid', 'mpn', 'ip', 'status_changed_on'),
            1
        )
        errors = []
        self.devices_to_update = []
        for row_num, row in enumerate(csv_data, 1):
            parsed_status_changed = None
            device = None
            try:
                device = GDrive.objects.get(meid=row['meid'])
            except GDrive.DoesNotExist:
                errors.append(
                    "[{0}] Could not find device with MEID: {1}".format(
                        row_num, row['meid']))
            try:
                parsed_status_changed = parse(row['status_changed_on'])
            except ValueError:
                errors.append("[{0}] Could not parse date/time: {1}".format(
                    row_num, row['status_changed_on']))
            if errors:
                continue
            details = {
                'phone_number': row['mpn'],
                'ip_address': row['ip'],
                'datetime_network_status_changed': parsed_status_changed,
                'network_status': self.cleaned_data['new_status']
            }
            if (self.cleaned_data['new_status'] ==
                    GDrive.DEVICE_NETWORK_STATUS_ACTIVE):
                details['datetime_network_status_activated'] = \
                    parsed_status_changed
            self.devices_to_update.append((device, details))
        if errors:
            raise forms.ValidationError("\n".join(errors))

    def save(self, *args, **kwargs):
        for device, details in self.devices_to_update:
            for field_name, val in details.items():
                setattr(device, field_name, val)
            device.save()
