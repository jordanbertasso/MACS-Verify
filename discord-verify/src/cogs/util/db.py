from __future__ import annotations

from os import environ
from typing import Dict, List, Optional, Union

# import discord  # type: ignore
from discord import Guild, Member  # type: ignore
from pymongo import MongoClient  # type: ignore

from ...logger import get_logger
from ..datatypes.attempt import Attempt
from ..datatypes.email_address import Email
from ..datatypes.user import User
from ..util.config import CONFIG

logger = get_logger(__name__)
logger.info("Waiting for DB connection.")

db_host = environ["DB_HOST"]
client = MongoClient(host=db_host)

try:
    if environ["DROP_DATABASE"] == "1":
        client.drop_database("discord_email_verification_bot_db")
except KeyError:
    logger.info("Keeping existing database")

db = client.get_database(CONFIG["DEFAULT"]["db_name"])
waiting_collection = db.get_collection("waiting_for_verify")


def set_exec_role(guild_id: str, role_id: str) -> bool:
    collection = db.get_collection(str(guild_id))
    existing_role_id: str = get_exec_role(guild_id)

    if existing_role_id:
        return False
    else:
        collection.insert_one({'_id': 'exec_role_id', 'id': str(role_id)})
        return True


def get_exec_role(guild_id: str) -> str:
    collection = db.get_collection(str(guild_id))
    res = collection.find_one({"_id": "exec_role_id"})

    if res:
        channel_id = res['id']
        return channel_id
    else:
        return ''


def set_verify_channel(guild_id: str, channel_id: str) -> bool:
    collection = db.get_collection(str(guild_id))

    existing_channel_id = get_verify_channel(guild_id)

    if existing_channel_id:
        return False
    else:
        collection.insert_one({
            '_id': 'verify_channel_id',
            'id': str(channel_id)
        })
        return True


def get_verify_channel(guild_id: str) -> str:
    collection = db.get_collection(str(guild_id))
    res = collection.find_one({"_id": "verify_channel_id"})

    if res:
        channel_id = res['id']
        return channel_id
    else:
        return ''


def set_verified_role_id(guild_id: str, role_id: str) -> None:
    collection = db.get_collection(str(guild_id))
    existing_role_id = get_verified_role_id(guild_id)

    if existing_role_id:
        return
    else:
        collection.insert_one({"_id": "verified_role_id", "id": str(role_id)})


def get_verified_role_id(guild_id: str) -> str:
    collection = db.get_collection(str(guild_id))
    res = collection.find_one({"_id": "verified_role_id"})

    if res:
        role_id = res["id"]
        return role_id
    else:
        return ""


def get_waiting_user_details(user_id: str) -> Optional[Dict]:
    waiting_user = waiting_collection.find_one({"user_id": user_id})

    return waiting_user


def save_user(user: User, guild_id: str) -> None:
    collection = db.get_collection(str(guild_id))
    existing_user = collection.find_one({"user_id": user.user_id})

    user_dict = User.to_dict(user)
    if existing_user:
        collection.replace_one({"user_id": user.user_id}, user_dict)
    else:
        collection.insert_one(user_dict)


def delete_user(user_id: str, guild_id: str) -> None:
    collection = db.get_collection(str(guild_id))
    collection.delete_one({"user_id": user_id})
    collection.delete_one({
        "_id": "guild_emails",
        "emails": {
            "$elemMatch": {
                "user_id": {
                    "$eq": user_id
                }
            }
        }
    })


def add_to_waiting(user: User, guild_id: str) -> None:
    waiting_user = waiting_collection.find_one({"user_id": user.user_id})

    if not waiting_user:
        waiting_collection.insert_one({
            "user_id": user.user_id,
            "guild_id": guild_id,
            "name": user.name,
            "discriminator": user.discriminator
        })
    else:
        waiting_collection.replace_one({"user_id": user.user_id}, {
            "user_id": user.user_id,
            "guild_id": guild_id,
            "name": user.name,
            "discriminator": user.discriminator
        })


def remove_from_waiting(user_id: str) -> None:
    waiting_collection.delete_one({"user_id": user_id})


def get_user(user_id: str, guild_id="", user_details={}) -> Optional[User]:
    user_dict = {}

    if guild_id:
        guild_collection = db.get_collection(str(guild_id))
        user_dict = guild_collection.find_one({"user_id": user_id})
    else:
        waiting_user = waiting_collection.find_one({"user_id": user_id})
        if waiting_user:
            guild_id = waiting_user["guild_id"]
            guild_collection = db.get_collection(str(guild_id))
            user_dict = guild_collection.find_one({"user_id": user_id})

    if user_dict:
        return initialise_user_from_dict(user_dict)
    else:
        return None


def create_user(user_id: str, guild_id="", user_details={}) -> User:
    return initialise_user_from_dict(user_details)


def get_user_raw(user_id: str, guild_id: str) -> Optional[Dict]:
    collection = db.get_collection(str(guild_id))
    return collection.find_one({"user_id": user_id})


def initialise_user_from_dict(user_dict: dict) -> User:
    try:
        attempts_dicts: List[Dict] = user_dict["attempts"]
        attempts = []
        for attempt_dict in attempts_dicts:
            verification_code: str = attempt_dict["verification_code"]
            guild_id: str = attempt_dict["guild_id"]
            email: str = attempt_dict["email"]
            attempt_time: str = attempt_dict["attempt_time"]

            attempt: Attempt = Attempt(verification_code,
                                       guild_id,
                                       email=Email(email),
                                       attempt_time=attempt_time)

            attempts.append(attempt)

        return User(user_dict["user_id"],
                    user_dict["name"],
                    user_dict["discriminator"],
                    user_dict["status"],
                    attempts=attempts)
    except KeyError:
        logger.info("User has no current attempts")

    return User(user_dict["user_id"], user_dict["name"],
                user_dict["discriminator"], user_dict["status"])


def get_verified_attempt(user_id: str, guild_id: str,
                         verification_code: str) -> Optional[Attempt]:
    guild_collection = db.get_collection(str(guild_id))
    target = {
        "user_id": user_id,
        "attempts": {
            "$elemMatch": {
                "verification_code": verification_code
            }
        }
    }
    verified_user_dict = guild_collection.find_one(target)

    if verified_user_dict:
        attempts_dicts: List[Dict] = verified_user_dict["attempts"]

        attempts = []
        for attempt_dict in attempts_dicts:
            verification_code = attempt_dict["verification_code"]
            guild_id = attempt_dict["guild_id"]
            email_address: str = attempt_dict["email"]
            attempts.append(
                Attempt(verification_code, guild_id, Email(email_address)))

        for attempt in attempts:
            if attempt.verification_code == verification_code:
                return attempt

    return None


def get_verified_members(
        guild: Guild) -> Optional[List[Dict[str, Union[Member, str]]]]:
    guild_collection = db.get_collection(str(guild.id))
    existing_emails = guild_collection.find_one({"_id": "guild_emails"})
    if existing_emails:
        res = []
        for d in existing_emails["emails"]:
            user_id: str = d["user_id"]
            email: str = d["email"]
            member: Member = guild.get_member(int(user_id))
            res.append({"member": member, "email": email})

        return res
    else:
        return []


def add_verified_email(user_id: str, email: Email, guild_id: str) -> None:
    guild_collection = db.get_collection(str(guild_id))
    existing_emails = guild_collection.find_one({"_id": "guild_emails"})

    if existing_emails:
        existing_emails = existing_emails["emails"]
        existing_emails.append({"user_id": user_id, "email": email.address})
        guild_collection.replace_one({"_id": "guild_emails"}, {
            "_id": "guild_emails",
            "emails": existing_emails
        })
    else:
        guild_collection.insert_one({
            "_id":
            "guild_emails",
            "emails": [{
                "user_id": user_id,
                "email": email.address
            }]
        })


def email_exists_in_guild(email: Email, guild_id: str):
    guild_collection = db.get_collection(str(guild_id))
    match = guild_collection.find_one({
        "_id": "guild_emails",
        "emails": {
            "$elemMatch": {
                "email": email.address
            }
        }
    })

    if match:
        return True
    else:
        return False
