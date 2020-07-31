from django.db import models
from django.utils.timezone import localtime, now

from genesishealth.apps.products.models import ProductType

from .order_entry import OrderEntry
from .order_problem import OrderProblem


class Order(models.Model):
    ORDER_TYPE_PATIENT = 'patient'
    ORDER_TYPE_BULK = 'bulk'

    ORDER_TYPE_CHOICES = (
        (ORDER_TYPE_PATIENT, 'Patient'),
        (ORDER_TYPE_BULK, 'Bulk')
    )

    ORDER_STATUS_ON_HOLD = 'on hold'
    ORDER_STATUS_WAITING_TO_BE_SHIPPED = 'waiting to be shipped'
    ORDER_STATUS_IN_PROGRESS = 'in progress'
    ORDER_STATUS_WAITING_FOR_RX = 'waiting for pharmacy partner'
    ORDER_STATUS_PARTIALLY_SHIPPED = 'partially_shipped'
    ORDER_STATUS_SHIPPED = 'shipped'
    ORDER_STATUS_FULFILLED = 'fulfilled'
    ORDER_STATUS_PROBLEM = 'problem'
    ORDER_STATUS_CANCELED = 'canceled'

    ORDER_STATUS_CHOICES = (
        (ORDER_STATUS_ON_HOLD, 'On Hold'),
        (ORDER_STATUS_WAITING_TO_BE_SHIPPED, 'Waiting to be shipped'),
        (ORDER_STATUS_IN_PROGRESS, 'In progress'),
        (ORDER_STATUS_WAITING_FOR_RX, 'Waiting for pharmacy partner'),
        (ORDER_STATUS_PARTIALLY_SHIPPED, 'Partially Shipped'),
        (ORDER_STATUS_SHIPPED, 'Shipped'),
        (ORDER_STATUS_PROBLEM, 'Problem'),
        (ORDER_STATUS_FULFILLED, 'Fulfilled'),
        (ORDER_STATUS_CANCELED, 'Canceled')
    )

    ORDER_ORIGIN_ACCOUNT_CREATION = 'account creation'
    ORDER_ORIGIN_MANUAL = 'manual'
    ORDER_ORIGIN_AUTOMATIC_REFILL = 'automatic refill'
    ORDER_ORIGIN_BULK_ORDER = 'bulk order'
    ORDER_ORIGIN_BATCH_IMPORT = 'batch import'
    ORDER_ORIGIN_API = 'api'

    ORDER_ORIGIN_CHOICES = (
        (ORDER_ORIGIN_ACCOUNT_CREATION, 'Account Creation'),
        (ORDER_ORIGIN_MANUAL, 'Manually Ordered'),
        (ORDER_ORIGIN_AUTOMATIC_REFILL, 'Automatic Refill'),
        (ORDER_ORIGIN_BULK_ORDER, 'Bulk Order'),
        (ORDER_ORIGIN_BATCH_IMPORT, 'Batch Import')
    )

    patient = models.ForeignKey(
        'auth.User', null=True, related_name='orders', on_delete=models.SET_NULL)
    datetime_added = models.DateTimeField(default=localtime)
    added_by = models.ForeignKey(
        'auth.User', null=True, related_name='orders_added', on_delete=models.SET_NULL)
    category = models.ForeignKey('OrderCategory', null=True, related_name='+', on_delete=models.SET_NULL)
    adjudicated_date = models.DateField(null=True)
    is_claim_approved = models.BooleanField(default=False)
    exception = models.CharField(max_length=255)
    order_status = models.CharField(
        max_length=255,
        default=ORDER_STATUS_WAITING_TO_BE_SHIPPED,
        choices=ORDER_STATUS_CHOICES)
    is_complete = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(
        'auth.User', null=True, related_name='locked_orders', on_delete=models.SET_NULL)
    locked_datetime = models.DateTimeField(null=True)
    order_type = models.CharField(max_length=255, choices=ORDER_TYPE_CHOICES)
    order_origin = models.CharField(
        max_length=255, choices=ORDER_ORIGIN_CHOICES)
    datetime_shipped = models.DateTimeField(null=True)
    rx_partner = models.ForeignKey(
        'pharmacy.PharmacyPartner', null=True, related_name='orders', on_delete=models.SET_NULL)
    invoice_number = models.CharField(max_length=255, null=True)
    fulfilled_by = models.ForeignKey(
        'pharmacy.PharmacyPartner', null=True,
        related_name='orders_to_fulfill', on_delete=models.SET_NULL)
    order_notes = models.TextField(blank=True)
    delivery_priority = models.ForeignKey(
        'ShippingClass', null=True, related_name='+', on_delete=models.SET_NULL)

    cancellation_reason = models.CharField(max_length=255, null=True)
    canceled_by = models.ForeignKey('auth.User', null=True, related_name='+', on_delete=models.SET_NULL)
    canceled_datetime = models.DateTimeField(null=True)

    hold_reason = models.CharField(max_length=255, null=True)
    hold_requested_by = models.ForeignKey(
        'auth.User', null=True, related_name='+', on_delete=models.SET_NULL)
    hold_datetime = models.DateTimeField(null=True)

    def add_problem(self, category, description, added_by=None):
        OrderProblem.objects.create(
            order=self,
            category=category,
            description=description,
            added_by=added_by
        )
        self.order_status = self.ORDER_STATUS_PROBLEM
        self.save()

    def can_add_problem(self):
        return self.order_status in (
            self.ORDER_STATUS_WAITING_TO_BE_SHIPPED,
            self.ORDER_STATUS_IN_PROGRESS,
            self.ORDER_STATUS_WAITING_FOR_RX,
            self.ORDER_STATUS_SHIPPED)

    def can_be_canceled(self):
        statuses = (
            self.ORDER_STATUS_ON_HOLD,
            self.ORDER_STATUS_WAITING_TO_BE_SHIPPED,
            self.ORDER_STATUS_IN_PROGRESS,
            self.ORDER_STATUS_WAITING_FOR_RX,
            self.ORDER_STATUS_PARTIALLY_SHIPPED,
            self.ORDER_STATUS_SHIPPED,
            self.ORDER_STATUS_PROBLEM)
        return self.order_status in statuses

    def can_be_fulfilled(self):
        return self.order_status == self.ORDER_STATUS_FULFILLED

    def can_be_held(self):
        statuses = (self.ORDER_STATUS_WAITING_TO_BE_SHIPPED,)
        return self.order_status in statuses

    def can_be_unheld(self):
        return self.order_status == self.ORDER_STATUS_ON_HOLD

    def can_be_unlocked(self):
        return self.order_status == self.ORDER_STATUS_IN_PROGRESS

    def can_resolve_problem(self):
        return self.order_status == self.ORDER_STATUS_PROBLEM

    def cancel(self, cancellation_reason, canceled_by=None):
        assert self.can_be_canceled()
        self.order_status = self.ORDER_STATUS_CANCELED
        self.cancellation_reason = cancellation_reason
        self.canceled_by = canceled_by
        self.canceled_datetime = now()
        self.save()

    def check_if_shipped(self):
        if self.order_status != self.ORDER_STATUS_IN_PROGRESS:
            return
        self.order_status = self.ORDER_STATUS_SHIPPED
        self.datetime_shipped = now()
        self.save()

    def check_lock(self):
        if not self.is_locked:
            return
        since_locked = (now() - self.locked_datetime).total_seconds()
        if since_locked > 60 * 60 * 12:
            self.unlock()

    def check_problem_status(self):
        if self.problems.filter(is_resolved=False).count() == 0:
            self.order_status = self.ORDER_STATUS_WAITING_TO_BE_SHIPPED
            self.save()

    def clear_problem(self, new_status):
        self.order_status = new_status
        self.problem_category = None
        self.problem_description = ""
        self.save()

    def fulfill(self):
        assert self.can_be_fulfilled()
        self.order_status = self.ORDER_STATUS_FULFILLED
        self.save()

    def get_contents_display(self):
        output = []
        for product_name, quantity in self.get_entries_dict().items():
            output.append("{0} x {1}".format(quantity, product_name))
        return ", ".join(output)

    def get_control_solution_quantity(self):
        return self.get_quantity_by_category(
            ProductType.CATEGORY_CONTROL_SOLUTION)

    def get_entries_dict(self):
        output = {}
        for entry in self.entries.all():
            output.setdefault(entry.product.name, 0)
            output[entry.product.name] += entry.quantity
        return output

    def get_gdrive_quantity(self):
        return self.get_quantity_by_category(
            ProductType.CATEGORY_GDRIVE)

    def get_lancet_quantity(self):
        return self.get_quantity_by_category(
            ProductType.CATEGORY_LANCET)

    def get_lancing_device_quantity(self):
        return self.get_quantity_by_category(
            ProductType.CATEGORY_LANCING_DEVICE)

    def get_problem(self):
        problems = self.problems.filter(is_resolved=False)
        if problems.count() > 0:
            return problems[0]

    def get_quantity_by_category(self, category):
        try:
            return self.entries.get(product__category=category).quantity
        except OrderEntry.DoesNotExist:
            return 0

    def get_recipient_name(self):
        if self.rx_partner:
            return self.rx_partner.name
        if self.patient:
            return self.patient.get_reversed_name()

    def get_shipment(self):
        shipments = self.shipments.order_by('-shipped_date')
        if shipments.count() > 0:
            return shipments[0]

    def get_shipping_address(self):
        if self.is_patient_order():
            contact = self.patient.patient_profile.contact
            return {
                'name': "{0} {1}".format(
                    self.patient.first_name, self.patient.last_name),
                'address1': contact.address1,
                'address2': contact.address2,
                'city': contact.city,
                'state': contact.state,
                'zip': contact.zip
            }
        else:
            return {
                'name': self.rx_partner.name,
                'address1': self.rx_partner.address,
                'address2': self.rx_partner.address2,
                'city': self.rx_partner.city,
                'state': self.rx_partner.state,
                'zip': self.rx_partner.zip
            }

    def get_shipping_label(self):
        shipments = self.shipments.filter(is_finalized=True, shipping_label_url__isnull=False)
        if shipments.count() == 0:
            return
        shipment = shipments[0]
        return shipment.shipping_label_url

    def get_strips_quantity(self):
        return self.get_quantity_by_category(
            ProductType.CATEGORY_STRIPS)

    def get_tracking_number(self):
        shipment = self.get_shipment()
        if shipment is not None:
            return shipment.tracking_number

    def get_unshipped_entries_dict(self):
        entries_dict = self.get_entries_dict()
        for shipment in self.shipments.all():
            for entry in shipment.entries.all():
                if entry.product.name not in entries_dict:
                    continue
                entries_dict[entry.product.name] -= entry.quantity
                if entries_dict[entry.product.name] <= 0:
                    del entries_dict[entry.product.name]
        return entries_dict

    def has_shipping_label(self):
        return self.get_shipping_label() is not None

    def hold(self, hold_reason, held_by=None):
        assert self.can_be_held()
        self.order_status = self.ORDER_STATUS_ON_HOLD
        self.hold_reason = hold_reason
        self.hold_requested_by = held_by
        self.hold_datetime = now()
        self.save()

    def is_patient_order(self):
        return self.patient is not None

    def lock(self, locking_user):
        if self.is_locked:
            if self.locked_by != locking_user:
                raise Exception(
                    "Attempting to lock order that is already locked "
                    "by another user.")
            else:
                raise Exception("Already locked by this user.")
        self.is_locked = True
        self.locked_by = locking_user
        self.locked_datetime = now()
        self.order_status = self.ORDER_STATUS_IN_PROGRESS
        self.save()

    def resolve_problem(self, description, resolved_by):
        self.check_problem_status()
        if not self.can_resolve_problem():
            return
        problem = self.get_problem()
        if problem is None:
            return
        problem.resolve(description, resolved_by)
        self.check_problem_status()

    def unhold(self):
        assert self.can_be_unheld()
        self.order_status = self.ORDER_STATUS_WAITING_TO_BE_SHIPPED
        self.save()

    def unlock(self):
        if not self.is_locked:
            return
        self.is_locked = False
        self.locked_by = None
        self.locked_datetime = None
        self.order_status = self.ORDER_STATUS_WAITING_TO_BE_SHIPPED
        self.save()
