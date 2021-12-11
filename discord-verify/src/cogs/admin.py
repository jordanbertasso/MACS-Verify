from __future__ import annotations

import pprint
from typing import Dict, List, NamedTuple, Union

from discord import Embed, Guild, Member  # type: ignore
from discord.ext import commands, menus  # type: ignore

from ..logger import get_logger
from .util import db

logger = get_logger(__name__)


class Admin(commands.Cog):
    """Admin only commands"""


class MembersSource(menus.ListPageSource):
    def __init__(self, entries: List[Dict[str, Union[Member, str]]],
                 guild: Guild):
        """MembersSource

        Args:
            entries (List[Dict[str, Union[Member, str]]]): {"member": Member, "email": str}
            guild (Guild): Discord Guild
        """
        super().__init__(entries, per_page=10)
        self._guild = guild

    async def format_page(
            self, menu, entries: List[Dict[str, Union[Member, str]]]) -> Embed:
        """Format page for the embed

        Args:
            menu ([type]): [description]
            entries (List[Dict[str, Union[Member, str]]]): {"member": Member, "email": str}

        Returns:
            Embed: The formatted embed
        """
        offset = menu.current_page * self.per_page

        fields = []
        for i, d in enumerate(entries, start=offset):
            m: Member = d["member"]
            e: str = d["email"]
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


def setup(bot):
    bot.add_cog(Admin(bot))
