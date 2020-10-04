from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.nursing_queue.models import NursingQueueEntry
from genesishealth.apps.utils.class_views import GenesisTableView, AttributeTableColumn, ActionTableColumn, ActionItem, \
    GenesisTableLink, GenesisTableLinkAttrArg, GenesisAboveTableButton
from genesishealth.apps.utils.request import professional_user


class NursingQueueView(GenesisTableView):
    extra_search_fields = ['patient__first_name', 'patient__last_name']

    def create_columns(self):
        return [
            AttributeTableColumn('Due Date', 'due_date', searchable=True),
            AttributeTableColumn('Patient', 'patient.user.get_reversed_name', proxy_field='patient.user.last_name'),
            AttributeTableColumn('Entry Type', 'get_entry_type_display', searchable=False),
            AttributeTableColumn('Group/Employer', 'patient.company.name', searchable=True),
            AttributeTableColumn('Insurance ID', 'patient.insurance_identifier', searchable=True),
            AttributeTableColumn('Date of Birth', 'patient.date_of_birth', searchable=True),
            AttributeTableColumn('Latest Note', 'patient.get_latest_note_summary', searchable=False),
            AttributeTableColumn('Phone Number', 'patient.contact.phone', searchable='patient.contact.phonenumber_set.phone'),
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
                ]
            ),
            ActionTableColumn(
                'Complete',
                actions=[
                    ActionItem(
                        'Complete',
                        GenesisTableLink(
                            'nursing-queue:entry-complete',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        )
                    ),
                ]
            ),
            ActionTableColumn(
                'Reschedule',
                actions=[
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

    def get_above_table_items(self):
        if self.get_should_show_completed():
            return [
                GenesisAboveTableButton(
                    'Show Uncompleted',
                    reverse('nursing-queue:queue')
                )
            ]
        return [
            GenesisAboveTableButton(
                'Show Completed',
                reverse('nursing-queue:queue') + "?showCompleted=1"
            )
        ]

    def get_page_title(self):
        return 'Nursing Work Queue'

    def get_queryset(self):
        try:
            nursing_group = self.request.user.professional_profile.nursing_group
        except NursingGroup.DoesNotExist:
            return NursingQueueEntry.objects.none()
        if nursing_group is None:
            return NursingQueueEntry.objects.none()
        should_show_completed = self.get_should_show_completed()
        return nursing_group.nursing_queue_entries.filter(is_completed=should_show_completed)

    def get_should_show_completed(self) -> bool:
        return self.request.GET.get('showCompleted') == '1'


nursing_queue_view = user_passes_test(professional_user)(NursingQueueView.as_view())
