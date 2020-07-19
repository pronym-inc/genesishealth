import csv
import io
from abc import ABC
from typing import List, Type, Any, Dict, ClassVar

from celery.result import AsyncResult
from django import forms
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpResponse

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


class CSVReport(ABC):
    configuration_form_class: ClassVar[Type[CSVReportForm]] = CSVReportForm
    header_rows: ClassVar[List[List[str]]] = []
    max_synchronous_rows: ClassVar[int] = 200
    never_async: ClassVar[bool] = False

    _config_kwargs: ClassVar[Dict[str, Any]]

    _rows: List[List[str]]

    def __init__(self, **kwargs: Any):
        self.config_kwargs = kwargs
        self._configure(**kwargs)

    def create_download(self, data: Dict[str, Any], user: User) -> TemporaryDownload:
        content = self.generate_csv_content(data)
        dl = TemporaryDownload.objects.create(
            for_user=user,
            content=content,
            content_type="text/csv",
            filename=self.get_filename(data))
        return dl

    def create_download_from_raw_data(self, input_data: Dict[str, Any], user: User) -> TemporaryDownload:
        form_kwargs = self.get_configuration_form_kwargs()
        form = self.get_form_class()(input_data, **form_kwargs)
        if not form.is_valid():
            raise Exception("Form was not valid in process_data")
        return self.create_download(form.cleaned_data, user)

    def generate_csv_content(self, data: Dict[str, Any]) -> str:
        # Create CSV in memory buffer
        buf = io.StringIO()
        writer = csv.writer(buf)
        # Write headers + rows
        for row in self.get_header_rows(data) + self.get_rows(data):
            writer.writerow(row)
        return buf.getvalue()

    def get_async_handle(self) -> str:
        return str(type(self))

    def get_configuration_form_kwargs(self) -> Dict[str, Any]:
        return {}

    def get_filename(self, data: Dict[str, Any]) -> str:
        return "report.csv"

    def get_form_class(self) -> Type[CSVReportForm]:
        return self.configuration_form_class

    def get_header_rows(self, data: Dict[str, Any]) -> List[List[str]]:
        return self.header_rows

    def get_item_row(self, item: Any) -> List[str]:
        return []

    def get_queryset(self, data: Dict[str, Any]) -> QuerySet:
        raise Exception("Must supply a get_queryset function!")

    def get_rows(self, data: Dict[str, Any]) -> List[List[str]]:
        if not hasattr(self, '_rows'):
            self._rows = list(map(self.get_item_row, self.get_queryset(data)))
        return self._rows

    def should_run_async(self, data: Dict[str, Any]) -> bool:
        if self.never_async:
            return False
        if self.get_queryset(data).count() > self.max_synchronous_rows:
            return True
        return data.get('run_async', False)

    def run_async(self, user: User, form_data: Dict[str, Any]) -> AsyncResult:
        async_handle = self.get_async_handle()
        if grc_async(async_handle) is None:
            raise Exception(
                "Invalid async handle: {0}".format(async_handle))
        return run_report_async.delay(
            async_handle, user.id, form_data, self.config_kwargs)

    def _configure(self, **kwargs: Any) -> None:
        pass


class CSVReportView(GenesisFormView):
    header_rows: ClassVar[List[str]] = []
    success_message: ClassVar[str] = "Your report has been generated."
    report_class: ClassVar[Type[CSVReport]]
    run_async: ClassVar[bool] = False

    def form_valid(self, form: CSVReportForm) -> HttpResponse:
        report = self._get_report()
        redirect_kwargs = {'go_back_until': self.go_back_until}
        if report.should_run_async(form.cleaned_data):
            report.run_async(self.request.user, self._get_post_data())
        else:
            dl = report.create_download(
                self._get_report_data(form), self.request.user)
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
        kwargs.update(self._get_report().get_configuration_form_kwargs())
        return kwargs

    def _get_post_data(self):
        output = {}
        for key, value in self.request.POST.lists():
            if len(value) == 1:
                output[key] = value[0]
            else:
                output[key] = value
        return output

    def _get_report_class(self) -> Type[CSVReport]:
        return self.report_class

    def _get_report(self) -> CSVReport:
        if not hasattr(self, '_report'):
            self._report = self.report_class(**self._get_report_kwargs())
        return self._report

    def _get_report_data(self, form: CSVReportForm) -> Dict[str, Any]:
        return form.cleaned_data

    def _get_report_kwargs(self) -> Dict[str, Any]:
        return {}

    def _create_download(self, data, user) -> TemporaryDownload:
        content = self.generate_csv_content(data)
        dl = TemporaryDownload.objects.create(
            for_user=user,
            content=content,
            content_type="text/csv",
            filename=self.get_filename(data))
        return dl
