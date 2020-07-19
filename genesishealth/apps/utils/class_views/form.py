from typing import List, Optional, ClassVar

from django.views.generic.edit import FormMixin, FormView

from genesishealth.apps.utils.breadcrumbs import Breadcrumb
from genesishealth.apps.utils.request import redirect_with_message


class GenesisBaseFormMixin(object):
    template_name = 'utils/generic_form.html'
    go_back_until = []
    do_raw_redirect = False

    def do_success_redirect(self, form):
        return redirect_with_message(
            self.request,
            self.get_success_url(form),
            self.get_success_message(form),
            go_back_until=self.go_back_until,
            raw_redirect=self.do_raw_redirect
        )

    def form_valid(self, form):
        self.save_form(form)
        return self.do_success_redirect(form)

    def get_success_message(self, form):
        return self.success_message

    def get_success_url(self, form):
        pass

    def save_form(self, form):
        try:
            form.save()
        except AttributeError:
            pass


class GenesisFormMixin(GenesisBaseFormMixin, FormMixin):
    pass


class GenesisFormView(GenesisBaseFormMixin, FormView):
    template_name = 'utils/generic_form.html'
    form_message = None
    page_title: ClassVar[str]

    def get_context_data(self, **kwargs):
        if 'breadcrumbs' not in kwargs:
            kwargs['breadcrumbs'] = self._get_breadcrumbs()
        kwargs.setdefault('title', self._get_page_title())
        form_message = self._get_form_message()
        if form_message:
            kwargs.setdefault('form_message', form_message)
        return super(GenesisFormView, self).get_context_data(**kwargs)

    def _get_breadcrumbs(self) -> List[Breadcrumb]:
        return []

    def _get_form_message(self) -> Optional[str]:
        return self.form_message

    def _get_page_title(self) -> str:
        return self.page_title


class GenesisBatchFormView(GenesisFormView):
    batch_variable = "batch_ids"

    def get_context_data(self, **kwargs):
        data = GenesisFormView.get_context_data(self, **kwargs)
        data['batch_id_str'] = self._get_batch_id_string()
        return data

    def get_form_kwargs(self):
        kwargs = GenesisFormView.get_form_kwargs(self)
        kwargs['batch_queryset'] = self.get_batch_queryset()
        kwargs['batch'] = map(int, self._get_batch_id_string().split(","))
        return kwargs

    def _get_batch_id_string(self):
        post_data = self.request.POST.copy()
        return post_data.get(self.batch_variable)
