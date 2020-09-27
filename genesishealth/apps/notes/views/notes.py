from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User

from genesishealth.apps.utils.class_views import GenesisTableView, AttributeTableColumn
from genesishealth.apps.utils.request import professional_user


class PatientNotesView(GenesisTableView):
    def create_columns(self):
        return [
            AttributeTableColumn('Date / Time Added', 'datetime_added'),
            AttributeTableColumn('Author', 'author.user.get_reversed_name'),
            AttributeTableColumn('Content', 'content')
        ]

    def get_page_title(self):
        return f'Notes for {self.get_patient().get_reversed_name()}'

    def get_patient(self):
        if not hasattr(self, '_patient'):
            self._patient = User.objects.filter(
                patient_profile__isnull=False
            ).get(pk=self.kwargs['patient_id'])
        return self._patient

    def get_queryset(self):
        patient = self.get_patient()
        return patient.patient_profile.patient_notes.all()


patient_notes = user_passes_test(professional_user)(PatientNotesView.as_view())
