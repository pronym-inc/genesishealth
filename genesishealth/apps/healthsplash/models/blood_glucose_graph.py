from datetime import date, timedelta
from io import BytesIO

import numpy
from django.conf import settings
from django.core.files import File
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from matplotlib import pyplot
from matplotlib.dates import MonthLocator, DateFormatter, DayLocator

from genesishealth.apps.readings.models import GlucoseReading


class BloodGlucoseGraph(models.Model):
    """A stored image of a line graph for a period of readings."""
    datetime_added = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="blood_glucose_graph/")

    @classmethod
    def for_readings(
            cls,
            readings: 'QuerySet[GlucoseReading]',
            start_date: date,
            end_date: date
    ) -> 'BloodGlucoseGraph':
        """Create a graph for the given set of readings, for the given period of time."""
        date_format = "%m-%d-%y"
        fig, ax = pyplot.subplots()
        sorted_readings = readings.order_by('reading_datetime_utc')
        ax.plot(
            [numpy.datetime64(reading.reading_datetime_utc) for reading in sorted_readings],
            [reading.glucose_value for reading in sorted_readings],
            'ko:'
        )
        # Add a day to the end date, so we include all the readings from that day.
        ax.set_xlim(numpy.datetime64(start_date), numpy.datetime64(end_date + timedelta(days=1)))
        pyplot.title(f"Blood Glucose - {start_date.strftime(date_format)} - {end_date.strftime(date_format)}")
        pyplot.ylabel("Blood Sugar - mg/dL")
        pyplot.xlabel("Date")
        x_axis = ax.xaxis
        # Depending on our interval, use different ticks.
        interval_days = int((end_date - start_date).total_seconds() // 60 // 60 // 24)
        if interval_days >= 30:
            x_axis.set_major_locator(MonthLocator())
            x_axis.set_major_formatter(DateFormatter("%m-%Y"))
            x_axis.set_minor_locator(DayLocator())
        else:
            day_interval: int
            if interval_days <= 7:
                day_interval = 1
            else:
                day_interval = interval_days // 7
            x_axis.set_major_locator(DayLocator(bymonthday=range(1, 32, day_interval)))
            x_axis.set_major_formatter(DateFormatter("%m-%d"))
            x_axis.set_minor_locator(DayLocator())
        fig.autofmt_xdate()
        buf = BytesIO()
        pyplot.savefig(buf)

        graph: BloodGlucoseGraph = BloodGlucoseGraph.objects.create()
        graph.image.save(f'{graph.pk}.png', File(buf))

        return graph

    def get_secure_url(self) -> str:
        path = reverse('healthsplash:blood-glucose-graph', args=[self.pk])
        protocol = 'https://' if settings.USE_HTTPS else 'http://'
        site_url = settings.SITE_URL
        return f'{protocol}{site_url}{path}'
