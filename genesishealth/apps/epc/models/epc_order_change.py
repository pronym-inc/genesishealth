from datetime import date

from dateutil.parser import parse

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now

from genesishealth.apps.epc.models import EPCOrderNote


def clean_field_name(field_name):
    split_name = field_name.split('_')
    capitalized_name = list(map(lambda x: x.capitalize(), split_name))
    return " ".join(capitalized_name)


class EPCOrderChange(models.Model):
    datetime_added = models.DateTimeField(default=now)
    epc_member = models.ForeignKey(
        'accounts.PatientProfile', related_name='epc_order_changes', on_delete=models.CASCADE)
    order = models.ForeignKey('EPCOrder', related_name='changes', on_delete=models.CASCADE)
    transaction = models.OneToOneField(
        'OrderRequestTransaction', related_name='order_change', on_delete=models.CASCADE)
    epc_member_identifier = models.CharField(max_length=255, null=True)
    order_number = models.CharField(max_length=255, null=True)
    order_type = models.CharField(max_length=255, null=True)
    order_method = models.CharField(max_length=255, null=True)
    order_date = models.DateField(null=True)
    control_solution_request = models.IntegerField(null=True)
    meter_request = models.IntegerField(null=True)
    strips_request = models.IntegerField(null=True)
    lancet_request = models.IntegerField(null=True)
    lancing_device_request = models.IntegerField(null=True)
    pamphlet_id_request = models.IntegerField(null=True)
    meter_shipped = models.IntegerField(null=True)
    meid = models.CharField(max_length=255, null=True)
    strips_shipped = models.IntegerField(null=True)
    lancets_shipped = models.IntegerField(null=True)
    control_solution_shipped = models.IntegerField(null=True)
    lancing_device_shipped = models.IntegerField(null=True)
    pamphlet_id_shipped = models.IntegerField(null=True)
    order_status = models.CharField(max_length=255, null=True)
    ship_date = models.DateField(null=True)
    tracking_number = models.CharField(max_length=255, null=True)
    ordering = models.PositiveIntegerField()

    class Meta:
        app_label = 'epc'
        unique_together = ('ordering', 'order')

    def generate_note(self):
        try:
            self.note
        except EPCOrderNote.DoesNotExist:
            pass
        else:  # pragma: no cover
            return
        self.note = EPCOrderNote.objects.create(
            order=self.order,
            order_change=self,
            message=self.get_note_message()
        )
        return self.note

    def get_note_message(self):
        previous_change = self.get_previous_change()
        if previous_change is None:
            return "Created order."
        fields = [
            'order_type', 'order_method',
            'control_solution_request', 'meter_request', 'strips_request',
            'lancet_request', 'lancing_device_request', 'pamphlet_id_request',
            'meter_shipped', 'meid', 'strips_shipped', 'lancets_shipped',
            'control_solution_shipped', 'lancing_device_shipped',
            'pamphlet_id_shipped', 'order_status', 'tracking_number'
        ]
        message_lines = []
        for field in fields:
            field_name = clean_field_name(field)
            previous_value = getattr(previous_change, field)
            current_value = getattr(self, field)
            try:
                previous_value = int(previous_value)
                current_value = int(current_value)
            except (ValueError, TypeError):
                pass
            if previous_value == current_value:
                continue
            new_message = "{0} changed from {1} to {2}".format(
                field_name, previous_value, current_value)
            message_lines.append(new_message)
        # Check some date fields.
        for field in ['order_date', 'ship_date']:
            field_name = clean_field_name(field)
            previous_value = getattr(previous_change, field)
            current_value = getattr(self, field)
            if not isinstance(current_value, date):
                try:
                    current_value = parse(current_value)
                except:
                    pass
            if not isinstance(previous_value, date):
                try:
                    previous_value = parse(previous_value).date()
                except:
                    pass
            if previous_value == current_value:
                continue
            new_message = "{0} changed from {1} to {2}".format(
                field_name, previous_value, current_value)
            message_lines.append(new_message)
        return "\n".join(message_lines)

    def get_previous_change(self):
        if self.ordering == 0:
            return
        previous_changes = self.order.changes.filter(
            ordering__lt=self.ordering).order_by('-ordering')
        if previous_changes.count() > 0:
            return previous_changes[0]


@receiver(pre_save, sender=EPCOrderChange)
def populate_ordering(sender, instance, *args, **kwargs):
    if instance.id is None and instance.ordering is None:
        instance.ordering = instance.order.get_next_change_ordering()
