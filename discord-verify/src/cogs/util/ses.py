from __future__ import annotations

import boto3  # type: ignore

from ...logger import get_logger
from ..datatypes.email_address import Email
from ..util.config import CONFIG

logger = get_logger(__name__)

client = boto3.client("ses")


def send_email(verification_code: str, email: Email) -> bool:

    logger.info(f"""
    To: {email.address}

    {verification_code}
    """)

    try:
        client.send_email(
            Source=CONFIG["DEFAULT"]["sender_address"],
            Destination={"ToAddresses": [
                f"{email.address}",
            ]},
            Message={
                "Subject": {
                    "Data": "Your MACS Verification Code",
                },
                "Body": {
                    "Text": {
                        "Data":
                        "Here is your verification code for the MACS "
                        f"Discord server:\n\n{verification_code}\n\nIf you "
                        "did not request this code, please ignore this email.",
                    }
                }
            })

        return True
    except Exception as e:
        logger.info(e)
        return False
