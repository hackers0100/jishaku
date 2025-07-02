import asyncio
import contextlib
import collections
import typing

from .context import Context
from typing import (
    Union,
    Awaitable,
    Any,
    Optional,
    Callable,
)
from datetime import datetime, timezone



class CommandTask(typing.NamedTuple):
    """
    A running Jishaku task, wrapping asyncio.Task
    """

    index: int  # type: ignore
    ctx: Context
    task: Optional['asyncio.Task[Any]']

class Command:
    name: str
    aliases: Optional[list[str]]
    def __init__(self, name: Optional[str] = None, aliases: Optional[list[str]] = None):
        self.help: str = self.__doc__ or ''
        if name is not None:
            self.name = name
        self.aliases = aliases or []

    def callback(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    def invoke(self, *args: Any, **kwargs: Any) -> Union[Awaitable[Any], Any]:
        return self.callback(*args, **kwargs)
    

class Group(Command):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.commands: list[Command] = []
        super().__init__(*args, **kwargs)

    def command(self, name: Optional[str] = None, aliases: Optional[list[str]] = None) -> Callable[[Callable[..., Any]], Command]:
        def decor(func: Callable[..., Any]) -> Command:
            cmd = Command(aliases=aliases)
            cmd.name = name or func.__name__
            cmd.callback = func
            return cmd

        return decor

    def group(self, name: Optional[str] = None, aliases: Optional[list[str]] = None) -> Callable[[Callable[..., Any]], "Group"]:
        def decor(func: Callable[..., Any]) -> "Group":
            cmd = Group(aliases=aliases)
            cmd.name = name or func.__name__
            cmd.callback = func
            return cmd

        return decor

class FeatureMixin:...
class Feature(Command, FeatureMixin):...
class GrpFeature(Group, FeatureMixin):...

class JishakuFeature(GrpFeature):
    def __init__(self, *a: Any, **k: Any):
        self.features: list[Union[Command, Group]] = []
        self.task_count: int = 0
        self.start_time: datetime = datetime.now(timezone.utc)
        self.tasks: typing.Deque[CommandTask] = collections.deque()
        super().__init__(*a, **k)

    async def callback(self):
        return "jsk"

    def load_feature(self, feature: Union[Command, Group]):
        if feature in self.features:
            self.remove_feature(feature)

        self.features.append(feature)

    def remove_feature(self, feature: Union[Command, Group]):
        if feature in self.features:
            self.features.remove(feature)

    @contextlib.contextmanager
    def submit(self, ctx: Context):
        """
        A context-manager that submits the current task to jishaku's task list
        and removes it afterwards.

        Parameters
        -----------
        ctx: commands.Context
            A Context object used to derive information about this command task.
        """

        self.task_count += 1

        try:
            current_task = asyncio.current_task()  # pylint: disable=no-member
        except RuntimeError:
            # asyncio.current_task doesn't document that it can raise RuntimeError, but it does.
            # It propagates from asyncio.get_running_loop(), so it happens when there is no loop running.
            # It's unclear if this is a regression or an intentional change, since in 3.6,
            #  asyncio.Task.current_task() would have just returned None in this case.
            current_task = None

        cmdtask = CommandTask(self.task_count, ctx, current_task)

        self.tasks.append(cmdtask)

        try:
            yield cmdtask
        finally:
            if cmdtask in self.tasks:
                self.tasks.remove(cmdtask)

JSK = JishakuFeature()