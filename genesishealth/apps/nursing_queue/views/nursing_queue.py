from django.contrib.auth.decorators import user_passes_test

from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.nursing_queue.models import NursingQueueEntry
from genesishealth.apps.utils.class_views import GenesisTableView, AttributeTableColumn, ActionTableColumn, ActionItem, \
    GenesisTableLink, GenesisTableLinkAttrArg
from genesishealth.apps.utils.request import professional_user


class NursingQueueView(GenesisTableView):
    extra_search_fields = ['patient__first_name', 'patient__last_name']

    def create_columns(self):
        return [
            AttributeTableColumn('Due Date', 'due_date'),
            AttributeTableColumn('Patient', 'patient.user.get_reversed_name'),
            AttributeTableColumn('Entry Type', 'get_entry_type_display'),
            AttributeTableColumn('Phone Number', 'patient.contact.phone'),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'accounts:manage-patients-professional-detail',
                            url_args=[GenesisTableLinkAttrArg('patient.user.id')]
                        )
                    ),
                    ActionItem(
                        'Complete',
                        GenesisTableLink(
                            'nursing-queue:entry-complete',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                    ActionItem(
                        'Reschedule',
                        GenesisTableLink(
                            'nursing-queue:entry-reschedule',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    )
                ]
            )
        ]

    def get_page_title(self):
        return 'Nursing Work Queue'

    def get_queryset(self):
        try:
            nursing_group = self.request.user.professional_profile.nursing_group
        except NursingGroup.DoesNotExist:
            return NursingQueueEntry.objects.none()
        return nursing_group.nursing_queue_entries.filter(is_completed=False)


nursing_queue_view = user_passes_test(professional_user)(NursingQueueView.as_view())
