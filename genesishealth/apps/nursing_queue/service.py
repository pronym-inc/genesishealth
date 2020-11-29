from datetime import timedelta

from django.utils.timezone import now

from genesishealth.apps.accounts.models import PatientProfile
from genesishealth.apps.nursing.models import NursingGroup
from genesishealth.apps.nursing_queue.models import NursingQueueEntry


class NursingQueueService:
    """A service for populating the nursing queue for nurses, based
    on the behavior of patients in their watch list."""
    def populate(self):
        for patient in PatientProfile.objects.filter(
                account_status=PatientProfile.ACCOUNT_STATUS_ACTIVE):
            self._populate_queue_entries_for_patient(patient)

    def _populate_queue_entries_for_patient(self, patient: PatientProfile) -> None:
        """Populate all queue entries for the given patient."""
        nursing_group = patient.get_nursing_group()
        if nursing_group is None:
            return
        print(f"Checking {patient}")
        self._check_if_readings_too_high(patient, nursing_group)
        self._check_if_readings_too_low(patient, nursing_group)
        self._check_if_not_enough_readings(patient, nursing_group)

    def _check_if_readings_too_high(
            self,
            patient: PatientProfile,
            nursing_group: NursingGroup
    ) -> None:
        # See if we have already made such a notification in the past
        # week for the patient.
        existing_entries = nursing_group.nursing_queue_entries.filter(
            patient=patient,
            entry_type=NursingQueueEntry.ENTRY_TYPE_READINGS_TOO_HIGH,
            datetime_added__gt=now() - timedelta(days=7)
        )
        # Abort if we do
        if len(existing_entries) > 0:
            return
        interval = patient.get_readings_too_high_interval()
        cutoff = now() - timedelta(days=interval)
        too_high_threshold = patient.get_readings_too_high_threshold()
        too_high_limit = patient.get_readings_too_high_limit()
        readings = patient.user.glucose_readings.filter(
            reading_datetime_utc__gt=cutoff,
            glucose_value__gte=too_high_threshold
        )
        if len(readings) >= too_high_limit:
            NursingQueueEntry.objects.create(
                nursing_group=nursing_group,
                patient=patient,
                entry_type=NursingQueueEntry.ENTRY_TYPE_READINGS_TOO_HIGH,
                due_date=(now() + timedelta(days=7)).date()
            )

    def _check_if_readings_too_low(
            self,
            patient: PatientProfile,
            nursing_group: NursingGroup
    ) -> None:
        # See if we have already made such a notification in the past
        # week for the patient.
        existing_entries = nursing_group.nursing_queue_entries.filter(
            patient=patient,
            entry_type=NursingQueueEntry.ENTRY_TYPE_READINGS_TOO_LOW,
            datetime_added__gt=now() - timedelta(days=7)
        )
        # Abort if we do
        if len(existing_entries) > 0:
            return
        interval = patient.get_readings_too_low_interval()
        cutoff = now() - timedelta(days=interval)
        too_low_threshold = patient.get_readings_too_low_threshold()
        too_low_limit = patient.get_readings_too_low_limit()
        readings = patient.user.glucose_readings.filter(
            reading_datetime_utc__gt=cutoff,
            glucose_value__lte=too_low_threshold
        )
        if len(readings) >= too_low_limit:
            NursingQueueEntry.objects.create(
                nursing_group=nursing_group,
                patient=patient,
                entry_type=NursingQueueEntry.ENTRY_TYPE_READINGS_TOO_LOW,
                due_date=(now() + timedelta(days=7)).date()
            )

    def _check_if_not_enough_readings(
            self,
            patient: PatientProfile,
            nursing_group: NursingGroup
    ) -> None:
        # See if we have already made such a notification in the past
        # week for the patient.
        existing_entries = nursing_group.nursing_queue_entries.filter(
            patient=patient,
            entry_type=NursingQueueEntry.ENTRY_TYPE_NOT_ENOUGH_RECENT_READINGS,
            datetime_added__gt=now() - timedelta(days=7)
        )
        # Abort if we do
        if len(existing_entries) > 0:
            return
        interval = patient.get_not_enough_recent_readings_interval()
        cutoff = now() - timedelta(days=interval)
        limit = patient.get_not_enough_recent_readings_minimum()
        readings = patient.user.glucose_readings.filter(reading_datetime_utc__gt=cutoff)
        if len(readings) < limit:
            NursingQueueEntry.objects.create(
                nursing_group=nursing_group,
                patient=patient,
                entry_type=NursingQueueEntry.ENTRY_TYPE_NOT_ENOUGH_RECENT_READINGS,
                due_date=(now() + timedelta(days=7)).date()
            )
