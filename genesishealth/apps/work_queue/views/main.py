from django.contrib.auth.decorators import user_passes_test

from genesishealth.apps.utils.class_views import GenesisTableView, AttributeTableColumn, ActionTableColumn, ActionItem, \
    GenesisTableLink, GenesisTableLinkAttrArg
from genesishealth.apps.utils.request import admin_user
from genesishealth.apps.work_queue.models import WorkQueueItem


class MainWorkQueueTableView(GenesisTableView):
    extra_search_fields = ['patient__first_name']

    def create_columns(self):
        return [
            AttributeTableColumn(
                'Datetime Added',
                'datetime_added'),
            AttributeTableColumn(
                'Datetime Due',
                'datetime_due',
                default_sort_direction='asc',
                default_sort=True
            ),
            AttributeTableColumn('Name', 'name'),
            AttributeTableColumn('Type', 'item_type'),
            AttributeTableColumn('Status', 'status'),
            AttributeTableColumn('Passed QA?', 'is_passed_qa'),
            ActionTableColumn(
                'View',
                actions=[
                    ActionItem(
                        'View',
                        GenesisTableLink(
                            'work_queue:view-item',
                            url_args=[GenesisTableLinkAttrArg('pk')])
                    ),
                    ActionItem(
                        'Approve',
                        GenesisTableLink(
                            'work_queue:approve-item',
                            url_args=[GenesisTableLinkAttrArg('pk')]
                        ),
                        condition=['is_passed_qa']
                    )
                ]
            )
        ]

    def get_page_title(self):
        return 'Work Queue'

    def get_queryset(self):
        return WorkQueueItem.objects.all()


main_queue = user_passes_test(admin_user)(MainWorkQueueTableView.as_view())
