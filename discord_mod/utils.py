from typing import (
    Any,
    AsyncIterable,
    # AsyncIterator,
    Awaitable,
    Callable,
    # Collection,
    Coroutine,
    # Dict,
    # ForwardRef,
    # Generic,
    Iterable,
    # Iterator,
    # List,
    # Literal,
    # NamedTuple,
    # Optional,
    # Protocol,
    # Set,
    # Sequence,
    # SupportsIndex,
    # Tuple,
    # Type,
    TypeVar,
    Union,
    # overload,
    TYPE_CHECKING,
)

from inspect import isawaitable as _isawaitable #, signature as _signature
class _cached_property:
    def __init__(self, function) -> None: # type: ignore
        self.function = function
        self.__doc__ = getattr(function, '__doc__') # type: ignore

    def __get__(self, instance, owner): # type: ignore
        if instance is None:
            return self

        value = self.function(instance) # type: ignore
        setattr(instance, self.function.__name__, value) # type: ignore

        return value # type: ignore


if TYPE_CHECKING:
    from functools import cached_property as cached_property

    from typing_extensions import ParamSpec, TypeGuard # , Self

    # from .permissions import Permissions
    # from .abc import Snowflake
    # from .invite import Invite
    # from .template import Template

    # class _DecompressionContext(Protocol):
    #     COMPRESSION_TYPE: str

    #     def decompress(self, data: bytes, /) -> str | None:
    #         ...

    P = ParamSpec('P')

    MaybeAwaitableFunc = Callable[P, 'MaybeAwaitable[T]']


else:
    cached_property = _cached_property


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
_Iter = Union[Iterable[T], AsyncIterable[T]]
Coro = Coroutine[Any, Any, T]
MaybeAwaitable = Union[T, Awaitable[T]]

class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, _) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return '...'


MISSING: Any = _MissingSentinel()


async def maybe_coroutine(f: MaybeAwaitableFunc[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    value = f(*args, **kwargs)
    if _isawaitable(value):
        return await value
    else:
        return value


async def async_all(
    gen: Iterable[Union[T, Awaitable[T]]],
    *,
    check: Callable[[Union[T, Awaitable[T]]], TypeGuard[Awaitable[T]]] = _isawaitable,  # type: ignore
) -> bool:
    for elem in gen:
        if check(elem):
            elem = await elem
        if not elem:
            return False
    return True


# async def sane_wait_for(futures: Iterable[Awaitable[T]], *, timeout: Optional[float]) -> Set[asyncio.Task[T]]:
#     ensured = [asyncio.ensure_future(fut) for fut in futures]
#     done, pending = await asyncio.wait(ensured, timeout=timeout, return_when=asyncio.ALL_COMPLETED)

#     if len(pending) != 0:
#         raise asyncio.TimeoutError()

#     return done