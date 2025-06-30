from typing import (
    Union,
    Awaitable,
    Any,
    Optional,
    Callable,
)
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
    def __init__(self, *args, **kwargs):
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
    
class JSK(Group): # type: ignore
    async def callback(self):
        return "jsk"
    
JSK: Group = JSK()