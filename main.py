from pathlib import WindowsPath

import click
from click import ClickException
from click_help_colors import HelpColorsGroup

from console import (
    HELP_HEADERS_COLOR,
    HELP_OPTIONS_COLOR,
    confirm_action,
    print_,
    print_library_table,
    print_success,
    print_title,
    style_library,
    style_path,
)
from exceptions import show_red_error
from filesystem import run_add_folder_actions, run_remove_folder_actions
from library import Folder, FolderLibrary


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
    print_title()

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


def dry_run_option(function):
    return click.option(
        "-d",
        "--dry-run",
        default=False,
        type=bool,
        is_flag=True,
        help="Run pre-flight checks but do not move data",
    )(function)


@cli.command(no_args_is_help=True)
@library_folder_option
@dry_run_option
@click.argument(
    "folder-path",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=WindowsPath,
    ),
)
def add(folder_path: WindowsPath, library_folder: WindowsPath, dry_run: bool):
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
        f"[bold]Add folder {style_path(folder.source_dir)} to {style_library(library)}[/bold]"
    )
    confirm_action(dry_run=dry_run)
    run_add_folder_actions(folder, library, dry_run)

    if not dry_run:
        library.folders.append(folder)
        library.save()
        print_(
            f"\n[bold]Added {style_path(folder.source_dir)} with name {style_path(folder.target_dir_name)} to {style_library(library)} [/bold]"
        )
        print_(
            f"Data is now in subfolder with name {style_path(folder.target_dir_name)}"
        )
        print_(f"{style_path(folder.source_dir)} [bold]is[/bold] a symlink")
    else:
        print_success("\nDry run result:")


@cli.command(no_args_is_help=True)
@library_folder_option
@dry_run_option
@click.argument("folder-path")
def remove(folder_path: str, library_folder: WindowsPath, dry_run: bool):
    """Remove FOLDER_PATH from library"""
    # Not casting folder_path to Path type so that we can search for target_dir_name too
    library = FolderLibrary(library_folder)
    folder = library.find_folder(folder_path)
    if not folder:
        raise ClickException(f"Cannot find folder information: {folder_path}.")

    print_(
        f"[bold]Remove folder {style_path(folder.source_dir)} with name {style_path(folder.target_dir_name)} from {style_library(library)}[/bold]"
    )
    confirm_action(dry_run=dry_run)
    run_remove_folder_actions(folder, library, dry_run=dry_run)

    if not dry_run:
        library.folders.remove(folder)
        library.save()
        print_(
            f"\n[bold]Removed {style_path(folder.source_dir)} with name {style_path(folder.target_dir_name)} from {style_library(library)} [/bold]"
        )
        print_(f"Data is now at {style_path(folder.source_dir)}")
        print_(f"{style_path(folder.source_dir)} is [bold]not[/bold] a symlink")
    else:
        print_success("\nDry run result:")


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
    # TODO: how to cleanup library and filesystem if left in an inconsistent state?
    # TODO: how to handle failure part way through action?
