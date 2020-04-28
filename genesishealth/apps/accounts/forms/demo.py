from django import forms

from genesishealth.apps.accounts.forms.patients import PatientForm
from genesishealth.apps.accounts.models import DemoPatientProfile
from genesishealth.apps.gdrives.models import GDrive


class DemoPatientForm(PatientForm):
    DEMO_FIELDS = ('reading_types', 'glucose_reading_interval', 'average_premeal_glucose_level',
        'average_postmeal_glucose_level')

    reading_types = forms.MultipleChoiceField(label="[Demo] Reading types", 
        choices=DemoPatientProfile.READING_TYPE_CHOICES, widget=forms.CheckboxSelectMultiple)
    glucose_reading_interval = forms.ChoiceField(label="[Demo] Glucose reading interval",
        choices=DemoPatientProfile.GLUCOSE_READING_INTERVAL_CHOICES)
    average_premeal_glucose_level = forms.CharField(label="[Demo] Average premeal glucose level",
        initial=str(DemoPatientProfile._meta.get_field('average_premeal_glucose_level').default))
    average_postmeal_glucose_level = forms.CharField(label="[Demo] Average postmeal glucose level",
        initial=str(DemoPatientProfile._meta.get_field('average_postmeal_glucose_level').default))

    def __init__(self, *args, **kwargs):
        super(DemoPatientForm, self).__init__(*args, **kwargs)
        # Demo Patients get assigned their own devices.
        self.fields.pop('device', None)
        self.fields.pop('email_confirm', None)
        if not self.is_new:
            for df in DemoPatientForm.DEMO_FIELDS:
                self.fields[df].initial = getattr(self.instance.demo_profile, df)

    def save(self):
        user = super(DemoPatientForm, self).save()
        user.patient_profile.demo_patient = True
        user.patient_profile.save()

        if self.is_new:
            demo_device = GDrive(demo=True,
                            group=self.initial_group,
                            meid=GDrive.generate_demo_meid(),
                            device_id=GDrive.generate_demo_serial(),
                            patient=user)
            demo_device.save()
            demo_profile = DemoPatientProfile(user=user)
        else:
            demo_profile = user.demo_profile

        for df in DemoPatientForm.DEMO_FIELDS: setattr(demo_profile, df, self.cleaned_data.get(df))
        demo_profile.save()
        return user
