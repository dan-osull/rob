from pathlib import WindowsPath
from typing import Union

from rich.console import Console

from config import PROJECT_NAME
from folders import FolderLibrary

# https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors

console = Console(highlight=False)
print_ = console.print


def style_project() -> str:
    return f"[bold][purple]{PROJECT_NAME}[/purple][/bold]"


def style_library(library: FolderLibrary) -> str:
    return (
        f"{style_project()} library at [purple]{str(library.library_folder)}[/purple]"
    )


def style_path(obj: Union[WindowsPath, str]) -> str:
    return f"[cyan]{str(obj)}[/cyan]"
