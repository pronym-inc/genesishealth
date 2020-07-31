from datetime import timedelta
from typing import Dict, Any

from django import forms
from django.urls import reverse

from genesishealth.apps.accounts.breadcrumbs.patients import (
    get_patient_breadcrumbs)
from genesishealth.apps.orders.models import OrderShipment
from genesishealth.apps.pharmacy.breadcrumbs import get_rx_partner_breadcrumbs
from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm, GenesisForm
from genesishealth.apps.utils.request import require_admin_permission
from genesishealth.apps.work_queue.models import WorkQueueItem

test = require_admin_permission('orders')


class DelayWorkQueueItemForm(GenesisForm):
    DELAY_CHOICES = (
        (1, 'One Day'),
        (2, 'Two Days'),
        (3, 'Three Days'),
        (4, 'Four Days'),
        (5, 'Five Days'),
        (7, 'One Week')
    )
    delay_by = forms.ChoiceField(choices=DELAY_CHOICES)
    _item: WorkQueueItem

    def __init__(self, *args, **kwargs):
        self._item = kwargs.pop('queue_item')
        super().__init__(*args, **kwargs)

    def save(self, commit=True, *args, **kwargs):
        print(self.cleaned_data)
        self._item.datetime_due += timedelta(days=int(self.cleaned_data['delay_by']))
        self._item.save()


class DelayWorkQueueItemView(GenesisFormView):
    form_class = DelayWorkQueueItemForm
    go_back_until = ['work_queue:main-queue']
    success_message = "The work queue item has been updated."

    _item: WorkQueueItem

    def get_work_queue_item(self) -> WorkQueueItem:
        if not hasattr(self, '_item'):
            self._item = WorkQueueItem.objects.get(pk=self.kwargs['item_id'])
        return self._item

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['queue_item'] = self.get_work_queue_item()
        return kwargs

    def _get_page_title(self):
        item = self.get_work_queue_item()
        return f'Update Work Queue Item - {item.name}'

    def get_success_url(self, form):
        return reverse('work_queue:main-queue')


delay_work_queue_item = test(DelayWorkQueueItemView.as_view())
