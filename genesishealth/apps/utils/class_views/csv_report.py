import csv
import io

from django import forms

from genesishealth.apps.reports.models import TemporaryDownload
from genesishealth.apps.reports.tasks import (
    get_report_class as grc_async, run_report_async)
from genesishealth.apps.utils.class_views.form import GenesisFormView
from genesishealth.apps.utils.forms import GenesisForm
from genesishealth.apps.utils.request import redirect_with_message


class CSVReportForm(GenesisForm):
    run_async = forms.BooleanField(
        required=False, label="Generate in background")

    def __init__(self, *args, **kwargs):
        super(CSVReportForm, self).__init__(*args, **kwargs)
        # Sort to put run async at the bottom
        ordered_fields = list(self.fields.keys())
        self.order_fields(sorted(
            ordered_fields,
            key=lambda x: x == 'run_async'))


class CSVReport(object):
    configuration_form_class = CSVReportForm
    header_rows = []
    max_synchronous_rows = 200
    never_async = False

    def __init__(self, **kwargs):
        self.config_kwargs = kwargs
        self.configure(**kwargs)

    def configure(self, **kwargs):
        pass

    def create_download(self, data, user):
        content = self.generate_csv_content(data)
        dl = TemporaryDownload.objects.create(
            for_user=user,
            content=content,
            content_type="text/csv",
            filename=self.get_filename(data))
        return dl

    def create_download_from_raw_data(self, input_data, user):
        form_kwargs = self.get_configuration_form_kwargs()
        form = self.get_form_class()(input_data, **form_kwargs)
        if not form.is_valid():
            raise Exception("Form was not valid in process_data")
        return self.create_download(form.cleaned_data, user)

    def generate_csv_content(self, data):
        # Create CSV in memory buffer
        buf = io.BytesIO()
        writer = csv.writer(buf)
        # Write headers + rows
        for row in self.get_header_rows(data) + self.get_rows(data):
            writer.writerow(row)
        return buf.getvalue()

    def get_async_handle(self):
        return str(type(self))

    def get_configuration_form_kwargs(self):
        return {}

    def get_filename(self, data):
        return "report.csv"

    def get_form_class(self):
        return self.configuration_form_class

    def get_header_rows(self, data):
        return self.header_rows

    def get_item_row(self, item):
        return []

    def get_queryset(self, data):
        raise Exception("Must supply a get_queryset function!")

    def get_rows(self, data):
        return map(self.get_item_row, self.get_queryset(data))

    def should_run_async(self, data):
        if self.never_async:
            return False
        if self.get_queryset(data).count() > self.max_synchronous_rows:
            return True
        return data.get('run_async', False)

    def run_async(self, user, form_data):
        async_handle = self.get_async_handle()
        if grc_async(async_handle) is None:
            raise Exception(
                "Invalid async handle: {0}".format(async_handle))
        return run_report_async.delay(
            async_handle, user.id, form_data, self.config_kwargs)


class CSVReportView(GenesisFormView):
    header_rows = []
    success_message = "Your report has been generated."
    report_class = None
    run_async = False

    def form_valid(self, form):
        report = self.get_report()
        redirect_kwargs = {'go_back_until': self.go_back_until}
        if report.should_run_async(form.cleaned_data):
            report.run_async(self.request.user, self.get_post_data())
        else:
            dl = report.create_download(
                self.get_report_data(form), self.request.user)
            redirect_kwargs['then_download_id'] = dl.id
        return redirect_with_message(
            self.request,
            self.get_success_url(form),
            self.get_success_message(form),
            **redirect_kwargs)

    def get_form_class(self):
        return self.report_class.configuration_form_class

    def get_form_kwargs(self):
        kwargs = super(CSVReportView, self).get_form_kwargs()
        kwargs.update(self.get_report().get_configuration_form_kwargs())
        return kwargs

    def get_post_data(self):
        output = {}
        print(self.request.POST.items())
        for key, value in self.request.POST.lists():
            if len(value) == 1:
                output[key] = value[0]
            else:
                output[key] = value
        return output

    def get_report_class(self):
        return self.report_class

    def get_report(self):
        if not hasattr(self, '_report'):
            self._report = self.report_class(**self.get_report_kwargs())
        return self._report

    def get_report_data(self, form):
        return form.cleaned_data

    def get_report_kwargs(self):
        return {}
