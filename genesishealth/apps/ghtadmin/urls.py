from django.conf.urls import url

from genesishealth.apps.ghtadmin.views import dashboard
from genesishealth.apps.ghtadmin.views.admin import index, reports, messaging, eligibility, program_tiers, \
    product_types, shipping, marketing, education

urlpatterns = [
    url(
        r'^$',
        dashboard.main,
        name="dashboard"
    ),
    url(
        r'^admin/$',
        index.main,
        name="admin-index"
    ),
    url(
        r'^admin/reports/$',
        reports.main,
        name="admin-reports"
    ),
    url(
        r'^admin/messaging/$',
        messaging.main,
        name="admin-messaging"
    ),
    url(
        r'^admin/eligibility/$',
        eligibility.main,
        name="admin-eligibility"
    ),
    url(
        r'^admin/program_tiers/$',
        program_tiers.main,
        name="admin-program-tiers"
    ),
    url(
        r'^admin/product_types/$',
        product_types.main,
        name="admin-product-types"
    ),
    url(
        r'^admin/shipping/$',
        shipping.main,
        name="admin-shipping"
    ),
    url(
        r'^admin/marketing/$',
        marketing.main,
        name="admin-marketing"
    ),
    url(
        r'^admin/education/$',
        education.main,
        name="admin-education"
    )
]
