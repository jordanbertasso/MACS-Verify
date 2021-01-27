from __future__ import annotations
from cogs.datatypes.email_address import Email
from cerberus import Validator
from datetime import datetime
import copy


class Attempt:
    guild_id: str
    verification_code: str
    attempt_time: str
    email: Email

    def __init__(
            self,
            verification_code: str,
            guild_id: str,
            email: Email,
            attempt_time="") -> Attempt:
        if Attempt.is_valid(verification_code, guild_id):
            self.guild_id = guild_id
            self.verification_code = verification_code
            self.email = email

            if attempt_time:
                self.attempt_time = attempt_time
            else:
                self.attempt_time = str(datetime.now())

    @staticmethod
    def to_dict(attempt: Attempt) -> str:
        attempt_copy = copy.deepcopy(attempt)

        if attempt_copy.email:
            attempt_copy.email = attempt_copy.email.address

        return vars(attempt_copy)

    @staticmethod
    def is_valid(verification_code: str, guild_id: str) -> None:
        attempt_details = {
            "verification_code": verification_code,
            "guild_id": guild_id
        }

        schema = {
            "verification_code": {
                "type": "string",
                "required": True,
                "coerce": str,
                "minlength": 16,
                "maxlength": 16
            },
            "guild_id": {
                "type": "string",
                "required": True,
                "coerce": str,
                "maxlength": 50
            }
        }

        validator = Validator(schema)
        validator.validate(attempt_details)
        verification_code = validator.document["verification_code"]
        guild_id = validator.document["guild_id"]

        if validator.errors:
            raise Exception(f"Validation failed: {validator.errors}")

        return True

    def add_verification_code(self, verification_code: str) -> None:
        self.verification_code = verification_code
