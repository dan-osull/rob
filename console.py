from pathlib import WindowsPath
from typing import Union

from rich.console import Console
from tabulate import tabulate

from config import PROJECT_NAME
from folders import FolderLibrary

# ANSI colors(?)
HELP_HEADERS_COLOR = "green"
HELP_OPTIONS_COLOR = "cyan"

# https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors
console = Console(highlight=False)
print_ = console.print


def print_library_table(library_folder: WindowsPath) -> None:
    library = FolderLibrary(library_folder)
    table = tabulate(library.get_table_data(), headers="keys")
    plur_s = "" if len(library.folders) == 1 else "s"

    print_(f"{len(library.folders)} folder{plur_s} in {style_library(library)}")
    if table:
        print_("")
        table = table.split("\n", 1)
        # Header row
        print_(f"{table[0]}")
        table = table[1].split("\n", 1)
        # Divider row
        print_(f"{table[0]}")
        # Table body
        print_(style_path(table[1]))
    print_("")


def style_project() -> str:
    return f"[bold][purple]{PROJECT_NAME}[/purple][/bold]"


def style_library(library: FolderLibrary) -> str:
    library_path = str(library.library_folder).strip("\\")
    return f"{style_project()} library at [purple]{library_path}[/purple]"


def style_path(obj: Union[WindowsPath, str]) -> str:
    return f"[cyan]{str(obj)}[/cyan]"
