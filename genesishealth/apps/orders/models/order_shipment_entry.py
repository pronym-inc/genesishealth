from django.db import models


class OrderShipmentEntry(models.Model):
    order_shipment = models.ForeignKey(
        'OrderShipment', related_name='entries', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, blank=True)
    product = models.ForeignKey(
        'products.ProductType', related_name="shipment_entries",
        blank=True, on_delete=models.CASCADE)
    expiration = models.DateField(null=True, blank=True)
    inventory_identifier = models.CharField(max_length=255, blank=True)
