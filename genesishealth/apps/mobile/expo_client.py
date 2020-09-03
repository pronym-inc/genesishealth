import logging
from dataclasses import dataclass

from exponent_server_sdk import PushClient, PushMessage, PushServerError, DeviceNotRegisteredError, PushResponseError

from genesishealth.apps.mobile.models import MobileNotification


logger = logging.getLogger('expo_client')


@dataclass
class ExpoNotificationResult:
    success: bool


class ExpoNotificationClient:
    def send_notification(self, notification: MobileNotification) -> ExpoNotificationResult:
        if notification.is_pushed:
            logger.warning("Attempted to push a notification that was already pushed.  Aborting...")
            return ExpoNotificationResult(success=False)
        if notification.profile.expo_push_token is None:
            logger.warning("Attempted to push a notification, but no token is configured for owner.  Aborting...")
            return ExpoNotificationResult(success=False)
        token: str = notification.profile.expo_push_token
        try:
            response = PushClient().publish(
                PushMessage(
                    to=token,
                    body=notification.message,
                    data={
                        'notification_id': notification.id
                    }
                )
            )
        except PushServerError as exc:
            logger.warning(f"Attempted to send a push notification, but received error: {exc}")
            return ExpoNotificationResult(success=False)

        try:
            response.validate_response()
        except DeviceNotRegisteredError:
            logger.warning("Attempted to send a push notification, but the device is not registered.")
            return ExpoNotificationResult(success=False)
        except PushResponseError as exc:
            logger.warning(f"Attempted to send a push notification, but received an error: {exc}")
            return ExpoNotificationResult(success=False)
        return ExpoNotificationResult(success=True)
