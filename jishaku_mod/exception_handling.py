# -*- coding: utf-8 -*-

import asyncio
import subprocess
import traceback
import typing
from types import TracebackType

from typing_extensions import ParamSpec

from jishaku_mod_.flags import Flags


async def send_traceback(
    destination: typing.Any,
    verbosity: int,
    etype: typing.Type[BaseException],
    value: BaseException,
    trace: TracebackType
):
    """
    Sends a traceback of an exception to a destination.
    Used when REPL fails for any reason.

    :param destination: Where to send this information to
    :param verbosity: How far back this traceback should go. 0 shows just the last stack.
    :param exc_info: Information about this exception, from sys.exc_info or similar.
    :return: The last message sent
    """

    traceback_content = "".join(traceback.format_exception(etype, value, trace, verbosity)).replace("``", "`\u200b`")



    message = None

    message = await destination.send("```py\n"+traceback_content+"\n```")

    return message


T = typing.TypeVar('T')
P = ParamSpec('P')


async def do_after_sleep(delay: float, coro: typing.Callable[P, typing.Awaitable[T]], *args: P.args, **kwargs: P.kwargs) -> T:
    """
    Performs an action after a set amount of time.

    This function only calls the coroutine after the delay,
    preventing asyncio complaints about destroyed coros.

    :param delay: Time in seconds
    :param coro: Coroutine to run
    :param args: Arguments to pass to coroutine
    :param kwargs: Keyword arguments to pass to coroutine
    :return: Whatever the coroutine returned.
    """
    await asyncio.sleep(delay)
    return await coro(*args, **kwargs)




class ReplResponseReactor:  # pylint: disable=too-few-public-methods
    """
    Extension of the ReactionProcedureTimer that absorbs errors, sending tracebacks.
    """

    __slots__ = ('message', 'loop', 'handle', 'raised')

    def __init__(self, message, loop: typing.Optional[asyncio.BaseEventLoop] = None):
        self.message = message
        self.loop = loop or asyncio.get_event_loop()
        self.handle = None
        self.raised = False

    async def __aenter__(self):
        # self.handle = self.loop.create_task(do_after_sleep(2, attempt_add_reaction, self.message,
        #                                                    "\N{BLACK RIGHT-POINTING TRIANGLE}"))
        return self

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType
    ) -> bool:
        if self.handle:
            self.handle.cancel()

        # no exception, check mark
        if not exc_val:
            await attempt_add_reaction(self.message, "\N{WHITE HEAVY CHECK MARK}")
            return False

        self.raised = True

        if isinstance(exc_val, (SyntaxError, asyncio.TimeoutError, subprocess.TimeoutExpired)):
            # short traceback, send to channel
            destination = Flags.traceback_destination(self.message) or self.message.channel

            if destination != self.message.channel:
                # await attempt_add_reaction(
                #     self.message,
                #     # timed out is alarm clock
                #     # syntax error is single exclamation mark
                #     "\N{HEAVY EXCLAMATION MARK SYMBOL}" if isinstance(exc_val, SyntaxError) else "\N{ALARM CLOCK}"
                # )
                ...

            await send_traceback(
                self.message if destination == self.message.channel else destination,
                0, exc_type, exc_val, exc_tb
            )
        else:
            destination = Flags.traceback_destination(self.message) or self.message.author

            if destination != self.message.channel:
                # other error, double exclamation mark
                # await attempt_add_reaction(self.message, "\N{DOUBLE EXCLAMATION MARK}")
                ...

            # this traceback likely needs more info, so increase verbosity, and DM it instead.
            await send_traceback(
                self.message if destination == self.message.channel else destination,
                8, exc_type, exc_val, exc_tb
            )

        return True  # the exception has been handled
