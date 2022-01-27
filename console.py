from rich.console import Console

from config import PROJECT_NAME

# https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors

console = Console()
print_ = console.print


def style_project_name() -> str:
    return f"[purple]{PROJECT_NAME}[/purple]"
