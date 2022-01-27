from pathlib import WindowsPath

import click
from click import ClickException
from click_default_group import DefaultGroup
from click_help_colors import HelpColorsGroup
from tabulate import tabulate

from console import console, print_, style_library, style_path
from exceptions import show_red_error
from filesystem import add_folder_actions, remove_folder_actions
from folders import Folder, FolderLibrary


class ClickGroup(DefaultGroup, HelpColorsGroup):
    ...


@click.group(
    cls=ClickGroup,
    help_headers_color="yellow",
    help_options_color="green",
    default_if_no_args=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
def cli():
    """Utility for..."""
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
        help="The path of the library folder. The current folder is used by default.",
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
    click.echo(cli.get_help(ctx.parent))
    print_("")
    console.rule(style="grey50")
    print_("")
    print_(f"{len(library.folders)} folder{plur_s} in {style_library(library)}")
    if table:
        print_("")
        print_(table)
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
            f"Cannot add folder. {folder_path} is already a symlink. Is it managed?"
        )

    library = FolderLibrary(library_folder)
    if folder_path in library.source_dirs:
        raise ClickException(f"Cannot add folder. {folder_path} is already managed.")

    # Resolve path to correct capitalisation
    # Do this after library has been checked to avoid resolving symlink!
    folder_path = folder_path.resolve()
    # TODO: should not be possible to add child (and parent?) of existing folder
    # TODO: don't allow root of disk
    # TODO: source and dest should be on different disks

    folder = Folder(source_dir=folder_path)

    print_(
        (
            f"[bold]Add folder {style_path(folder.source_dir)} to {style_library(library)} ?[/bold]"
        )
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
@click.argument(
    "folder-path",
    type=click.Path(path_type=WindowsPath),
)
def remove(folder_path: WindowsPath, library_folder: WindowsPath):
    """Remove FOLDER_PATH from library"""
    library = FolderLibrary(library_folder)
    folder = library.get_folder_by_path(folder_path)
    if not folder:
        # TODO: either accept target_dir_name, or add more help about using source_dir
        raise ClickException(f"Cannot find info for folder: {folder_path}.")

    print_(
        f"[bold]Remove folder {style_path(folder.source_dir)} from {style_library(library)} ?[/bold]"
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
