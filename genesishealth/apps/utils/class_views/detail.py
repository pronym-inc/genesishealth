from django.template.loader import get_template
from django.views.generic import TemplateView


class GenesisBaseDetailPane(object):
    def __init__(self, request, context):
        self.request = request
        self.context = context
        self.title = self.get_pane_title()
        self.content = self.render()

    def get_pane_title(self):
        return self.pane_title

    def render(self):
        template = get_template(self.template_name)
        return template.render(self.context, self.request)


class GenesisDetailView(TemplateView):
    template_name = 'utils/detail/detail.html'

    def get_buttons(self):
        return []

    def get_breadcrumbs(self):
        return []

    def get_context_data(self, **kwargs):
        data = super(GenesisDetailView, self).get_context_data(**kwargs)
        data['page_title'] = self.get_page_title()
        data['panes'] = self.render_panes()
        data['buttons'] = self.get_buttons()
        data['breadcrumbs'] = self.get_breadcrumbs()
        return data

    def get_page_title(self):
        return self.page_title

    def get_pane_context(self):
        return {}

    def render_panes(self):
        panes = []
        context = self.get_pane_context()
        for pane_class in self.pane_classes:
            panes.append(pane_class(self.request, context))
        return panes
