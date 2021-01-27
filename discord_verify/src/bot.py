from __future__ import annotations
from discord.ext import commands
from discord import Game, Status, ChannelType
from cogs.util.config import CONFIG
from logger import get_logger
import discord


logger = get_logger(__name__)

bot = commands.Bot(CONFIG["DEFAULT"]["command_prefix"])


@bot.event
async def on_ready():
    logger.info(f"We have logged in as {bot.user}")
    game = Game("SMTP")
    await bot.change_presence(status=Status.online, activity=game)


bot.load_extension("cogs.admin")
bot.load_extension("cogs.verify")
bot.load_extension("cogs.error_handler")
bot.run(CONFIG["DEFAULT"]["discord_token"])
