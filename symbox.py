from pathlib import WindowsPath

import click
from click import ClickException
from rich import print
from tabulate import tabulate

from exceptions import show_red_error
from folders import Folder, FolderList


@click.group()
def cli():
    "Utility for..."
    # TODO: doesn't change color of e.g. exists=True error,
    # because its subclass has a custom show()
    ClickException.show = show_red_error


@cli.command()
def list():
    "List managed folders"
    folder_list = FolderList()
    table = tabulate(
        folder_list.get_table_data(),
        headers="keys",
        # showindex="always"
    )
    print(
        f"""
Folders currently managed:

{table}
       """
    )


@cli.command()
@click.argument(
    "folder-path",
    type=click.Path(exists=True, file_okay=False, path_type=WindowsPath),
)
def add(folder_path: WindowsPath):
    "Add folder to list"
    # Resolve path to correct capitalisation
    folder_path = folder_path.resolve()
    folder_list = FolderList()
    if folder_path in folder_list.source_dirs:
        raise ClickException(f"Cannot add folder. {folder_path} is already managed.")
    # TODO: should also be impossible to add child (and parent?) of existing folder

    folder = Folder(source_dir=folder_path)

    click.confirm(text=f"Add {folder}?", abort=True)
    folder_list.folders.append(folder)
    folder_list.save()

    print(f"Added {folder}")
    # TODO: finish


@cli.command()
@click.argument(
    "folder-path",
    type=click.Path(path_type=WindowsPath),
)
def remove(folder_path: WindowsPath):
    "Remove folder from list"
    folder_list = FolderList()
    folder = folder_list.get_folder_by_path(folder_path)
    if not folder:
        raise ClickException(f"Cannot find info for folder: {folder_path}.")

    click.confirm(text=f"Remove {folder}?", abort=True)
    folder_list.folders.remove(folder)
    folder_list.save()

    print(f"Removed {folder}")
    # TODO: finish


if __name__ == "__main__":
    cli()
