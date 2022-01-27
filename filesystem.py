import os
from pathlib import Path, WindowsPath

from click import ClickException

from console import print_
from folders import Folder, FolderLibrary

ROBOCOPY_PATH: WindowsPath = (
    WindowsPath(os.environ["SystemRoot"]).joinpath("system32/robocopy.exe").resolve()
)


def test_dir_creation(path: WindowsPath) -> None:
    """Test write access by creating and deleting an empty folder"""
    print_(f"Testing write access to {path}")
    if path.exists():
        raise ClickException(f"{path} already exists")
    try:
        Path.mkdir(path)
        Path.rmdir(path)
    except PermissionError as e:
        raise ClickException(
            f"Could not create {path}. Do you need to run Command Prompt as Administrator?"
        ) from e


def rename_folder(source: WindowsPath, target: WindowsPath) -> None:
    print_(f"Renaming {source=} to {target=}")
    try:
        source.rename(target)
    except PermissionError as e:
        raise ClickException(
            f"Unable to rename {source} to {target}. Is an application locking the folder open?"
        ) from e


def add_folder_actions(folder: Folder, library: FolderLibrary):
    """Filesystem actions for `add` command"""
    target_dir = folder.get_target_dir(library.library_folder)
    test_dir_creation(target_dir)
    temp_dir = folder.get_temp_dir()
    test_dir_creation(temp_dir)
    # TODO: test symlink creation at temp_dir location?

    rename_folder(folder.source_dir, temp_dir)

    print_(f"Copying data from {temp_dir=} to {target_dir=}")
    # TODO: robocopy here

    print_(f"Making symlink from {folder.source_dir=} to {target_dir=}")
    # TODO: make symlink here

    # TODO: delete source_dir here


def remove_folder_actions(folder: Folder, library: FolderLibrary):
    """Filesystem actions for `remove` command"""
    target_dir = folder.get_target_dir(library.library_folder)
    if not target_dir.exists():
        raise ClickException(f"{target_dir} does not exist")
        # TODO: how to handle? remove library entry?
    temp_dir = folder.get_temp_dir()
    test_dir_creation(temp_dir)

    print_(f"Copying data from {target_dir=} to {temp_dir=}")
    # TODO: robocopy here

    print_(f"Deleting symlink from {folder.source_dir=} to {target_dir=}")
    # TODO: delete symlink here

    print_(f"Renaming {temp_dir=} to {folder.source_dir=}")
    # TODO: rename here

    # TODO: delete target_dir here
