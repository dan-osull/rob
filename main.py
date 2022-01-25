from pathlib import Path
from folders import FolderList, Folder

import click

JSON_FILENAME = "folders.json"


def save_json(folder_list: FolderList, filename=JSON_FILENAME) -> None:
    json = folder_list.json()
    with open(filename, "w") as file:
        file.write(json)


def load_json(filename=JSON_FILENAME) -> FolderList:
    return FolderList.parse_file(filename)


@click.group()
def cli():
    pass


@cli.command()
def save_example():
    managed_folders = [
        Folder(source_dir=Path("C:\Temp")),
        Folder(source_dir=Path("C:\Windows")),
    ]
    managed_folders = FolderList.parse_obj(managed_folders)
    save_json(managed_folders)


@cli.command()
@click.option(
    "--json-filename",
    default=JSON_FILENAME,
    help="List folders that are currently managed",
)
def list(json_filename):
    loaded_folders = load_json(json_filename)
    click.echo(loaded_folders)


if __name__ == "__main__":
    cli()
    # if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    #     print("running in a PyInstaller bundle")
    #     cli(sys.argv[1:])
