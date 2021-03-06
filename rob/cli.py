from pathlib import WindowsPath

import click
from click import ClickException
from click_help_colors import HelpColorsGroup

from rob.actions import AddFolderActions, RemoveFolderActions
from rob.console import (
    HELP_HEADERS_COLOR,
    HELP_OPTIONS_COLOR,
    print_,
    print_library_info,
    print_success,
    print_title,
    style_library,
    style_path,
)
from rob.exceptions import echo_red_error
from rob.folders import Folder, Library


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
    """
    rob is a command line tool that frees up space on your SSD by moving data to a library of folders on another disk.

    rob creates a symlink from the original location to the library so that games continue to work and can be updated.
    """
    click.exceptions.echo = echo_red_error  # type: ignore
    print_title()

    if ctx.invoked_subcommand is None:
        # Show help and library info if no command provided
        click.echo(cli.get_help(ctx))
        print_("")
        library = Library(library_folder)
        print_library_info(library)


@cli.command(name="list")
@library_folder_option
def list_(library_folder: WindowsPath):
    """List folders in library and their size"""
    library = Library(library_folder)
    print_library_info(library, show_size=True)


def dry_run_option(function):
    return click.option(
        "-d",
        "--dry-run",
        default=False,
        type=bool,
        is_flag=True,
        help="Run pre-flight checks but do not move data.",
    )(function)


def dont_copy_permissions_option(function):
    return click.option(
        "--dont-copy-permissions",
        default=False,
        type=bool,
        is_flag=True,
        help="Do not copy NTFS permission and owner data (advanced).",
    )(function)


@cli.command(no_args_is_help=True)
@library_folder_option
@dry_run_option
@dont_copy_permissions_option
@click.option(
    "--allow-same-disk",
    default=False,
    type=bool,
    is_flag=True,
    help="Allow source folder to be on same disk as rob library (advanced).",
)
@click.argument(
    "folder-path",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=WindowsPath,
    ),
)
def add(
    folder_path: WindowsPath,
    library_folder: WindowsPath,
    dry_run: bool,
    dont_copy_permissions: bool,
    allow_same_disk: bool,
):
    """
    Add FOLDER_PATH to library

    Data is moved to the library folder and the original location is replaced by a symlink.
    """
    if folder_path.is_symlink():
        raise ClickException(
            f"Cannot add folder. {folder_path} is a symlink. Is it already in library?"
        )
    # Resolve path to fix capitalisation
    # Do this after symlink check to avoid resolving symlink!
    folder_path = folder_path.resolve()
    library = Library(library_folder)

    if folder_path in library.source_dirs:
        raise ClickException(f"Cannot add folder. {folder_path} is already in library.")

    folder = Folder(source_dir=folder_path)
    if library.library_folder.drive == folder.source_dir.drive and not allow_same_disk:
        raise ClickException(
            f"Cannot add {folder_path}. Source folder and library should be on different disks. "
        )
    if len(folder.source_dir.parts) == 1:
        raise ClickException("Cannot add the root folder of a disk.")
    for source_dir in library.source_dirs:
        if folder_path in source_dir.parents:
            raise ClickException(
                f"Cannot add {folder_path} because it is the parent of an existing source folder."
            )
    if library.library_folder in folder_path.parents:
        # Will resolve as child of library folder
        raise ClickException(
            f"Cannot add {folder_path} because it is the child of an existing source folder."
        )
    msg = f"[bold]Add folder {style_path(folder.source_dir)} to {style_library(library)}[/bold]"
    print_(msg)

    actions = AddFolderActions(folder, library, dry_run, dont_copy_permissions)
    actions.run()

    if not dry_run:
        # Load library again in case it has been updated by another process
        library = Library(library_folder)
        library.add_folder(folder)
        library.save()
        print_success("\n" + msg)
        print_(f"Data is now in subfolder with name {style_path(folder.short_name)}")
        print_(f"{style_path(folder.source_dir)} [bold]is[/bold] a symlink")
    else:
        print_success("\nDry run result:")


@cli.command(no_args_is_help=True)
@library_folder_option
@dry_run_option
@dont_copy_permissions_option
@click.argument("folder-path")
def remove(
    folder_path: str,
    library_folder: WindowsPath,
    dry_run: bool,
    dont_copy_permissions: bool,
):
    """
    Remove FOLDER_PATH from library

    Data is restored to its original location.

    You can also select a folder by providing its ID or Name.
    """
    # Not casting folder_path to Path type so that we can search for target_dir_name too
    library = Library(library_folder)
    folder = library.find_folder(folder_path)

    if not folder:
        raise ClickException(f"Cannot find folder information: {folder_path}.")
    if not folder.get_library_subdir(library).exists():
        library.remove_folder(folder)
        library.save()
        raise ClickException(
            f"{folder.get_library_subdir(library)} does not exist. Removed from folder list."
        )

    msg = f"[bold]Remove folder {style_path(folder.source_dir)} with name {style_path(folder.short_name)} from {style_library(library)}[/bold]"
    print_(msg)
    actions = RemoveFolderActions(folder, library, dry_run, dont_copy_permissions)
    actions.run()

    if not dry_run:
        # Load library again in case it has been updated by another process
        library = Library(library_folder)
        library.remove_folder(folder)
        library.save()
        print_success("\n" + msg)
        print_(f"Data is now at {style_path(folder.source_dir)}")
        print_(f"{style_path(folder.source_dir)} is [bold]not[/bold] a symlink")
    else:
        print_success("\nDry run result:")
