from pathlib import WindowsPath

import click
from click import ClickException
from click_default_group import DefaultGroup
from rich import print  # pylint: disable=redefined-builtin
from tabulate import tabulate

from console import style_project_name
from exceptions import show_red_error
from filesystem import add_folder_actions
from folders import Folder, FolderLibrary


@click.group(
    cls=DefaultGroup,
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


@cli.command(name="list", default=True)
@library_folder_option
@click.pass_context
def list_(ctx, library_folder: WindowsPath):
    """List folders in library"""
    # Provide help from root context
    click.echo(cli.get_help(ctx.parent))
    library = FolderLibrary(library_folder)
    table = tabulate(library.get_table_data(), headers="keys")

    print("")
    print(
        f"{len(library.folders)} folders in {style_project_name()} library at [cyan]{library.library_folder}[/cyan]"
    )
    if table:
        print("")
        print(table)
    print("")


@cli.command()
@library_folder_option
@click.argument(
    "folder-path",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=WindowsPath,
        # Resolve path to correct capitalisation
        resolve_path=True,
    ),
)
def add(folder_path: WindowsPath, library_folder: WindowsPath):
    """Add FOLDER_PATH to library"""
    library = FolderLibrary(library_folder)
    if folder_path in library.source_dirs:
        raise ClickException(f"Cannot add folder. {folder_path} is already managed.")
    # TODO: should not be possible to add child (and parent?) of existing folder
    # TODO: don't allow root of disk

    folder = Folder(source_dir=folder_path)

    print(
        f"Add {folder} to {style_project_name()} library at [cyan]{library.library_folder}[/cyan]?"
    )
    click.confirm(text="Confirm", abort=True)
    # add_folder_actions(folder, library)

    library.folders.append(folder)
    library.save()

    print(f"Added {folder}")
    # TODO: finish


@cli.command()
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

    print(
        f"Remove {folder} from {style_project_name()} library at [cyan]{library.library_folder}[/cyan]?"
    )

    click.confirm(
        text="Confirm",
        abort=True,
    )
    library.folders.remove(folder)
    library.save()

    print(f"Removed {folder}")
    # TODO: finish


if __name__ == "__main__":
    cli()
    # TODO: can we find invokations without a command here, instead of by using external module?
