from cogs.util.config import CONFIG
from cerberus import Validator
from smtplib import SMTP
from requests import post
from logger import get_logger

logger = get_logger(__name__)

class Email:
    def __init__(self, address: str):
        valid, address = Email.validate(address)

        if valid:
            self.address = address

    @staticmethod
    def validate(address: str) -> (bool, str):

        valid_regex = CONFIG["DEFAULT"]["valid_email_regex"]
        invalid_regex = CONFIG["DEFAULT"]["invalid_email_regex"]

        schema = {
            "address": {
                "type": "string",
                "required": True,
                "coerce": str,
                "minlength": 11,
                "maxlength": 100,
                "regex": valid_regex,
                "noneof": [{
                    "regex": invalid_regex
                }]
            }
        }

        validator = Validator(schema)
        result = validator.validate({"address": address})
        address = validator.document["address"]
        if validator.errors:
            raise Exception(f"Validation failed: {validator.errors}")
            logger.info(f'Invalid Email: {address}')

        student = address.split("@")[1] == CONFIG["DEFAULT"]["student_domain"]

        if student and not Email.student_address_exists(address):
            raise Exception(f"Email address does not exist: {address=}")
        elif not student and not Email.staff_address_exists(address):
            raise Exception(f"Email address does not exist: {address=}")

        return result, address

    @staticmethod
    def student_address_exists(email_address: str) -> bool:
        smtp = SMTP(CONFIG["DEFAULT"]["student_mail_server"])
        smtp.ehlo()
        smtp.docmd("MAIL", "FROM:<>")
        resp_code, _ = smtp.docmd("RCPT", f"TO:<{email_address}>")

        if resp_code != 250:
            return False
        else:
            return True

    @staticmethod
    def staff_address_exists(email_address: str) -> bool:
        split = email_address.split(".")
        first_name = split[0]
        last_name = split[1]

        url = CONFIG["DEFAULT"]["staff_search_url"]
        request_json = {"search_by_name": True,
                        "search_by_position": False, "search_term": f"{first_name} {last_name}"}
        res = post(url, json=request_json)

        staff_members = res.json()["staff"]

        emails = []
        for member in staff_members:
            emails.append(member["email_address"])

        return email_address in emails
