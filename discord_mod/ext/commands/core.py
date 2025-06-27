# from typing import Generic, ParamSpec, TYPE_CHECKING, TypeVar
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    # Generator,
    Generic,
    List,
    # Literal,
    Optional,
    # Set,
    Tuple,
    # Type,
    TypeVar,
    Union,
    # overload,
)
import asyncio
import inspect
from .context import Context

from .parameters import Parameter #, Signature

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec # Self

    from ._types import (
        # BotT,
        # Check,
        # ContextT,
        Coro,
        # CoroFunc,
        # Error,
        # Hook,
        # UserCheck
    )

from ._types import _BaseCommand, CogT #type: ignore

T = TypeVar('T')

def extract_descriptions_from_docstring(function: Callable[..., Any], params: Dict[str, Parameter], /) -> Optional[str]:
    docstring = inspect.getdoc(function)

    if docstring is None:
        return None

    divide = PARAMETER_HEADING_REGEX.split(docstring, 1)
    if len(divide) == 1:
        return docstring

    description, param_docstring = divide
    for match in NUMPY_DOCSTRING_ARG_REGEX.finditer(param_docstring):
        name = match.group('name')

        if name not in params:
            is_display_name = discord_mod.utils.get(params.values(), displayed_name=name)
            if is_display_name:
                name = is_display_name.name
            else:
                continue

        param = params[name]
        if param.description is None:
            param._description = _fold_text(match.group('description'))

    return _fold_text(description.strip())


if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')

class Command(_BaseCommand, Generic[CogT, P, T]):
    def __init__(
        self,
        func: Union[
            Callable[Concatenate[CogT, Context[Any], P], Coro[T]],
            Callable[Concatenate[Context[Any], P], Coro[T]],
        ],
        /,
        **kwargs: Any,
    ) -> None:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        name = kwargs.get('name') or func.__name__
        if not isinstance(name, str):
            raise TypeError('Name of a command must be a string.')
        self.name: str = name

        self.callback = func
        self.enabled: bool = kwargs.get('enabled', True)

        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = extract_descriptions_from_docstring(func, self.params)

        self.help: Optional[str] = help_doc

        self.brief: Optional[str] = kwargs.get('brief')
        self.usage: Optional[str] = kwargs.get('usage')
        self.rest_is_raw: bool = kwargs.get('rest_is_raw', False)
        self.aliases: Union[List[str], Tuple[str]] = kwargs.get('aliases', [])
        self.extras: Dict[Any, Any] = kwargs.get('extras', {})

        if not isinstance(self.aliases, (list, tuple)):
            raise TypeError("Aliases of a command must be a list or a tuple of strings.")

        self.description: str = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden: bool = kwargs.get('hidden', False)

        self._cog = None


    @property
    def cog(self) -> CogT:
        return self._cog

    @cog.setter
    def cog(self, value: CogT) -> None:
        self._cog = value

class GroupMixin(Generic[CogT]):
    pass

class Group(GroupMixin[CogT], Command[CogT, P, T]):
    pass