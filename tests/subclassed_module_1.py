# -*- coding: utf-8 -*-

"""
jishaku subclassing test 1
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a valid extension file for discord.py intended to
discover weird behaviors related to subclassing.

This variant overrides behavior using a Feature.

:copyright: (c) 2021 Devon (scarletcafe) R
:license: MIT, see LICENSE for more details.

"""

from discord_mod.ext import commands

import jishaku_mod_
from jishaku_mod_.types import ContextT


class ThirdPartyFeature(jishaku_mod_.Feature):
    """
    overriding feature for test
    """

    @jishaku_mod_.Feature.Command(name="jishaku", aliases=["jsk"], invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx: ContextT):
        """
        override test
        """
        return await ctx.send("The behavior of this command has been overridden with a third party feature.")


class Magnet1(ThirdPartyFeature, *jishaku_mod_.OPTIONAL_FEATURES, *jishaku_mod_.STANDARD_FEATURES):  # pylint: disable=too-few-public-methods
    """
    The extended Jishaku cog
    """


async def setup(bot: commands.Bot):
    """
    The setup function for the extended cog
    """

    await bot.add_cog(Magnet1(bot=bot))
