from __future__ import annotations

import contextlib
import shlex
from typing import (
    Callable,
    Generator,
    List,
)

from attr import Factory, define
from loguru import logger as log
from typer import Typer

import Broken
from Broken import flatten
from Broken.Core.BrokenUtils import Ignore


@define
class BrokenTyper:
    """
    A wrap around Typer with goodies

    • Why? Automation.
    • Stupid? Absolutely.
    • Useful? Maybe.
    • Fun? Yes.
    • Worth it? Probably not.
    • Will I use it? Yes.
    """
    description: str       = ""
    app:         Typer     = None
    chain:       bool      = False
    commands:    List[str] = Factory(list)
    default:     str       = None
    help_option: bool      = False
    exit_hook:   Callable  = Factory(Ignore)
    __first__:   bool      = True
    epilog:      str       = (
        f"• Made with [red]:heart:[/red] by [green]Broken Source Software[/green] [yellow]v{Broken.VERSION}[/yellow]\n\n"
        "→ [italic grey53]Consider [blue][link=https://www.patreon.com/Tremeschin]Sponsoring[/link][/blue] my Open Source Work[/italic grey53]"
    )

    def __attrs_post_init__(self):
        self.app = Typer(
            help=self.description or "No help provided",
            add_help_option=self.help_option,
            pretty_exceptions_enable=False,
            no_args_is_help=True,
            add_completion=False,
            rich_markup_mode="rich",
            chain=self.chain,
            epilog=self.epilog,
        )

    __panel__: str = None

    @contextlib.contextmanager
    def panel(self, name: str) -> Generator[None, None, None]:
        try:
            self.__panel__ = name
            yield
        finally:
            self.__panel__ = None

    def command(self,
        callable: Callable,
        help: str=None,
        add_help_option: bool=True,
        name: str=None,
        context: bool=True,
        default: bool=False,
        panel: str=None,
        **kwargs,
    ):
        # Command must be implemented
        if getattr(callable, "__isabstractmethod__", False):
            return

        # Maybe get callable name
        name = name or callable.__name__

        # Create Typer command
        self.app.command(
            help=help or callable.__doc__ or None,
            add_help_option=add_help_option,
            name=name,
            rich_help_panel=panel or self.__panel__ ,
            context_settings=dict(
                allow_extra_args=True,
                ignore_unknown_options=True,
            ) if context else None,
            **kwargs,
        )(callable)

        # Add to known commands
        self.commands.append(name)

        # Set as default command
        self.default = name if default else self.default

    def __call__(self, *args, shell: bool=False):
        while True:
            args = flatten(args)

            # Insert default implied command
            first = (args[0] if (len(args) > 0) else None)
            if self.default and ((not args) or (first not in self.commands)):
                args.insert(0, self.default)

            # Update args to BrokenTyper
            if not self.__first__:
                args = shlex.split(input("\n:: BrokenShell (enter for help) $ "))
            self.__first__ = False

            try:
                self.app(args)
            except SystemExit:
                self.exit_hook()
            except KeyboardInterrupt:
                log.success("BrokenTyper stopped by user")
                self.exit_hook()
            except Exception as e:
                self.exit_hook()
                raise e

            # Don't continue on non BrokenShell mode
            if not shell:
                break
