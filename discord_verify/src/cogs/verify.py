from __future__ import annotations

from typing import Union, cast

import discord  # type: ignore
from discord import ChannelType, Game, Message, Status
from discord.ext import commands  # type: ignore

from ..logger import get_logger
from .datatypes.attempt import Attempt
from .datatypes.email_address import Email
from .datatypes.user import User
from .util import db, ses, util
from .util.config import CONFIG

logger = get_logger(__name__)


class Verify(commands.Cog):
    bot: commands.Bot
    """Functionality relating to verifying a user"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        # Private message
        if message.channel.type == ChannelType.private:
            logger.info(
                f"{message.author.name}#{message.author.discriminator}: {message.content}"
            )

            # Get the user from the db, if they haven't initiated the verification process yet,
            # user will be None
            user_id = str(message.author.id)
            user = db.get_user(user_id=user_id)

            # Do nothing if this user hasn't initiated the verification process
            if not user:
                return

            # If we are waiting for them to enter their email
            if user.status == "waiting":
                await self.handle_enter_email(message=message, user=user)
                return
            elif user.status == "has code":
                await self.handle_enter_verification_code(message=message,
                                                          user=user)
                return
        else:
            guild_id = str(message.guild.id)
            channel_id = str(message.channel.id)
            author_role_ids = [str(role.id) for role in message.author.roles]

            prefix = CONFIG["DEFAULT"]["command_prefix"]

            if all([
                    message.clean_content.lower().split() == [
                        prefix, 'verify'
                    ], channel_id == db.get_verify_channel(guild_id),
                    db.get_exec_role(guild_id) not in author_role_ids
            ]):
                await self.initiate_verification(message)
            elif channel_id == db.get_verify_channel(
                    guild_id) and db.get_exec_role(
                        guild_id) not in author_role_ids:
                await message.delete()

            if message.clean_content.lower().replace(
                    "\\", "") == f'{CONFIG["DEFAULT"]["command_prefix"]}banme':
                await self.ban_user(message)

        # await bot.process_commands(message)

    @commands.command(name="banme", hidden=True)
    async def ban_user(self, ctx):
        """
        Bans the invoking user
        """
        if ctx.channel.type == ChannelType.private:
            return

        member_role_names = [role.name for role in ctx.author.roles]
        # if "Executive" in member_role_names:
        #     await ctx.send("Why would you do that???")
        #     return

        major_role_names = [
            "Postgraduate / Researcher", "Alumni", "Cyber Security",
            "Data Science", "Games Design & Development",
            "Information Systems & Business Analysis", "Software Engineering",
            "Software Technology", "Web Design & Development", "Computing",
            "Other"
        ]
        major_roles = [
            role for role in ctx.author.roles if role.name in major_role_names
        ]

        if "Verified" not in member_role_names:
            applied_major_roles = [
                role for role in ctx.author.roles
                if role.name in major_role_names
            ]
            await ctx.author.remove_roles(*applied_major_roles)

        await ctx.message.add_reaction("✅")
        await ctx.send(
            f"Banned **{ctx.author.name}#{ctx.author.discriminator}**. Cya :slight_smile:"
        )
        await ctx.guild.ban(ctx.message.author,
                            reason="banme command",
                            delete_message_days=0)

    @commands.command(name="deleteme", hidden=True)
    @util.is_admin()
    async def delete_user(self, ctx):
        """
        Deletes user from DB for testing
        """
        if ctx.channel.type == ChannelType.private:
            return

        db.delete_user(user_id=str(ctx.author.id), guild_id=str(ctx.guild.id))

        await ctx.message.add_reaction("✅")

    @commands.command(name="verify")
    async def initiate_verification(self, ctx: Union[commands.Context,
                                                     Message]):
        """
        Begins the verification process
        """
        if isinstance(ctx, commands.Context):
            message: Message = cast(Message, ctx.message)
        else:
            message = cast(Message, ctx)

        if message.channel.type == ChannelType.private:
            return

        if str(message.channel.id) != db.get_verify_channel(
                str(message.guild.id)):
            return

        try:
            await message.delete()
        except discord.errors.Forbidden:
            logger.warning(f"Message deletion forbidden. {message}")

        # Fetch the user from the db. If the user doesn't exist in the db return None
        user_details = {
            "user_id": str(message.author.id),
            "name": str(message.author.name),
            "discriminator": str(message.author.discriminator),
            "status": "verifying"
        }
        user = db.get_user(user_id=str(message.author.id),
                           user_details=user_details,
                           guild_id=str(message.guild.id))
        if not user:
            user = db.create_user(user_id=str(message.author.id),
                                  user_details=user_details,
                                  guild_id=str(message.guild.id))

        if not user:
            logger.error(
                f"Failed to create user for {message.author.id} in guild: {message.guild.id}"
            )
            return

        # Check if the user already has the verified role in the given server
        already_verified = util.is_verified_in_guild(member=message.author,
                                                     guild=message.guild)
        if already_verified:
            dm_channel = await message.author.create_dm()
            await dm_channel.send("You are already verified!")
            logger.info("Replied: You are already verified!")

            return

        # Check if the user has already been sent a verification code.
        # Don't allow another code to be sent for this user for 24 hours.
        latest_attempt = user.get_latest_attempt()
        earliest_attempt = user.get_earliest_attempt()
        allowed_more_attempts = True
        if latest_attempt and earliest_attempt:
            allowed_more_attempts = await util.allowed_attempts(
                latest_attempt=latest_attempt,
                earliest_attempt=earliest_attempt,
                user=user,
                message=message)

            if not allowed_more_attempts:
                return

        # Waiting status: We are waiting for the user to send their email
        # in a private message
        user.status = "waiting"

        # Insert or update the user
        db.save_user(user=user, guild_id=str(message.guild.id))
        db.add_to_waiting(user=user, guild_id=str(message.guild.id))

        dm_channel = await message.author.create_dm()
        await dm_channel.send(
            "Please enter your student or staff email address.")
        logger.info(
            f"Replied to {message.author.name}#{message.author.discriminator}: Please enter your student or staff email address"
        )

    async def handle_enter_email(self, message, user):
        # Grab the email from the first argument
        try:
            user_input_email = message.clean_content.split()[0]
        except IndexError:
            logger.info("No email found. Likely empty message")
            await message.channel.send("Please send your email only.")
            logger.info("Replied: Please send your email only.")
            return

        # memez
        if user_input_email == "no":
            await message.channel.send("Don't be a smartass.")
            return

        # Perform verification
        try:
            email = Email(user_input_email)
        except Exception as e:
            logger.error(e)
            await message.channel.send(
                "Sorry, only students.mq.edu.au or mq.edu.au "
                "email addresses are allowed. You may not use your student ID "
                "email address.")
            logger.info(
                "Replied: Sorry, only students.mq.edu.au or mq.edu.au email "
                "addresses are allowed. You may not use your student ID email address."
            )
            return

        # Reject if someone else has already used this email to verify themselves in the server
        waiting_user = db.get_waiting_user_details(user_id=user.user_id)
        if waiting_user:
            try:
                guild_id = waiting_user["guild_id"]
            except KeyError:
                logger.error("Waiting user does not have a guild_id")
        else:
            logger.info("Waiting user does not exist")
            return

        if util.email_used_in_guild(email=email, guild_id=str(guild_id)):
            await message.channel.send(
                f"Please enter the verification code sent to {email.address}.")
            logger.info(
                f"Replied: Please enter the verification code sent to {email.address}."
            )
            return

        # Random 16 char hex string
        verification_code = util.generate_verification_code()

        # Create a new attempt for the server with the invocation
        attempt = Attempt(verification_code, guild_id, email=email)

        user.add_attempt(attempt)
        # user.attempt_count += 1

        # Try to send the verification code to the given email.
        # True if there was no error
        success = ses.send_email(verification_code=verification_code,
                                 email=email)

        # Report errors from Amazon SES sending email
        if not success:
            await message.channel.send("There was an error with the email "
                                       f"{email.address}. Please try again.")
            logger.info("Replied: There was an error with the email "
                        f"{email.address}. Please try again."
                        "")
            return

        # Update the users status
        user.status = "has code"
        # Update the user in the db
        db.save_user(user=user, guild_id=guild_id)

        await message.channel.send(
            f"Please enter the verification code sent to {email.address}.")
        logger.info(
            f"Replied: Please enter the verification code sent to {email.address}."
        )

    async def handle_enter_verification_code(self, message: Message, user):
        try:
            # Grab the verification code from the first argument
            verification_code = message.clean_content.split()[0]
        except IndexError:
            # If the message is empty (files/attachments but no text)
            logger.info("No verification code found. Likely empty message.")
            await message.channel.send(
                "Please send the verification code only.")
            logger.info("Replied: Please send the verification code only.")
            return

        # If there is an attempt associated with this user in the db that also has this verification
        # code, then the verification code is correct
        guild_id = user.get_latest_attempt().guild_id
        verified_attempt = db.get_verified_attempt(
            user_id=user.user_id,
            guild_id=guild_id,
            verification_code=verification_code)

        # SUCCESS
        if verified_attempt:
            try:
                message.guild
                await util.add_verified_role(self.bot.guilds, user.user_id,
                                             verified_attempt.guild_id)
            except discord.errors.Forbidden:
                await message.channel.send(
                    "I do not have the required permissions to modify your roles."
                )
                logger.info(
                    "Replied: I do not have the required permissions to modify your roles."
                )
                return
            except ValueError:
                await message.channel.send(
                    "This server does not have a verified role.")
                logger.info(
                    "Replied: This server does not have a verified role.")
                return

            await message.channel.send(
                "Verified!\nHead over to <#526261113814384640> "
                "to add a Major role and to access the rest of the server!")
            logger.info(
                "Verified!\nHead over to <#526261113814384640> to add a Major role and "
                "to access the rest of the server!")

            verified_attempt.status = "verified"
            # user.verify_attempt(verification_code=verification_code)
            user.status = "verified"
            db.add_verified_email(user_id=user.user_id,
                                  email=verified_attempt.email,
                                  guild_id=verified_attempt.guild_id)
        else:
            await message.channel.send(
                "Verification failed. Please wait and try again later.")
            logger.info(
                "Replied: Verification failed. Please wait and try again later."
            )
            user.status = "failed"
            # TODO 10 min delay

        db.save_user(user, guild_id=guild_id)
        db.remove_from_waiting(user_id=user.user_id)

    @commands.command(name="verifiedrole")
    @util.is_admin()
    async def set_verified_role(self, ctx):
        """
        Sets the role to give to verified members
        """

        # Return if in a DM
        if ctx.channel.type == ChannelType.private:
            return

        role = ctx.message.role_mentions[0]

        db.set_verified_role_id(ctx.guild.id, role.id)
        await ctx.channel.send(f"{role.mention} set as the verified role.")
        logger.info(f"{role.mention} set as the verified role.")

    @commands.command(name="verifychannel")
    @util.is_admin()
    async def set_verify_channel(self, ctx):
        """
        Sets the channel in which people will type !verify
        """
        try:
            channel = ctx.message.channel_mentions[0]
            success = db.set_verify_channel(str(ctx.guild.id), str(channel.id))
        except IndexError:
            await ctx.send("Verify channel not specified")

        if success:
            await ctx.send(f'Verify channel set to {channel.mention}')
        else:
            await ctx.send(
                f'unable to set verify channel. Have you already set one?')

    @commands.command(name="execrole")
    @util.is_admin()
    async def set_exec_role(self, ctx):
        """
        Sets the executive role
        """
        try:
            role = ctx.message.role_mentions[0]
            success = db.set_exec_role(str(ctx.guild.id), str(role.id))
        except IndexError:
            await ctx.send("Exec role not specified")

        if success:
            await ctx.send(f'Exec role set to {role.mention}')
        else:
            await ctx.send(
                f'Unable to set exec role. Have you already set one?')


def setup(bot):
    bot.add_cog(Verify(bot))
