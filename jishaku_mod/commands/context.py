from typing import Any

class Context:
    def __init__(self, author, message, bot):
        self.author = author
        self.message = message
        self.bot = bot

    async def send(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError