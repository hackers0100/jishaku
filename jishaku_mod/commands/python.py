# -*- coding: utf-8 -*-

from .base import Command, JSK

import asyncio
import collections
import inspect
import io
import sys
import time
import typing

# import discord_mod

from jishaku_mod.codeblocks import Codeblock, codeblock_converter
from jishaku_mod.commands.context import Context
from jishaku_mod.exception_handling import ReplResponseReactor
from jishaku_mod.flags import Flags
from jishaku_mod.formatting import MultilineFormatter
from jishaku_mod.functools import AsyncSender
from jishaku_mod.math import format_bargraph, format_stddev
# from jishaku_mod_.paginators import PaginatorInterface, WrappedPaginator, use_file_check
from jishaku_mod.repl import (
    AsyncCodeExecutor,
    Scope,
    all_inspections,
    create_tree,
    disassemble,
    get_adaptive_spans,
    get_var_dict_from_ctx
)

try:
    import line_profiler  # type: ignore
except ImportError:
    line_profiler = None


class PythonFeature(Command):
    """
    Feature containing the Python-related commands
    """

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        self._scope = Scope()
        self.retain = Flags.RETAIN
        self.last_result: typing.Any = None
        super().__init__(*args, **kwargs)

    @property
    def scope(self):
        """
        Gets a scope for use in REPL.

        If retention is on, this is the internal stored scope,
        otherwise it is always a new Scope.
        """

        if self.retain:
            return self._scope
        return Scope()

    @JSK.command(name="retain")
    async def jsk_retain(self, ctx: Context, *, toggle: bool = None):  # type: ignore
        """
        Turn variable retention for REPL on or off.

        Provide no argument for current status.
        """

        if toggle is None:
            if self.retain:
                return await ctx.send("Variable retention is set to ON.")

            return await ctx.send("Variable retention is set to OFF.")

        if toggle:
            if self.retain:
                return await ctx.send("Variable retention is already set to ON.")

            self.retain = True
            self._scope = Scope()
            return await ctx.send("Variable retention is ON. Future REPL sessions will retain their scope.")

        if not self.retain:
            return await ctx.send("Variable retention is already set to OFF.")

        self.retain = False
        return await ctx.send("Variable retention is OFF. Future REPL sessions will dispose their scope when done.")

    async def jsk_python_result_handling(self, ctx: Context, result: typing.Any):
        """
        Determines what is done with a result when it comes out of jsk py.
        This allows you to override how this is done without having to rewrite the command itself.
        What you return is what gets stored in the temporary _ variable.
        """
        if not isinstance(result, str):
            # repr all non-strings
            result = repr(result)


        if result.strip() == '':
            result = "\u200b"

        # if self.bot.http.token:
        #     result = result.replace(self.bot.http.token, "[token omitted]")

        return await ctx.send(
            result,
        )

    def jsk_python_get_convertables(self, ctx: Context) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, str]]:
        """
        Gets the arg dict and convertables for this scope.

        The arg dict contains the 'locals' to be propagated into the REPL scope.
        The convertables are string->string conversions to be attempted if the code fails to parse.
        """

        arg_dict = get_var_dict_from_ctx(ctx, Flags.SCOPE_PREFIX)
        arg_dict["_"] = self.last_result
        convertables: typing.Dict[str, str] = {}

        return arg_dict, convertables

    @JSK.command(name="py", aliases=["python"])
    async def jsk_python(self, ctx: Context, *, argument: str):  # type: ignore
        """
        Direct evaluation of Python code.
        """

        argument: Codeblock = codeblock_converter(argument)

        arg_dict, convertables = self.jsk_python_get_convertables(ctx)
        scope = self.scope

        try:
            async with ReplResponseReactor(ctx.message):
                with JSK.submit(ctx):
                    executor = AsyncCodeExecutor(argument.content, scope, arg_dict=arg_dict, convertables=convertables)
                    async for send, result in AsyncSender(executor):  # type: ignore
                        send: typing.Callable[..., None]
                        result: typing.Any

                        if result is None:
                            continue

                        self.last_result = result

                        send(await self.jsk_python_result_handling(ctx, result))

        finally:
            scope.clear_intersection(arg_dict)

    @JSK.command(name="py_inspect", aliases=["pyi", "python_inspect", "pythoninspect"])
    async def jsk_python_inspect(self, ctx: Context, *, argument: str):  # type: ignore
        """
        Evaluation of Python code with inspect information.
        """

        argument: Codeblock = codeblock_converter(argument)

        arg_dict, convertables = self.jsk_python_get_convertables(ctx)
        scope = self.scope

        try:
            async with ReplResponseReactor(ctx.message):
                with JSK.submit(ctx):
                    executor = AsyncCodeExecutor(argument.content, scope, arg_dict=arg_dict, convertables=convertables)
                    async for send, result in AsyncSender(executor):  # type: ignore
                        send: typing.Callable[..., None]
                        result: typing.Any

                        self.last_result = result

                        header = repr(result).replace("``", "`\u200b`")

                        # if self.bot.http.token:
                            # header = header.replace(self.bot.http.token, "[token omitted]")

                        if len(header) > 485:
                            header = header[0:482] + "..."

                        lines = [f"=== {header} ===", ""]

                        for name, res in all_inspections(result):
                            lines.append(f"{name:16.16} :: {res}")

                        docstring = (inspect.getdoc(result) or '').strip()

                        if docstring:
                            lines.append(f"\n=== Help ===\n\n{docstring}")

                        text = "\n".join(lines)

                        # if use_file_check(ctx, len(text)):  # File "full content" preview limit
                            # send(await ctx.send(file=discord_mod.File(
                                # filename="inspection.prolog",
                                # fp=io.BytesIO(text.encode('utf-8'))
                            # )))
                        # else:
                        # paginator = WrappedPaginator(prefix="```prolog", max_size=1980)

                        # paginator.add_line(text)

                        # interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
                        # send(await interface.send_to(ctx))
                        await ctx.send("```prolog\n"+text+'\n```')
        finally:
            scope.clear_intersection(arg_dict)

    if line_profiler is not None:
        @JSK.command(name="timeit")
        async def jsk_timeit(self, ctx: Context, *, argument: str):  # type: ignore
            """
            Times and produces a relative timing report for a block of code.
            """

            argument: Codeblock = codeblock_converter(argument)

            arg_dict, convertables = self.jsk_python_get_convertables(ctx)
            scope = self.scope

            try:
                async with ReplResponseReactor(ctx.message):
                    with JSK.submit(ctx):
                        executor = AsyncCodeExecutor(
                            argument.content, scope,
                            arg_dict=arg_dict,
                            convertables=convertables,
                            auto_return=False
                        )

                        overall_start = time.perf_counter()
                        count: int = 0
                        timings: typing.List[float] = []
                        ioless_timings: typing.List[float] = []
                        line_timings: typing.Dict[int, typing.List[float]] = collections.defaultdict(list)

                        while count < 10_000 and (time.perf_counter() - overall_start) < 30.0:
                            profile = line_profiler.LineProfiler()  # type: ignore
                            profile.add_function(executor.function)  # type: ignore

                            profile.enable()  # type: ignore
                            try:
                                start = time.perf_counter()
                                async for send, result in AsyncSender(executor):  # type: ignore
                                    send: typing.Callable[..., None]
                                    result: typing.Any

                                    if result is None:
                                        continue

                                    self.last_result = result

                                    send(await self.jsk_python_result_handling(ctx, result))
                                    # Reduces likelihood of hardblocking
                                    await asyncio.sleep(0.001)

                                end = time.perf_counter()
                            finally:
                                profile.disable()  # type: ignore

                            # Reduces likelihood of hardblocking
                            await asyncio.sleep(0.001)

                            count += 1
                            timings.append(end - start)

                            ioless_time: float = 0

                            for function in profile.code_map.values():  # type: ignore
                                for timing in function.values():  # type: ignore
                                    line_timings[timing['lineno']].append(timing['total_time'] * profile.timer_unit)  # type: ignore
                                    ioless_time += timing['total_time'] * profile.timer_unit  # type: ignore

                            ioless_timings.append(ioless_time)

                        execution_time = format_stddev(timings)
                        active_time = format_stddev(ioless_timings)

                        max_line_time = max(max(timing) for timing in line_timings.values())

                        linecache = executor.create_linecache()
                        lines: typing.List[str] = []

                        for lineno in sorted(line_timings.keys()):
                            timing = line_timings[lineno]
                            max_time = max(timing)
                            percentage = max_time / max_line_time
                            blocks = format_bargraph(percentage, 5)

                            line = f"{format_stddev(timing)} {blocks} {linecache[lineno - 1] if lineno <= len(linecache) else ''}"
                            color = '\u001b[31m' if percentage > 6 / 8 else '\u001b[33m' if percentage > 3 / 8 else '\u001b[32m'

                            lines.append('\u001b[0m' + color + line if Flags.use_ansi(ctx) else line)

                        await ctx.send(
                            content="\n".join([
                                f"Executed {count} times",
                                f"Actual execution time: {execution_time}",
                                f"Active (non-waiting) time: {active_time}",
                                "**Delay will be added by async setup, use only for relative measurements**",
                            ]),
                            # file=discord_mod.File(
                            #     filename="lines.ansi",
                            #     fp=io.BytesIO(''.join(lines).encode('utf-8'))
                            # )
                        )

            finally:
                scope.clear_intersection(arg_dict)

    @JSK.command(name="dis", aliases=["disassemble"])
    async def jsk_disassemble(self, ctx: Context, *, argument: str):  # type: ignore
        """
        Disassemble Python code into bytecode.
        """

        argument: Codeblock = codeblock_converter(argument)

        arg_dict = get_var_dict_from_ctx(ctx, Flags.SCOPE_PREFIX)

        async with ReplResponseReactor(ctx.message):
            text = "\n".join(disassemble(argument.content, arg_dict=arg_dict))

            # if use_file_check(ctx, len(text)):  # File "full content" preview limit
            #     await ctx.send(file=discord_mod.File(
            #         filename="dis.py",
            #         fp=io.BytesIO(text.encode('utf-8'))
            #     ))
            # else:
            #     paginator = WrappedPaginator(prefix='```py', max_size=1980)

            #     paginator.add_line(text)

            #     interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
            #     await interface.send_to(ctx)
            await ctx.send(f"```py\n{text}\n```")

    @JSK.command(name="ast")
    async def jsk_ast(self, ctx: Context, *, argument: str):  # type: ignore
        """
        Disassemble Python code into AST.
        """

        argument: Codeblock = codeblock_converter(argument)

        async with ReplResponseReactor(ctx.message):
            text = create_tree(argument.content, use_ansi=Flags.use_ansi(ctx))

            # await ctx.send(file=discord_mod.File(
            #     filename="ast.ansi",
            #     fp=io.BytesIO(text.encode('utf-8'))
            # ))
            # TODO: File support

    if sys.version_info >= (3, 11):
        @JSK.command(name="specialist")
        async def jsk_specialist(self, ctx: Context, *, argument: str):  # type: ignore
            """
            Direct evaluation of Python code.
            """

            argument: Codeblock = codeblock_converter(argument)

            arg_dict, convertables = self.jsk_python_get_convertables(ctx)
            scope = self.scope

            try:
                async with ReplResponseReactor(ctx.message):
                    with JSK.submit(ctx):
                        executor = AsyncCodeExecutor(argument.content, scope, arg_dict=arg_dict, convertables=convertables)
                        async for send, result in AsyncSender(executor):  # type: ignore
                            send: typing.Callable[..., None]
                            result: typing.Any

                            if result is None:
                                continue

                            self.last_result = result

                            send(await self.jsk_python_result_handling(ctx, result))

                        formatter = MultilineFormatter(argument.content)

                        for (
                            index,
                            (instruction, line, span, specialized, adaptive)
                        ) in enumerate(get_adaptive_spans(executor.function.__code__)):  # pylint: disable=protected-access
                            if line - 1 < len(formatter.lines):
                                formatter.add_annotation(
                                    line - 1,
                                    instruction.opname,
                                    span,
                                    (index % 6) + 31,
                                    None,
                                    45 if specialized else 46 if adaptive else None
                                )

                        text = formatter.output(True, Flags.use_ansi(ctx))

                        # await ctx.send(file=discord_mod.File(
                        #     filename="specialist.ansi",
                        #     fp=io.BytesIO(text.encode('utf-8'))
                        # ))
                        # TODO

            finally:
                scope.clear_intersection(arg_dict)
