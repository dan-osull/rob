from pathlib import WindowsPath

import click
from click import ClickException
from click_help_colors import HelpColorsGroup

from console import (
    HELP_HEADERS_COLOR,
    HELP_OPTIONS_COLOR,
    print_,
    print_library_table,
    style_library,
    style_path,
    style_project,
)
from exceptions import show_red_error
from filesystem import add_folder_actions, remove_folder_actions
from folders import Folder, FolderLibrary


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


@click.group(
    cls=HelpColorsGroup,
    help_headers_color=HELP_HEADERS_COLOR,
    help_options_color=HELP_OPTIONS_COLOR,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.pass_context
@library_folder_option
def cli(ctx, library_folder: WindowsPath):
    """Utility for..."""
    ClickException.show = show_red_error
    # TODO: doesn't change color of subclasses with custom show() e.g. error on exists=True
    print_()
    print_(style_project())
    print_()

    if ctx.invoked_subcommand is None:
        # Show help and list library if no command provided
        click.echo(cli.get_help(ctx))
        print_("")
        print_library_table(library_folder)


@cli.command(
    name="list",
)
@library_folder_option
def list_(library_folder: WindowsPath):
    """List folders in library"""
    print_library_table(library_folder)


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
    # Do this after symlink check to avoid resolving symlink!
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
    cli()  # pylint: disable=no-value-for-parameter
    # TODO: how to cleanup library and filesystem if left in an inconsistent state?
    # TODO: how to handle failure part way through action?
