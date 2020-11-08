from __future__ import annotations
from cerberus import Validator, TypeDefinition
from cogs.datatypes.attempt import Attempt
import datetime
import copy

# Define a custom attempt type for cerberus validatio
attempt_type = TypeDefinition("attempt", (Attempt,), ())
Validator.types_mapping["attempt"] = attempt_type


class User:
    user_id: str
    name: str
    discriminator: str
    status: str
    attempts: [Attempt]

    def __init__(
            self,
            user_id: str,
            name: str,
            discriminator: str,
            status: str,
            attempts: list = []) -> User:

        user_details = {
            "user_id": user_id,
            "name": name,
            "discriminator": discriminator,
            "status": status
        }

        valid, user_details = User.validate(user_details)
        if valid:
            self.user_id: str = user_details["user_id"]
            self.name: str = user_details["name"]
            self.discriminator: str = user_details["discriminator"]
            self.status = user_details["status"]

        if attempts:
            self.attempts: [Attempt] = attempts
        else:
            self.attempts: [Attempt] = []

    @staticmethod
    def to_dict(user: User) -> str:
        user_copy = copy.deepcopy(user)
        if user_copy.attempts:
            user_copy.attempts = [Attempt.to_dict(
                attempt) for attempt in user_copy.attempts]

        return vars(user_copy)

    @staticmethod
    def validate(user_details: dict) -> (bool, dict):

        schema = {
            "user_id": {
                "type": "string",
                "required": True,
                "coerce": str,
                "minlength": 10,
                "maxlength": 20
            },
            "name": {
                "type": "string",
                "required": True
            },
            "discriminator": {
                "type": "string",
                "required": True,
                "coerce": str
            },
            "status": {
                "type": "string"
            }
        }

        validator = Validator(schema)
        result = validator.validate(user_details)
        user_details = validator.document
        if validator.errors:
            raise Exception(f"Validation failed: {validator.errors}")

        return result, user_details

    def add_attempt(self, attempt: Attempt) -> None:
        self.attempts.append(attempt)

    def get_earliest_attempt(self) -> Attempt or None:
        earliest_attempt = None
        earliest_time = datetime.datetime.max

        if self.attempts:
            for attempt in self.attempts:
                current_time = datetime.datetime.fromisoformat(
                    attempt.attempt_time)
                if current_time < earliest_time:
                    earliest_time = current_time
                    earliest_attempt = attempt

        return earliest_attempt

    def get_latest_attempt(self) -> Attempt or None:
        latest_attempt = None
        latest_time = datetime.datetime.min

        if self.attempts:
            for attempt in self.attempts:
                current_time = datetime.datetime.fromisoformat(
                    attempt.attempt_time)
                if current_time > latest_time:
                    latest_time = current_time
                    latest_attempt = attempt

        return latest_attempt

    def verify_attempt(self, verification_code: str) -> bool:
        for attempt in self.attempts:
            if attempt.verification_code == verification_code:
                attempt.status = "verified"
                return True
            else:
                return False
