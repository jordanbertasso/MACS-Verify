from __future__ import annotations

from discord import ChannelType, Game, Status  # type: ignore
from discord.ext import commands  # type: ignore
from discord.flags import Intents  # type: ignore

from .cogs import admin, error_handler, verify
from .cogs.util.config import CONFIG
from .logger import get_logger

logger = get_logger(__name__)

bot = commands.Bot(CONFIG["DEFAULT"]["command_prefix"], intents=Intents.all())


@bot.event
async def on_ready():
    logger.info(f"We have logged in as {bot.user}")
    game = Game("SMTP")
    await bot.change_presence(status=Status.online, activity=game)


bot.add_cog(admin.Admin())
bot.add_cog(verify.Verify(bot))
bot.add_cog(error_handler.CommandErrorHandler())
bot.run(CONFIG["DEFAULT"]["discord_token"])
