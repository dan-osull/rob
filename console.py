from typing import Any

from rich.console import Console

from config import PROJECT_NAME
from folders import FolderLibrary

# https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors

console = Console()
print_ = console.print


def style_library(library: FolderLibrary) -> str:
    return f"[purple]{PROJECT_NAME}[/purple] library at [purple]{str(library.library_folder)}[/purple]"


def style_path(obj: Any) -> str:
    return f"[cyan]{str(obj)}[/cyan]"
