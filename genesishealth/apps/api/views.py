from dateutil.parser import parse

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.utils.timezone import now

from genesishealth.apps.api.models import APIPartner
from genesishealth.apps.utils.request import admin_user

import pytz


@user_passes_test(admin_user)
def wellness_doc(request, pk):
    partner = APIPartner.objects.get(pk=pk)
    tz = pytz.timezone('America/Chicago')
    if 'date' in request.GET:
        target_date = tz.localize(parse(request.GET['date']))
    else:
        target_date = now().astimezone(tz).date()
    filename, doc = partner.make_wellness_document(target_date)
    resp = HttpResponse(doc.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return resp
