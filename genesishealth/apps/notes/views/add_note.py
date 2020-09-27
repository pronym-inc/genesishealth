from typing import List, Dict, Any

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse

from genesishealth.apps.notes.models import PatientNote
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import check_user_type


class AddPatientNoteForm(GenesisModelForm):
    class Meta:
        model = PatientNote
        fields = ('content',)

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester')
        self.patient = kwargs.pop('patient')
        super().__init__(*args, **kwargs)

    def save(self, commit=True, **kwargs):
        obj = super().save(commit=False)
        obj.patient = self.patient.patient_profile
        obj.author = self.requester.professional_profile
        obj.save()
        return obj


class AddPatientNoteView(GenesisFormView):
    form_class = AddPatientNoteForm
    go_back_until = [
        'notes:patient-notes',
        'accounts:manage-patients-professional-detail'
    ]
    success_message = 'The note has been added'

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['requester'] = self.request.user
        kwargs['patient'] = self._get_patient()
        return kwargs

    def _get_breadcrumbs(self) -> List[Breadcrumb]:
        patient = self._get_patient()
        return [
            Breadcrumb(
                f'Patient: {patient.get_reversed_name()}',
                reverse(
                    'accounts:manage-patients-professional-detail',
                    args=[patient.pk]
                )
            ),
            Breadcrumb(
                'Notes',
                reverse('notes:patient-notes', args=[patient.pk])
            )
        ]

    def _get_page_title(self) -> str:
        patient = self._get_patient()
        return f"Add note for {patient.get_reversed_name()}"

    def _get_patient(self) -> User:
        if not hasattr(self, '_patient'):
            self._patient = User.objects.filter(
                patient_profile__isnull=False
            ).get(pk=self.kwargs['patient_id'])
        return self._patient


add_patient_note = user_passes_test(
    lambda u: check_user_type(u, ['Professional'])
)(AddPatientNoteView.as_view())
