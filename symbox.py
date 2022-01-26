from pathlib import WindowsPath
from typing import Optional

import click
from click import ClickException
from rich import print
from tabulate import tabulate

from exceptions import show_red_error
from folders import Folder, FolderLibrary


@click.group()
def cli():
    "Utility for..."
    # TODO: doesn't change color of subclasses with custom show() e.g. error on exists=True
    ClickException.show = show_red_error


def library_folder_option(function):
    return click.option(
        "--library-folder",
        default=None,
        type=click.Path(exists=True, file_okay=False, path_type=WindowsPath),
        help="The path of the library folder. The current folder is used by default.",
    )(function)


@cli.command(name="list")
@library_folder_option
def list_(library_folder: Optional[WindowsPath]):
    "List folders in library"
    library = FolderLibrary(library_folder)
    table = tabulate(library.get_table_data(), headers="keys")

    print("")
    print(
        f"{len(library.folders)} folders in [cyan]{library.library_folder}[/cyan] library."
    )
    if table:
        print("")
        print(table)
    print("")


@cli.command()
@library_folder_option
@click.argument(
    "folder-path",
    type=click.Path(exists=True, file_okay=False, path_type=WindowsPath),
)
def add(folder_path: WindowsPath, library_folder: Optional[WindowsPath]):
    "Add FOLDER_PATH to library"
    # Resolve path to correct capitalisation
    folder_path = folder_path.resolve()
    library = FolderLibrary(library_folder)
    if folder_path in library.source_dirs:
        raise ClickException(f"Cannot add folder. {folder_path} is already managed.")
    # TODO: should not be possible to add child (and parent?) of existing folder
    # TODO: don't allow root of disk

    folder = Folder(source_dir=folder_path)

    print(f"Add {folder} to [cyan]{library.library_folder}[/cyan] library?")
    click.confirm(text="Confirm", abort=True)
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
def remove(folder_path: WindowsPath, library_folder: Optional[WindowsPath]):
    "Remove FOLDER_PATH from library"
    library = FolderLibrary(library_folder)
    folder = library.get_folder_by_path(folder_path)
    if not folder:
        # TODO: either accept target_dir_name, or add more help about using source_dir
        raise ClickException(f"Cannot find info for folder: {folder_path}.")

    print(f"Remove {folder} from [cyan]{library.library_folder}[/cyan] library?")

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
