from __future__ import annotations

import datetime
import uuid
from typing import List

from discord import Guild, Member, Message  # type: ignore
from discord.ext import commands  # type: ignore
from discord.ext.commands import Context  # type: ignore

from ...logger import get_logger
from ..datatypes.attempt import Attempt
from ..datatypes.email_address import Email
from ..datatypes.user import User
from . import db

logger = get_logger(__name__)


async def add_verified_role(guilds: List[Guild], user_id: str,
                            guild_id: str) -> None:
    # DEBUG
    # return

    guild = get_guild_from_id(guilds, guild_id)
    member = await get_member_from_user_id(user_id=user_id, guild=guild)
    verified = is_verified_in_guild(member=member, guild=guild)
    if verified:
        return

    verified_role_id = db.get_verified_role_id(guild_id)
    if not verified_role_id:
        raise ValueError
        return

    verified_role = guild.get_role(int(verified_role_id))

    await member.add_roles(verified_role, reason="MACS Verify")

    logger.info(f"Added verified role to {member.id} in guild: {guild.id}")


def get_guild_from_id(guilds: List[Guild], guild_id: str):
    for guild in guilds:
        if str(guild.id) == guild_id:
            return guild


async def get_member_from_user_id(user_id: str, guild: Guild) -> Member:
    # for member in guild.fetch_members(limit=None):
    #     if str(member.id) == user_id:
    #         return member

    member = await guild.fetch_member(int(user_id))
    return member


def is_verified_in_guild(member: Member, guild: Guild) -> bool:
    current_role_ids = [str(role.id) for role in member.roles]
    verified_role_id = db.get_verified_role_id(str(guild.id))
    if verified_role_id in current_role_ids:
        return True
    else:
        return False


def generate_verification_code() -> str:
    """
    Generate a random 16 character hex string
    """
    return uuid.uuid4().hex[:16]


def email_used_in_guild(email: Email, guild_id: str) -> bool:
    return db.email_exists_in_guild(email=email, guild_id=guild_id)


def time_has_passed(hours: int, datetime_string: str) -> bool:
    if not datetime_string:
        return True

    start = datetime.datetime.fromisoformat(datetime_string)
    now = datetime.datetime.now()

    if now - start > datetime.timedelta(hours=hours):
        return True
    else:
        return False


async def send_email_debug(verification_code="", email=""):
    logger.info(f"""
    To: {email}

    {verification_code}
    """)


async def allowed_attempts(latest_attempt: Attempt, earliest_attempt: Attempt,
                           user: User, message: Message) -> bool:

    # If the current verify guild is different to the previous one
    if latest_attempt.guild_id != str(message.guild.id):
        return True

    # If a verification code has been sent to the user, because they have an email associated with
    # their latest attempt
    try:
        email = latest_attempt.email
    except AttributeError:
        logger.info(
            "Lastest attempt does not have an email. User may have used !verify multiple times."
        )
        return True

    if email and not time_has_passed(
            hours=24, datetime_string=earliest_attempt.attempt_time):

        attempts_within_day = len(user.attempts)

        dm_channel = await message.author.create_dm()
        if attempts_within_day >= 3:

            await dm_channel.send(
                "You have attempted 3 verifications for this server within "
                "24 hours. Please try again in 24 hours.")
            logger.info(
                "You have attempted 3 verifications for this server within "
                "24 hours. Please try again in 24 hours.")

            return False
        else:
            await dm_channel.send(
                f"You have attempted {attempts_within_day} verification(s) for "
                "this server within 24 hours. "
                f"You have {3 - attempts_within_day} attempts remaining")
            logger.info(
                f"Replied: You have attempted {attempts_within_day} verification(s) for "
                "this server within 24 hours. "
                f"You have {3 - attempts_within_day} attempts remaining")
            return True

        # await dm_channel.send("A verification code has already been sent to your email.
        # \n\nPlease enter that code or wait 24 hours to use !verify for this server again.")
        # logging.info("Replied: A verification code has already been sent to your email.\n\nPlease
        # enter that code or wait 24 hours to use !verify for this server again.")
        # return
    else:
        user.attempts = []
        db.save_user(user, str(message.guild.id))
        return True

    return False


def is_admin():
    def predicate(ctx):
        return ctx.message.author.guild_permissions.administrator

    return commands.check(predicate)
