from pathlib import Path, WindowsPath

import click
from click import ClickException

from folders import Folder, FolderList, load_json, save_json


@click.group()
def cli():
    """Utility for"""


@cli.command()
def save_example():
    managed_folders = [
        Folder(source_dir=WindowsPath("C:\\Temp")),
        Folder(source_dir=WindowsPath("C:\\Windows")),
    ]
    managed_folders = FolderList.parse_obj(managed_folders)
    save_json(managed_folders)


@cli.command()
def list():
    """
    Read folders.json configuration file and list managed folders.
    """
    managed_folders = load_json()
    click.echo(managed_folders)


@cli.command()
@click.argument(
    "folder-path",
    type=click.Path(exists=True, file_okay=False, path_type=WindowsPath),
)
def add(folder_path: WindowsPath):
    managed_folders = load_json()
    if folder_path in managed_folders.source_dirs:
        raise ClickException("Cannot add. Folder is already managed.")
    # TODO: should also be impossible to add child (or parent?) of existing folder
    managed_folders.add_folder(Folder(source_dir=folder_path))
    save_json(managed_folders)
    # TODO: finish


@cli.command()
@click.argument(
    "folder-path",
    type=click.Path(path_type=WindowsPath),
)
def remove(folder_path: WindowsPath):
    managed_folders = load_json()
    item_found = managed_folders.get_folder_by_path(folder_path)
    if not item_found:
        raise ClickException("Cannot find folder info.")
    managed_folders.remove_folder(item_found)
    save_json(managed_folders)
    # TODO: finish


if __name__ == "__main__":
    cli()
