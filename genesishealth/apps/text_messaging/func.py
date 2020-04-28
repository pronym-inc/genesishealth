import re

from json import dumps

import requests

from requests.auth import HTTPBasicAuth

from genesishealth.apps.text_messaging.models import (
    TextMessagingConfiguration, TextMessageLogEntry)


def clean_phone_number(in_phone):
    cleaned_number = re.sub(r"\D", "", in_phone)
    cleaned_number = "1" + cleaned_number
    return cleaned_number


class ConnectionsAPIClient(object):
    MESSAGE_ENDPOINT_URL = "/messages/"

    def send_text(self, message, users):
        config = TextMessagingConfiguration.get_solo()
        url = "{0}{1}".format(
            config.end_point_url_base,
            self.MESSAGE_ENDPOINT_URL)
        auth = HTTPBasicAuth(
            config.header_username,
            config.header_password)
        payload = {
            "username": config.body_username,
            "password": config.body_password,
            "source": config.source_number,
            "message": message,
            "recipients": []
        }
        for user in users:
            phone = user.patient_profile.contact.phone
            if phone is None:
                continue
            cleaned_number = clean_phone_number(phone)
            payload["recipients"].append({
                "code": cleaned_number,
                "CodeID": user.id
            })
        data = dumps(payload)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            url,
            auth=auth,
            headers=headers,
            data=data,
            verify=config.verify_ssl)
        # Log it.
        log_entry = TextMessageLogEntry.objects.create(
            message=message,
            request_payload=data,
            response_content=response.content
        )
        for user in users:
            log_entry.recipients.add(user)
        return response
