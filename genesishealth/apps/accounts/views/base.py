from genesishealth.apps.accounts.models import GenesisGroup
from genesishealth.apps.utils.class_views import GenesisTableView


class GetGroupMixin(object):
    def get_group(self, force=False):
        if not hasattr(self, '_group'):
            self._group = None
        if force or self._group is None:
            group_id = self.kwargs.get('group_id')
            if group_id:
                self._group = GenesisGroup.objects.get(pk=group_id)
            else:
                if self.request.user.is_professional():
                    self._group = self.request.user.professional_profile\
                        .parent_group
        return self._group


class GroupTableView(GenesisTableView, GetGroupMixin):
    pass
