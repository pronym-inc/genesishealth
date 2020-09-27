from typing import Dict, Any

from django.contrib.auth.decorators import user_passes_test

from genesishealth.apps.nursing_queue.models import NursingQueueEntry
from genesishealth.apps.utils.class_views import GenesisFormView
from genesishealth.apps.utils.forms import GenesisModelForm
from genesishealth.apps.utils.request import professional_user


class NursingQueueEntryRescheduleForm(GenesisModelForm):
    class Meta:
        model = NursingQueueEntry
        fields = ('due_date',)


class NursingQueueEntryRescheduleView(GenesisFormView):
    form_class = NursingQueueEntryRescheduleForm
    page_title = "Reschedule Queue Item"
    go_back_until = ['nursing-queue:queue']
    success_message = "The item has been rescheduled."

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = NursingQueueEntry.objects.get(
            pk=self.kwargs['nursing_queue_entry_id']
        )
        return kwargs


nursing_queue_entry_reschedule_view = user_passes_test(professional_user)(NursingQueueEntryRescheduleView.as_view())
