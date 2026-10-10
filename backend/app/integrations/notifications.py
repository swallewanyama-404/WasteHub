from typing import Protocol


class ExternalNotificationChannel(Protocol):
    def send(
        self,
        *,
        destination: str,
        title: str,
        message: str,
    ) -> None:
        ...


class NullNotificationChannel:
    """Safe default used when SMS/email credentials are not configured."""

    def send(
        self,
        *,
        destination: str,
        title: str,
        message: str,
    ) -> None:
        return None


def get_external_notification_channel() -> ExternalNotificationChannel:
    return NullNotificationChannel()
