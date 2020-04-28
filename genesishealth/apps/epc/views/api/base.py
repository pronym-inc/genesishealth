import sys

from django.conf import settings

from restless.dj import DjangoResource
from restless.utils import format_traceback

from genesishealth.apps.epc.models import EPCAPIUser, EPCLogEntry


def get_client_ip(request):  # pragma: no cover
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class BaseEPCTransactionResource(DjangoResource):
    def __init__(self, *args, **kwargs):
        self.has_logged = False
        self.transaction = None
        super(BaseEPCTransactionResource, self).__init__(*args, **kwargs)

    def build_error(self, err):
        print(err)
        data = {
            'error': err.args[0],
            'success': False,
            'transaction_id': self.get_transaction_id()
        }

        if settings.DEBUG:  # pragma: no cover
            # Add the traceback.
            data['traceback'] = format_traceback(sys.exc_info())

        body = self.serializer.serialize(data)
        status = getattr(err, 'status', 500)
        return self.build_response(body, status=status)

    def is_authenticated(self):
        return self.get_api_user() is not None

    def get_api_user(self):
        if not hasattr(self, '_api_user'):
            data = self.get_deserialized_data()
            try:
                self._api_user = EPCAPIUser.objects.get(
                    is_active=True,
                    username=data['username'],
                    password=data['password'])
            except EPCAPIUser.DoesNotExist:
                self._api_user = None
        return self._api_user

    def get_deserialized_data(self):
        return self.deserialize(
            self.request_method(), self.endpoint, self.request_body())

    def get_transaction_id(self):
        return 1

    def log(self, is_successful, response_sent):
        if self.has_logged:
            return
        self.has_logged = True
        log_entry = EPCLogEntry.objects.create(
            content=self.request_body(),
            response_sent=response_sent,
            source=get_client_ip(self.request),
            transaction_type=self.log_transaction_type,
            is_successful=is_successful
        )
        if self.transaction is not None:
            log_entry.add_transaction(self.transaction)

    def handle(self, endpoint, *args, **kwargs):
        response = super(BaseEPCTransactionResource, self).handle(
            endpoint, *args, **kwargs)
        self.log(is_successful=True, response_sent=response.content)
        return response

    def handle_error(self, err):
        error = super(BaseEPCTransactionResource, self).handle_error(err)
        self.log(is_successful=False, response_sent=error.content)
        return error
