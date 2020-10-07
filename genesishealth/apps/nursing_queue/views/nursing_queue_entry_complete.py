from typing import Dict, Any

from django.contrib.auth.decorators import user_passes_test
from django.utils.timezone import now

from genesishealth.apps.nursing_queue.models import NursingQueueEntry
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import professional_user


class NursingQueueEntryCompleteForm(GenesisForm):
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super().__init__(*args, **kwargs)

    def save(self):
        self.instance.is_completed = True
        self.instance.completed_datetime = now()
        self.instance.save()
        return self.instance


class NursingQueueEntryCompleteView(GenesisFormView):
    form_class = NursingQueueEntryCompleteForm
    page_title = "Complete Nursing Queue Item"
    go_back_until = ['nursing-queue:queue']
    success_message = "The item has been completed."

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = NursingQueueEntry.objects.get(
            pk=self.kwargs['nursing_queue_entry_id']
        )
        return kwargs


nursing_queue_entry_complete_view = user_passes_test(professional_user)(NursingQueueEntryCompleteView.as_view())
