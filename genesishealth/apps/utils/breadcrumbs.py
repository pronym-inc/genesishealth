from django.conf import settings


class Breadcrumb(object):
    def __init__(self, title, link):
        self.title = title
        self.link = "{0}{1}".format(settings.DASHBOARD_PREFIX, link)
