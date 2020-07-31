from django.db import models


class WorkQueueItem(models.Model):
    """An item in the work queue."""
    ITEM_TYPE_CHOICES = (
        ('Order', 'Order'),
        ('Report', 'Report'),
    )
    STATUS_CHOICES = (
        ('In QA', 'In QA'),
        ('Ready to Work', 'Ready to Work')
    )
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_due = models.DateTimeField()
    name = models.CharField(max_length=255)
    item_type = models.ForeignKey('WorkQueueType', on_delete=models.CASCADE, related_name='+')
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='In QA')
    is_passed_qa = models.BooleanField(default=False)
