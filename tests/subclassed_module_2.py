# -*- coding: utf-8 -*-

"""
jishaku subclassing test 2
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a valid extension file for discord.py intended to
discover weird behaviors related to subclassing.

This variant overrides behavior directly.

:copyright: (c) 2021 Devon (scarletcafe) R
:license: MIT, see LICENSE for more details.

"""

from discord_mod.ext import commands

import jishaku_mod_
from jishaku_mod_.types import ContextT


class Magnet2(*jishaku_mod_.OPTIONAL_FEATURES, *jishaku_mod_.STANDARD_FEATURES):  # pylint: disable=too-few-public-methods
    """
    The extended Jishaku cog
    """

    @jishaku_mod_.Feature.Command(name="jishaku", aliases=["jsk"], invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx: ContextT):
        """
        override test
        """
        return await ctx.send("The behavior of this command has been overridden directly.")


async def setup(bot: commands.Bot):
    """
    The setup function for the extended cog
    """

    await bot.add_cog(Magnet2(bot=bot))  # type: ignore[reportGeneralTypeIssues]
