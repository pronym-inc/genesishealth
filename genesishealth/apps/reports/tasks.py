from celery.task import task


def get_report_class(report_name):
    from genesishealth.apps.accounts.views.groups import GroupExportReport, GroupExportAccountReport, GroupAccountStatusReport, GroupReadingDelayReport  # noqa
    from genesishealth.apps.epc.views.groups.export import ShippingHistoryReport  # noqa
    from genesishealth.apps.gdrives.views.cellular import CellularFullMEIDListReport, CellularDeactivationReport  # noqa
    from genesishealth.apps.orders.views.reports.business_partner_order_history import BusinessPartnerOrderHistoryReport  # noqa
    from genesishealth.apps.orders.views.reports.order_history import OrderHistoryReport  # noqa
    from genesishealth.apps.orders.views.reports.patient_order_history import PatientOrderHistoryReport  # noqa
    from genesishealth.apps.orders.views.reports.projected_refills import ProjectedRefillReport  # noqa
    from genesishealth.apps.orders.views.reports.rx_partner_order_history import RxPartnerOrderHistoryReport  # noqa
    from genesishealth.apps.readings.views.reports.exception import ReadingExceptionReport  # noqa
    reports = [
        GroupExportReport, BusinessPartnerOrderHistoryReport,
        OrderHistoryReport, PatientOrderHistoryReport,
        RxPartnerOrderHistoryReport, ProjectedRefillReport,
        GroupExportAccountReport, CellularFullMEIDListReport,
        CellularDeactivationReport, GroupAccountStatusReport,
        ShippingHistoryReport, GroupReadingDelayReport,
        ReadingExceptionReport]
    report_dict = {str(a): a for a in reports}
    report = report_dict.get(report_name)
    if report is not None:
        return report
    for key, value in report_dict.items():
        if report_name in key:
            return value


@task
def trigger_report(report):
    report.trigger_delayed()


@task
def run_report_async(report_name, user_id, form_data, form_config):
    from django.contrib.auth.models import User
    user = User.objects.get(id=user_id)
    report_class = get_report_class(report_name)
    if report_class is None:
        raise Exception("Invalid report name {0}".format(report_name))
    report = report_class(**form_config)
    report.create_download_from_raw_data(form_data, user)
