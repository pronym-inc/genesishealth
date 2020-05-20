import os
import time
import sys
import socket
import traceback
import re

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.timezone import now

from genesishealth.external.middleman.parse import verified
from genesishealth.apps.gdrives.models import GDriveTransmissionLogEntry
from genesishealth.apps.readings.models import GlucoseReading
from genesishealth.apps.readings.tasks import forward_reading


class Command(BaseCommand):
    args = ''
    help = 'Processes readings coming in over stdin and sends them to 0MQ'

    def log(self, message):
        try:
            encoded_message = str(message)
        except UnicodeDecodeError:
            encoded_message = ''
        sys.stderr.write("%s: %s\n" % (now(), encoded_message))
        sys.stderr.flush()

    def handle(self, *args, **kwargs):
        # Verify we have the right settings configured.
        for setting_name in ('GDRIVE_READING_PORT',
                             'GDRIVE_READING_DATA_LENGTH',
                             'GDRIVE_DECRYPTION_KEY',
                             'GDRIVE_TCP_SIMULTANEOUS_CONNECTIONS'):
            if not hasattr(settings, setting_name):
                raise Exception(
                    '%s must be configured in settings.' % setting_name)
        self.server_name = socket.gethostname()
        self.log('creating TCP listener on %s on %s' % (
            settings.GDRIVE_READING_PORT, self.server_name))
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Retry listening
        while True:
            try:
                self.serv.bind((settings.SPY_BIND_ADDRESS,
                                settings.GDRIVE_READING_PORT))
            except socket.error:
                print('retrying')
                time.sleep(5)
            else:
                break

        self.serv.listen(settings.GDRIVE_TCP_SIMULTANEOUS_CONNECTIONS)
        self.loop()

    def send_to_client(self, connection, message):
        self.log('sending to client: %s' % message)
        connection.send(message)

    def loop(self):
        while True:
            # Check for new connections.
            conn, addr = self.serv.accept()
            content = conn.recv(settings.GDRIVE_READING_DATA_LENGTH).decode('ascii')
            if len(content) > 0:
                self.log("**************BEGINNING OF READING**************")
                self.log('received content: %s' % content)
                self.log('remote: read %d bytes\n' % len(content))
                # Log it.
                log_entry = GDriveTransmissionLogEntry(
                    content=content, reading_server=self.server_name,
                    success_sent_to_client=False, processing_succeeded=False)
                if len(content) == settings.GDRIVE_READING_DATA_LENGTH:
                    self.log(
                        'remote: pid: %d, buffer size: %d, content: %s...' %
                            (os.getpid(), len(content), content[:75]))
                    if verified(content, settings.GDRIVE_DECRYPTION_KEY):
                        self.log('reading verified, processing...')
                        try:
                            results = GlucoseReading.process_reading(
                                content, self.server_name)
                            success, decrypted_data, error_message,\
                                reading, patient = results
                        except Exception:
                            tb = traceback.format_exc()
                            log_entry.error = tb
                            log_entry.resolution = \
                                GDriveTransmissionLogEntry\
                                .RESOLUTION_PROCESSING_FAILED
                            self.log(
                                'invalid reading or other error; sending '
                                'failures: %s' % tb)
                            self.send_to_client(conn, 'fail')
                        else:
                            self.log(
                                'local: reading successfully parsed and saved.'
                            )
                            log_entry.processing_succeeded = success
                            log_entry.decrypted_content = decrypted_data
                            log_entry.success_sent_to_client = True
                            log_entry.error = error_message
                            log_entry.meid = decrypted_data.get('meid')
                            log_entry.reading = reading
                            if patient:
                                log_entry.associated_patient_profile = \
                                    patient.patient_profile
                            if success:
                                log_entry.resolution = \
                                    GDriveTransmissionLogEntry.RESOLUTION_VALID
                            else:
                                error_messages = {
                                    'Duplicate reading.':
                                        GDriveTransmissionLogEntry
                                        .RESOLUTION_DUPLICATE,
                                    'Invalid device.':
                                        GDriveTransmissionLogEntry
                                        .RESOLUTION_UNKNOWN_DEVICE,
                                    'Invalid measure type.':
                                        GDriveTransmissionLogEntry
                                        .RESOLUTION_INVALID_MEASURE,
                                    'Device not associated with patient.':
                                        GDriveTransmissionLogEntry
                                        .RESOLUTION_NO_PATIENT
                                }
                                # Strip off message from error message.
                                clean_error_message = re.sub(
                                    "Reading processing failed with error: ",
                                    "",
                                    error_message)
                                # Append the right text.
                                log_entry.resolution = error_messages.get(
                                    clean_error_message,
                                    GDriveTransmissionLogEntry
                                    .RESOLUTION_UNRESOLVED)
                            self.log('Message: %s' % error_message)
                            self.log('Resolved as: %s' % log_entry.resolution)
                            self.log('decrypted data: %s' % decrypted_data)
                            self.send_to_client(conn, 'success')
                    else:
                        msg = ('local: decryption or checksum failure; '
                               'sending failure to client')
                        self.log(msg)
                        log_entry.error = msg
                        log_entry.resolution = \
                            GDriveTransmissionLogEntry.RESOLUTION_INVALID
                        self.send_to_client(conn, 'fail')
                else:
                    log_entry.resolution = \
                        GDriveTransmissionLogEntry.RESOLUTION_INVALID
                log_entry.save()
            conn.close()
            if len(content) > 0:
                self.log('Forwarding reading')
                try:
                    forward_reading.delay(content)
                except socket.error:
                    self.log(
                        "Could not connect to MQ server to forward reading.")
                else:
                    self.log("Successfully sent task to forward reading.")
                self.log("**************END OF READING**************\n\n\n")
            time.sleep(0.05)
