from pathlib import WindowsPath
from typing import Union

import click
from rich.console import Console
from tabulate import tabulate

import filesystem
from constants import PROJECT_NAME, VERSION
from folders import Library

# click.termui._ansi_colors
HELP_HEADERS_COLOR = "bright_white"
HELP_OPTIONS_COLOR = "cyan"

# https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors
console = Console(highlight=False)
print_ = console.print


def print_library_info(library: Library, show_size: bool = False) -> None:
    print_("")
    disk_usage = library.disk_usage
    for disk in disk_usage:
        print_disk_usage(disk)
    print_("")
    print_library_folder_count(library)
    table_data = library.get_table_data(show_size=show_size)
    if table_data:
        print_library_table(table_data)
        if not show_size:
            print_("\nRun [bold]rob list[/bold] to see size of folders.")


def print_disk_usage(disk: filesystem.DiskUsage) -> None:
    print_(
        f"Drive {style_path(disk.drive)} "
        f"{style_bytes_as_gb((disk.usage.used),ndigits=None)} used / "
        f"{style_bytes_as_gb(disk.usage.total,ndigits=None)} total "
        f"({round(disk.usage.used/disk.usage.total*100)}% full)"
    )


def print_library_folder_count(library: Library) -> None:
    plur_s = "" if len(library.folders) == 1 else "s"
    print_(f"{len(library.folders)} folder{plur_s} in {style_library(library)}")


def print_library_table(table_data: list[dict]) -> None:
    table = tabulate(table_data, headers="keys")
    print_("")
    table = table.split("\n", 1)
    # Header row
    print_(f"[bright_white]{table[0]}[/bright_white]")
    table = table[1].split("\n", 1)
    # Divider row
    print_(f"{table[0]}")
    # Table body
    print_(style_path(table[1]))


def print_fail(msg: str = "") -> None:
    print_(f"{msg} [bold][red]FAIL[/red][/bold]")


def print_success(msg: str = "") -> None:
    print_(f"{msg} [bold][green]SUCCESS[/green][/bold]")


def print_skipped() -> None:
    print_(" [grey50]SKIPPED[/grey50]")


def print_title() -> None:
    # Font Slant at https://patorjk.com/software/taag/#p=display&f=Slant&t=rob
    # See logo.txt for original
    logo_text = "               __\n   _________  / /_ \n  / ___/ __ \\/ __ \\\n / /  / /_/ / /_/ /\n/_/   \\____/_.___/"
    print_(f"[bold][purple]{logo_text}[/purple][/bold]  v.{VERSION}\n")
    print_(
        "[bold]Help:[/bold] [link=https://github.com/dan-osull/rob/]https://github.com/dan-osull/rob/[/link]\n"
    )


def style_project() -> str:
    return f"[bold][purple]{PROJECT_NAME}[/purple][/bold]"


def style_library(library: Library) -> str:
    library_path = str(library.library_folder).strip("\\")
    return f"{style_project()} library at [purple]{library_path}[/purple]"


def style_path(obj: Union[WindowsPath, str]) -> str:
    return f"[cyan]{str(obj)}[/cyan]"


def style_bytes_as_gb(size_bytes: int, ndigits=1) -> str:
    gigabytes = round(size_bytes / 1024**3, ndigits)
    return f"{gigabytes} GB"


def confirm_action(dry_run: bool) -> None:
    if dry_run:
        confirm_text = "Confirm dry run?"
    else:
        confirm_text = "Confirm?"
    click.confirm(text=confirm_text, abort=True)
