from django.db import models


class OrderEntry(models.Model):
    order = models.ForeignKey('Order', related_name='entries', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    product = models.ForeignKey(
        'products.ProductType', related_name='order_entries', on_delete=models.CASCADE)
    is_fulfilled = models.BooleanField(default=False)
    invoice_number = models.CharField(max_length=255)
