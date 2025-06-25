from typing import Any, Awaitable, Callable, Coroutine, TYPE_CHECKING, Protocol, TypeVar, Union, Tuple, Optional


T = TypeVar('T')

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    from .bot import Bot, AutoShardedBot
    from .context import Context
    # from .cog import Cog
    # from .errors import CommandError

    P = ParamSpec('P')
    MaybeAwaitableFunc = Callable[P, 'MaybeAwaitable[T]']
else:
    P = TypeVar('P')
    MaybeAwaitableFunc = Tuple[P, T]

_Bot = Union['Bot', 'AutoShardedBot']