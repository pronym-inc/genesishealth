from dateutil.parser import parse

from django.contrib.auth import get_user_model
from django.db.models import Q

from restless.exceptions import BadRequest
from restless.preparers import FieldsPreparer

from genesishealth.apps.accounts.models import Company, PatientProfile
from genesishealth.apps.epc.views.api import error_messages
from genesishealth.apps.epc.models import PatientRequestTransaction
from genesishealth.apps.epc.views.api.base import BaseEPCTransactionResource
from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.pharmacy.models import PharmacyPartner


User = get_user_model()


class PatientRequestTransactionResource(BaseEPCTransactionResource):
    log_transaction_type = 'patient'

    preparer = FieldsPreparer(fields={
        'success': 'is_successful',
        'epc_member_id': 'epc_member_identifier',
        'transaction_id': 'transaction_identifier',
        'genesis_id': 'epc_member.user.id'
    })

    def create(self):
        patient_data = self.data['Patient']
        gid = patient_data['group_id']
        try:
            company = Company.objects.get(group_identifier=gid)
        except Company.DoesNotExist:
            raise BadRequest(error_messages.PATIENT_GROUP_NONEXISTENT)
        else:
            group = company.group
        fid = patient_data['fulfillment_id']
        try:
            fulfillment_identifier = PharmacyPartner.objects.get(
                epc_identifier=fid)
        except PharmacyPartner.DoesNotExist:
            raise BadRequest(error_messages.PATIENT_PHARMACY_NONEXISTENT)
        nid = patient_data['nursing_id']
        if nid is not None:
            try:
                nursing_identifier = NursingGroup.objects.get(
                    epc_identifier=nid)
            except NursingGroup.DoesNotExist:
                raise BadRequest(
                    error_messages.PATIENT_NURSING_NONEXISTENT)
        else:
            nursing_identifier = None

        # Find existing member if they exist.
        profile = None
        try:
            profile = PatientProfile.objects.get(
                epc_member_identifier=patient_data['epc_member_id'])
        except PatientProfile.DoesNotExist:
            # Did not find an account, but let's see if we can match
            # on name and dob for a patient with null EPC identifier
            # this will let us update epc IDs.
            if (all([patient_data['first_name'],
                     patient_data['last_name'],
                     patient_data['date_of_birth']])):
                dob = parse(patient_data['date_of_birth']).date()
                try:
                    profile = company.patients.get(
                        user__first_name=patient_data['first_name'],
                        user__last_name=patient_data['last_name'],
                        date_of_birth=dob)
                except PatientProfile.DoesNotExist:
                    pass

        account_status = patient_data.get('memberStatus', 'active')
        # If we don't have a profile, then account status should
        # not be termed.
        if profile is None and account_status == 'termed':
            raise BadRequest(
                "New patients cannot be created with termed status.")

        # If we didn't find a profile, then we'll create a new one.
        # otherwise, we'll update
        if profile is None:
            # Verify user with email doesn't exist
            if patient_data['email_address']:
                email = patient_data['email_address']
                if (User.objects.filter(
                        Q(username=email) | Q(email=email)).count() > 0):
                    raise BadRequest(error_messages.PATIENT_EMAIL_EXISTS)

            kwargs = {
                'first_name': patient_data['first_name'] or '',
                'last_name': patient_data['last_name'] or '',
                'email': patient_data['email_address'],
                'address1': patient_data['address1'],
                'address2': patient_data['address2'],
                'city': patient_data['city'],
                'state': patient_data['state'],
                'zip': patient_data['zipcode'],
                'group': group,
                'company': company,
                'date_of_birth': patient_data['date_of_birth'],
                'email_password': False,
                'rx_partner': fulfillment_identifier,
                'nursing_group': nursing_identifier,
                'epc_member_identifier': patient_data['epc_member_id']
            }

            if group.is_no_pii:
                kwargs['username'] = patient_data['epc_member_id']
            elif patient_data['first_name'] and patient_data['last_name']:
                base_username = "{0}.{1}".format(
                    patient_data['first_name'].lower(),
                    patient_data['last_name'].lower())
                counter = 0
                while True:
                    if counter == 0:
                        username = base_username
                    else:
                        username = "{0}{1}".format(base_username, counter)
                    try:
                        User.objects.get(username=username)
                    except User.DoesNotExist:
                        break
                    counter += 1
                kwargs['username'] = username
            # Create the member.
            patient = PatientProfile.myghr_patients.create_user(**kwargs)
            # Add the phone number.
            if patient_data['phone']:
                patient.patient_profile.contact.add_phone(
                    patient_data['phone'])
        else:
            # Update existing profile.
            user = profile.user
            contact = profile.contact
            # Verify another user with email doesn't exist
            if patient_data['email_address']:
                email = patient_data['email_address']
                if (User.objects.exclude(id=profile.user.pk).filter(
                        Q(username=email) | Q(email=email)).count() > 0):
                    raise BadRequest(error_messages.PATIENT_EMAIL_EXISTS)

            contact.first_name = user.first_name = \
                patient_data['first_name'] or ''
            contact.last_name = user.last_name = \
                patient_data['last_name'] or ''

            user.email = patient_data['email_address'] or ''

            contact.address1 = patient_data['address1']
            contact.address2 = patient_data['address2']
            contact.city = patient_data['city']
            contact.state = patient_data['state']
            contact.zip = patient_data['zipcode']

            profile.date_of_birth = patient_data['date_of_birth']
            profile.epc_member_identifier = patient_data['epc_member_id']

            if patient_data['phone']:
                contact.set_phone(patient_data['phone'])

            user.save()
            contact.save()
            profile.save()
            patient = user

            # Update status, if necessary.
            if (account_status == 'termed' and
                    profile.account_status !=
                    PatientProfile.ACCOUNT_STATUS_TERMED):
                profile.change_account_status(
                    PatientProfile.ACCOUNT_STATUS_TERMED)
            elif (account_status == 'active' and
                    profile.account_status !=
                    PatientProfile.ACCOUNT_STATUS_ACTIVE):
                profile.change_account_status(
                    PatientProfile.ACCOUNT_STATUS_ACTIVE)

        self.transaction = PatientRequestTransaction.objects.create(
            submitted_username=self.data['username'],
            authenticated_user=self.get_api_user(),
            raw_request=self.request.body,
            transaction_identifier=patient_data['transaction_id'],
            transaction_type=patient_data['transaction_type'],
            epc_member_identifier=patient_data['epc_member_id'],
            epc_member=patient.patient_profile,
            group_identifier_raw=patient_data['group_id'],
            group_identifier=company,
            fulfillment_identifier_raw=patient_data['fulfillment_id'],
            fulfillment_identifier=fulfillment_identifier,
            nursing_identifier_raw=patient_data['nursing_id'],
            nursing_identifier=nursing_identifier,
            first_name=patient_data['first_name'],
            last_name=patient_data['last_name'],
            address1=patient_data['address1'],
            address2=patient_data['address2'],
            city=patient_data['city'],
            state=patient_data['state'],
            zipcode=patient_data['zipcode'],
            phone=patient_data['phone'],
            date_of_birth=patient_data['date_of_birth'],
            email_address=patient_data['email_address'],
            is_successful=True
        )

        return self.transaction
