from pathlib import WindowsPath

import click
from click import ClickException
from click_default_group import DefaultGroup
from click_help_colors import HelpColorsGroup
from tabulate import tabulate

from console import console, print_, style_library, style_path, style_project
from exceptions import show_red_error
from filesystem import add_folder_actions, remove_folder_actions
from folders import Folder, FolderLibrary


class ClickGroup(DefaultGroup, HelpColorsGroup):
    ...


@click.group(
    cls=ClickGroup,
    help_headers_color="green",
    help_options_color="cyan",
    default_if_no_args=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def cli():
    """Utility for..."""
    print_()
    print_(style_project())
    print_()
    # TODO: doesn't change color of subclasses with custom show() e.g. error on exists=True
    ClickException.show = show_red_error


def library_folder_option(function):
    return click.option(
        "-l",
        "--library-folder",
        default=".",
        type=click.Path(
            exists=True, file_okay=False, path_type=WindowsPath, resolve_path=True
        ),
        help="The path of the library. The current folder is used by default.",
    )(function)


@cli.command(
    name="list",
    default=True,
)
@library_folder_option
@click.pass_context
def list_(ctx, library_folder: WindowsPath):
    """List folders in library"""

    library = FolderLibrary(library_folder)
    plur_s = "" if len(library.folders) == 1 else "s"
    table = tabulate(library.get_table_data(), headers="keys")

    # Show help from root context
    click.echo(cli.get_help(ctx))
    # TODO: missing --library-folder option
    print_("")
    console.rule(style="grey50")
    print_("")
    print_(f"{len(library.folders)} folder{plur_s} in {style_library(library)}")
    if table:
        print_("")
        table = table.split("\n", 1)
        # Header row
        print_(f"[green]{table[0]}[/green]")
        table = table[1].split("\n", 1)
        # Divider row
        print_(f"{table[0]}")
        print_(style_path(table[1]))
    print_("")


@cli.command(no_args_is_help=True)
@library_folder_option
@click.argument(
    "folder-path",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=WindowsPath,
    ),
)
def add(folder_path: WindowsPath, library_folder: WindowsPath):
    """Add FOLDER_PATH to library"""
    if folder_path.is_symlink():
        raise ClickException(
            f"Cannot add folder. {folder_path} is a symlink. Is it already in library?"
        )
    # Resolve path to fix capitalisation
    # Do this after check to avoid resolving symlink!
    folder_path = folder_path.resolve()
    library = FolderLibrary(library_folder)
    if folder_path in library.source_dirs:
        raise ClickException(f"Cannot add folder. {folder_path} is already in library.")

    # TODO: should not be possible to add child (and parent?) of existing folder
    # TODO: don't allow root of disk
    # TODO: source and dest should be on different disks

    folder = Folder(source_dir=folder_path)

    print_(
        f"[bold]Add folder {style_path(folder.source_dir)} to {style_library(library)} ?[/bold]"
    )
    click.confirm(text="Confirm", abort=True)
    add_folder_actions(folder, library)

    library.folders.append(folder)
    library.save()

    print_("")
    print_(
        f"[bold]Added {style_path(folder.source_dir)} to {style_library(library)} with name {style_path(folder.target_dir_name)}[/bold]"
    )


@cli.command(no_args_is_help=True)
@library_folder_option
@click.argument("folder-path")
def remove(folder_path: str, library_folder: WindowsPath):
    """Remove FOLDER_PATH from library"""
    # Not casting folder_path to Path type so that we can search for target_dir_name too
    library = FolderLibrary(library_folder)
    folder = library.find_folder(folder_path)
    if not folder:
        raise ClickException(f"Cannot find info for folder: {folder_path}.")

    print_(
        f"[bold]Remove folder {style_path(folder.source_dir)} with name {style_path(folder.target_dir_name)} from {style_library(library)} ?[/bold]"
    )

    click.confirm(
        text="Confirm",
        abort=True,
    )
    remove_folder_actions(folder, library)

    library.folders.remove(folder)
    library.save()

    print_(f"Removed {folder}")


if __name__ == "__main__":
    cli()
    # TODO: how to cleanup library and filesystem if left in an inconsistent state?
    # TODO: how to handle failure part way through action?
