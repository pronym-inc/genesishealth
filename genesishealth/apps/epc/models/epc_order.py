from datetime import datetime, time

import pytz

from django.db import models
from django.utils.timezone import now

from genesishealth.apps.orders.models import (
    Order, OrderEntry, OrderShipment)
from genesishealth.apps.products.models import ProductType


class EPCOrder(models.Model):
    STATUS_SHIPPED = 'SHIPPED'

    datetime_added = models.DateTimeField(default=now)
    epc_member = models.ForeignKey(
        'accounts.PatientProfile', related_name='epc_orders', on_delete=models.CASCADE)
    original_transaction = models.ForeignKey(
        'OrderRequestTransaction', related_name='epc_orders', on_delete=models.CASCADE)
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
    order = models.ForeignKey(
        'orders.Order', related_name='epc_orders', null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = 'epc'

    def create_ght_order(self):
        if self.order is not None:
            return
        if self.is_shipped():
            order_status = Order.ORDER_STATUS_SHIPPED
        else:
            order_status = Order.ORDER_STATUS_WAITING_TO_BE_SHIPPED
        self.order = Order.objects.create(
            patient=self.epc_member.user,
            order_status=order_status,
            order_origin=Order.ORDER_ORIGIN_API,
            order_type=Order.ORDER_TYPE_PATIENT,
            fulfilled_by=self.epc_member.rx_partner
        )
        self.save()
        self.update_order_entries()
        self.update_order_shipping()

    def create_or_update_ght_order(self):
        print(self.order)
        if self.order is None:
            self.create_ght_order()
        else:
            self.update_ght_order()

    def get_next_change_ordering(self):
        qs = self.changes.order_by('-ordering')
        if qs.count() == 0:
            return 0
        return qs[0].ordering + 1

    def get_next_note_ordering(self):
        qs = self.notes.order_by('-ordering')
        if qs.count() == 0:
            return 0
        return qs[0].ordering + 1

    def is_shipped(self):
        print(self.order_status)
        return self.order_status == self.STATUS_SHIPPED

    def update_ght_order(self):
        if self.is_shipped():
            order_status = Order.ORDER_STATUS_SHIPPED
        else:
            order_status = Order.ORDER_STATUS_WAITING_TO_BE_SHIPPED
        self.order.order_status = order_status
        self.order.save()
        self.update_order_entries()
        self.update_order_shipping()

    def update_order_entries(self):
        # Clear out existing entries and recreate
        self.order.entries.all().delete()
        if self.is_shipped():
            meter_quantity = self.meter_shipped
            strip_quantity = self.strips_shipped
            lancet_quantity = self.lancets_shipped
            control_solution_quantity = self.control_solution_shipped
            lancing_device_quantity = self.lancing_device_shipped
            pamphlet_quantity = self.pamphlet_id_shipped
        else:
            meter_quantity = self.meter_request
            strip_quantity = self.strips_request
            lancet_quantity = self.lancet_request
            control_solution_quantity = self.control_solution_request
            lancing_device_quantity = self.lancing_device_request
            pamphlet_quantity = self.pamphlet_id_request
        type_quantities = {
            ProductType.CATEGORY_GDRIVE: meter_quantity,
            ProductType.CATEGORY_STRIPS: strip_quantity,
            ProductType.CATEGORY_LANCET: lancet_quantity,
            ProductType.CATEGORY_CONTROL_SOLUTION: control_solution_quantity,
            ProductType.CATEGORY_LANCING_DEVICE: lancing_device_quantity,
            ProductType.CATEGORY_PAMPHLET: pamphlet_quantity
        }
        for product_category, quantity in type_quantities.items():
            if quantity == 0 or quantity is None:
                continue
            typ = ProductType.objects.get(category=product_category)
            box_quantity = typ.convert_to_boxes(quantity)
            OrderEntry.objects.create(
                order=self.order,
                product=typ,
                quantity=box_quantity)

    def update_order_shipping(self):
        if self.order is None:
            return
        shipment = self.order.get_shipment()
        if self.is_shipped():
            if self.ship_date is not None:
                ship_dt = pytz.UTC.localize(
                    datetime.combine(self.ship_date, time()))
            else:
                ship_dt = None
            self.order.shipped_datetime = ship_dt
            self.order.save()
            if shipment is None:
                OrderShipment.objects.create(
                    order=self.order,
                    tracking_number=self.tracking_number,
                    shipped_date=self.ship_date,
                    is_finalized=True)
            else:
                shipment.tracking_number = self.tracking_number
                shipment.shipped_date = self.ship_date
                shipment.is_finalized = True
                shipment.save()
        else:
            if shipment is not None:
                shipment.delete()
