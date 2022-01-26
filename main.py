from pathlib import WindowsPath

import click
from click import ClickException
from rich import print
from tabulate import tabulate

from exceptions import show_red_error
from folders import Folder, load_json, save_json


@click.group()
def main():
    "Utility for..."
    # TODO: doesn't change color of e.g. exists=True error
    ClickException.show = show_red_error


@main.command()
def list():
    "List managed folders"
    folder_list = load_json()
    print(tabulate(folder_list.get_table_data(), headers="keys", showindex="always"))


@main.command()
@click.argument(
    "folder-path",
    type=click.Path(exists=True, file_okay=False, path_type=WindowsPath),
)
def add(folder_path: WindowsPath):
    "Add folder to list"
    # Resolve path to correct capitalisation
    folder_path = folder_path.resolve()
    folder_list = load_json()
    if folder_path in folder_list.source_dirs:
        raise ClickException(f"Cannot add folder. {folder_path} is already managed.")
    # TODO: should also be impossible to add child (and parent?) of existing folder

    new_folder = Folder(source_dir=folder_path)

    folder_list.add_folder(new_folder)
    save_json(folder_list)
    print(f"Added {new_folder}")
    # TODO: finish


@main.command()
@click.argument(
    "folder-path",
    type=click.Path(path_type=WindowsPath),
)
def remove(folder_path: WindowsPath):
    "Remove folder from list"
    folder_list = load_json()
    item_found = folder_list.get_folder_by_path(folder_path)
    if not item_found:
        raise ClickException(f"Cannot find info for folder: {folder_path}.")
    folder_list.remove_folder(item_found)
    save_json(folder_list)
    print(f"Removed {item_found}")
    # TODO: finish


if __name__ == "__main__":
    main()
