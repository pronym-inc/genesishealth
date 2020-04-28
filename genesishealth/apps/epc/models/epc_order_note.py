from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now


class EPCOrderNote(models.Model):
    order = models.ForeignKey('EPCOrder', related_name='notes', on_delete=models.CASCADE)
    order_change = models.OneToOneField(
        'EPCOrderChange', related_name='note', null=True, on_delete=models.SET_NULL)
    message = models.TextField()
    added_by = models.ForeignKey(
        'auth.User', related_name='epc_order_notes', null=True, on_delete=models.SET_NULL)
    added_datetime = models.DateTimeField(default=now)
    ordering = models.PositiveIntegerField()

    class Meta:
        app_label = 'epc'
        unique_together = ('order', 'ordering')
        ordering = ('-ordering',)


@receiver(pre_save, sender=EPCOrderNote)
def populate_ordering(sender, instance, *args, **kwargs):
    if instance.id is None and instance.ordering is None:
        instance.ordering = instance.order.get_next_note_ordering()
