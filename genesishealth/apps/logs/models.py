from django.db import models


class QALogEntry(models.Model):
    datetime_created = models.DateTimeField(auto_now_add=True)
    reading_datetime = models.DateTimeField()
    glucose_value = models.IntegerField()
    meid = models.CharField(max_length=255)

    def __unicode__(self):
        return "QALogEntry ({}) for {} at {}".format(
            self.glucose_value, self.meid, self.reading_datetime)
