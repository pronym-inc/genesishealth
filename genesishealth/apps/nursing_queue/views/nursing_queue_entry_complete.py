from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.utils.timezone import now
from django.views import View

from genesishealth.apps.nursing_queue.models import NursingQueueEntry
from genesishealth.apps.utils.request import professional_user, redirect_with_message


class NursingQueueEntryCompleteView(View):
    def get(self, request, *args, **kwargs):
        entry = NursingQueueEntry.objects.get(
            pk=self.kwargs['nursing_queue_entry_id']
        )
        entry.completed_datetime = now()
        entry.is_completed = True
        entry.save()
        return redirect_with_message(
            self.request,
            reverse('nursing-queue:queue'),
            "The task has been marked complete."
        )


nursing_queue_entry_complete_view = user_passes_test(professional_user)(NursingQueueEntryCompleteView.as_view())
