from pathlib import Path, WindowsPath
from folders import FolderList, Folder

import click
from click import ClickException

JSON_FILENAME = "folders.json"


def save_json(folder_list: FolderList, filename=JSON_FILENAME) -> None:
    json = folder_list.json()
    with open(filename, "w") as file:
        file.write(json)


def load_json(filename=JSON_FILENAME) -> FolderList:
    return FolderList.parse_file(filename)


@click.group()
def cli():
    """Utility for"""


@cli.command()
def save_example():
    managed_folders = [
        Folder(source_dir=Path("C:\Temp")),
        Folder(source_dir=Path("C:\Windows")),
    ]
    managed_folders = FolderList.parse_obj(managed_folders)
    save_json(managed_folders)


@cli.command()
def list():
    """
    Read folders.json configuration file and list managed folders.
    """
    managed_folders = load_json(JSON_FILENAME)
    click.echo(managed_folders)


@cli.command()
@click.argument(
    "folder-path",
    type=click.Path(exists=True, file_okay=False, path_type=WindowsPath),
)
def add(folder_path: WindowsPath):
    managed_folders = load_json(JSON_FILENAME)
    if folder_path in managed_folders.source_dirs:
        raise ClickException("Cannot add. Folder is already managed.")
    # TODO: should also not be possible to add child (or parent?) of existing folder
    click.echo(folder_path)


@cli.command()
@click.argument(
    "folder-path",
    type=click.Path(path_type=WindowsPath),
)
def remove(folder_path: WindowsPath):
    managed_folders = load_json(JSON_FILENAME)


if __name__ == "__main__":
    cli()
