from dateutil.parser import parse

from restless.exceptions import BadRequest
from restless.preparers import FieldsPreparer

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.epc.models import (
    EPCOrder, EPCOrderChange, EPCOrderNote, OrderRequestTransaction)
from genesishealth.apps.epc.views.api import error_messages
from genesishealth.apps.epc.views.api.base import BaseEPCTransactionResource
from genesishealth.apps.gdrives.models import GDrive


def try_parse_date(dt_str):
    try:
        assert dt_str not in ('', None)
        return parse(dt_str).date()
    except (AssertionError, ValueError):
        pass


class OrderRequestTransactionResource(BaseEPCTransactionResource):
    log_transaction_type = 'order'

    preparer = FieldsPreparer(fields={
        'success': 'is_successful',
        'epc_member_id': 'epc_member_identifier',
        'transaction_id': 'transaction_identifier',
        'genesis_id': 'epc_member.user.id'
    })

    def create(self):
        order_data = self.data['Order']

        # Verify that epc_member_identifier exists
        try:
            member = PatientProfile.objects.get(
                epc_member_identifier=order_data['epc_member_id'])
        except PatientProfile.DoesNotExist:
            raise BadRequest(error_messages.ORDER_NO_MATCH_FOR_EPC_MEMBER)

        # Get the device, if there is one.
        assign_device = False
        device = None
        if order_data['meid']:
            existing_device = member.get_device()
            if existing_device and existing_device.meid == order_data['meid']:
                device = existing_device
            else:
                try:
                    device = GDrive.objects.filter(
                        status=GDrive.DEVICE_STATUS_AVAILABLE
                    ).get(meid=order_data['meid'])
                except GDrive.DoesNotExist:
                    raise BadRequest(error_messages.ORDER_GDRIVE_NOT_AVAILABLE)
                else:
                    assign_device = True
        # Validation complete.
        try:
            order = EPCOrder.objects.get(
                order_number=order_data['order_no'])
        except EPCOrder.DoesNotExist:
            order = None
        # Assign device
        if assign_device and order_data['meid']:
            device.register(member.user)

        # Strip password out of raw data.
        raw_data = self.request.body

        self.transaction = OrderRequestTransaction.objects.create(
            submitted_username=self.data['username'],
            epc_member=member,
            authenticated_user=self.get_api_user(),
            raw_request=raw_data,
            transaction_identifier=order_data['transaction_id'],
            transaction_type=order_data['transaction_type'],
            epc_member_identifier=order_data['epc_member_id'],
            order_number=order_data['order_no'],
            order_type=order_data['order_type'],
            order_method=order_data['order_method'],
            order_date=try_parse_date(order_data['order_date']),
            meter_request=order_data['meter_request'],
            strips_request=order_data['strips_request'],
            lancet_request=order_data['lancet_request'],
            lancing_device_request=order_data['lancing_device_request'],
            pamphlet_id_request=order_data['pamphlet_id_request'],
            control_solution_request=order_data['control_solution_request'],
            meter_shipped=order_data['meter_shipped'],
            meid=order_data['meid'],
            strips_shipped=order_data['strips_shipped'],
            lancets_shipped=order_data['lancets_shipped'],
            control_solution_shipped=order_data['control_solution_shipped'],
            lancing_device_shipped=order_data['lancing_device_shipped'],
            pamphlet_id_shipped=order_data['pamphlet_id_shipped'],
            order_status=order_data['order_status'],
            ship_date=try_parse_date(order_data['ship_date']),
            tracking_number=order_data['tracking_no'],
            is_successful=True
        )

        # Create or update order.
        if order is None:
            order = EPCOrder.objects.create(
                original_transaction=self.transaction,
                epc_member_identifier=order_data['epc_member_id'],
                epc_member=member,
                order_number=order_data['order_no'],
                order_type=order_data['order_type'],
                order_method=order_data['order_method'],
                order_date=try_parse_date(order_data['order_date']),
                meter_request=order_data['meter_request'],
                strips_request=order_data['strips_request'],
                lancet_request=order_data['lancet_request'],
                lancing_device_request=order_data['lancing_device_request'],
                pamphlet_id_request=order_data['pamphlet_id_request'],
                control_solution_request=order_data[
                    'control_solution_request'],
                meter_shipped=order_data['meter_shipped'],
                meid=order_data['meid'],
                strips_shipped=order_data['strips_shipped'],
                lancets_shipped=order_data['lancets_shipped'],
                control_solution_shipped=order_data[
                    'control_solution_shipped'],
                lancing_device_shipped=order_data['lancing_device_shipped'],
                pamphlet_id_shipped=order_data['pamphlet_id_shipped'],
                order_status=order_data['order_status'],
                ship_date=try_parse_date(order_data['ship_date']),
                tracking_number=order_data['tracking_no']
            )
        else:
            # Two tuple of API field, EPCOrder field
            update_fields = (
                ('order_no', 'order_number'),
                ('order_type', 'order_type'),
                ('order_method', 'order_method'),
                ('meter_request', 'meter_request'),
                ('strips_request', 'strips_request'),
                ('lancet_request', 'lancet_request'),
                ('pamphlet_id_request', 'pamphlet_id_request'),
                ('meter_shipped', 'meter_shipped'),
                ('meid', 'meid'),
                ('strips_shipped', 'strips_shipped'),
                ('lancets_shipped', 'lancets_shipped'),
                ('control_solution_request', 'control_solution_request'),
                ('control_solution_shipped', 'control_solution_shipped'),
                ('lancing_device_shipped', 'lancing_device_shipped'),
                ('pamphlet_id_shipped', 'pamphlet_id_shipped'),
                ('order_status', 'order_status'),
                ('tracking_no', 'tracking_number')
            )
            for api_field, order_field in update_fields:
                setattr(order, order_field, order_data[api_field])
            order.order_date = try_parse_date(order_data['order_date'])
            order.ship_date = try_parse_date(order_data['ship_date'])
            order.save()

        order.create_or_update_ght_order()

        # Create order change
        change = EPCOrderChange.objects.create(
            transaction=self.transaction,
            order=order,
            epc_member_identifier=order_data['epc_member_id'],
            epc_member=member,
            order_number=order_data['order_no'],
            order_type=order_data['order_type'],
            order_method=order_data['order_method'],
            order_date=order_data['order_date'],
            meter_request=order_data['meter_request'],
            strips_request=order_data['strips_request'],
            lancet_request=order_data['lancet_request'],
            lancing_device_request=order_data['lancing_device_request'],
            pamphlet_id_request=order_data['pamphlet_id_request'],
            meter_shipped=order_data['meter_shipped'],
            meid=order_data['meid'],
            strips_shipped=order_data['strips_shipped'],
            lancets_shipped=order_data['lancets_shipped'],
            control_solution_shipped=order_data[
                'control_solution_shipped'],
            control_solution_request=order_data['control_solution_request'],
            lancing_device_shipped=order_data['lancing_device_shipped'],
            pamphlet_id_shipped=order_data['pamphlet_id_shipped'],
            order_status=order_data['order_status'],
            ship_date=order_data['ship_date'],
            tracking_number=order_data['tracking_no']
        )
        change.generate_note()
        return self.transaction

    def get_transaction_id(self):
        data = self.get_deserialized_data()
        return data['Order']['transaction_id']

    def handle_error(self, err):
        error = super(OrderRequestTransactionResource, self).handle_error(err)
        # See if we can tie this to a patient / order.
        if 'Order' in self.data and 'order_no' in self.data['Order']:
            try:
                order = EPCOrder.objects.get(
                    order_number=self.data['Order']['order_no'])
            except EPCOrder.DoesNotExist:
                pass
            else:
                # Create a note.
                message = "FAILED API REQUEST: {0}".format(self.data)
                message += "\n\nResponse Sent: {0}".format(error.content)
                EPCOrderNote.objects.create(order=order, message=message)
        return error
