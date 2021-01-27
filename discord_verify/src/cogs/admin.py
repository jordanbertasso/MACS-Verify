from __future__ import annotations
from cogs.util import db
from discord import Embed
from discord.ext import commands, menus
from logger import get_logger
import pprint

logger = get_logger(__name__)

class Admin(commands.Cog):
    """Admin only commands"""
    def __init__(self, bot):
        self.bot = bot


class MembersSource(menus.ListPageSource):
    def __init__(self, entries:  [{"member": discord.Member, "email": str}], guild: discord.Guild):
        super().__init__(entries, per_page=10)
        self._guild = guild

    async def format_page(self, menu, entries: [{"member": discord.Member, "email": str}]):
        offset = menu.current_page * self.per_page

        fields = []
        for i, d in enumerate(entries, start=offset):
            m = d["member"]
            e = d["email"]
            fields.append({
                'name': f'{i+1}. {m.name}#{m.discriminator}',
                'value': e
            })

        embed = Embed.from_dict({
            'title': f'Verified Members for {self._guild.name}',
            'type': 'rich',
            'fields': fields,
            'color': 0x89c6f6
        })

        return embed

        # return '\n'.join(f'{i}. {v.name}#{v.discriminator}' for i, v in
        #                  enumerate(entries, start=offset))


def setup(bot):
    bot.add_cog(Admin(bot))
