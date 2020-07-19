from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from genesishealth.apps.utils.request import admin_user


class ViewWorkQueueItemView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        pass


view_work_queue_item = user_passes_test(admin_user)(ViewWorkQueueItemView.as_view())
