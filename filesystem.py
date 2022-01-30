import os
import shutil
from pathlib import WindowsPath

from click import ClickException

from console import print_, print_skipped, print_success, style_path
from library import Folder, FolderLibrary
from robocopy import run_robocopy


def get_tree_size(path: WindowsPath) -> int:
    """Return total size of files in given path and subdirs."""
    # https://www.python.org/dev/peps/pep-0471/
    if not WindowsPath(path).exists():
        # Avoid race with file creation
        return 0
    total = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)  # type: ignore
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total


def test_dir_creation(path: WindowsPath) -> None:
    """Test write access by creating and deleting an empty folder"""
    print_(f"Testing write access to {style_path(path)}", end="")
    if path.exists():
        raise ClickException(f"{path} already exists")
    try:
        path.mkdir()
    except PermissionError as e:
        raise ClickException(
            f"Could not create {path}. Do you need to run Command Prompt as Administrator?"
        ) from e
    finally:
        if path.exists():
            path.rmdir()
    print_success()


def test_symlink_creation(source: WindowsPath, target: WindowsPath) -> None:
    print_(
        f"Testing symlink creation from {style_path(source)} to {style_path(target)}",
        end="",
    )
    target.mkdir()
    try:
        create_symlink(source, target, quiet=True)
        delete_symlink(source, quiet=True)
    finally:
        if target.exists():
            target.rmdir()
    print_success()


def rename_folder(
    source: WindowsPath, target: WindowsPath, dry_run: bool = False
) -> None:
    print_(f"Renaming {style_path(source)} to {style_path(target)}", end="")
    if dry_run:
        print_skipped()
        return

    try:
        source.rename(target)
    except PermissionError as e:
        raise ClickException(
            f"Unable to rename {source} to {target}. Is an application locking the folder open?"
        ) from e
    print_success()


def create_symlink(
    source: WindowsPath, target: WindowsPath, quiet: bool = False, dry_run: bool = False
) -> None:
    if not quiet:
        print_(
            f"Making symlink from {style_path(source)} to {style_path(target)}",
            end="",
        )
    if dry_run:
        print_skipped()
        return

    if not target.exists():
        raise ClickException(f"{target} does not exist")
    try:
        source.symlink_to(target, target_is_directory=True)
    except FileExistsError as e:
        raise ClickException(f"{source} already exists") from e
    except OSError as e:
        raise ClickException(
            "Permission denied when creating symlink. Run Command Prompt as Administrator or enable Windows Developer Mode."
        ) from e
    if not quiet:
        print_success()


def delete_symlink(
    path: WindowsPath, quiet: bool = False, dry_run: bool = False
) -> None:
    if not quiet:
        print_(f"Deleting symlink {style_path(path)}", end="")
    if not path.is_symlink():
        raise ClickException(f"{path} is not a symlink")
    if dry_run and not quiet:
        print_skipped()
    if dry_run:
        return

    path.unlink()
    if not quiet:
        print_success()


def delete_folder(path: WindowsPath, dry_run: bool = False) -> None:
    print_(f"Deleting folder {style_path(path)}", end="")
    if path.is_symlink():
        raise ClickException(f"Cannot delete. {path} is a symlink.")
    if dry_run:
        print_skipped()
        return

    shutil.rmtree(path)
    print_success()


def add_folder_actions(folder: Folder, library: FolderLibrary, dry_run: bool) -> None:
    """Filesystem actions for `add` command"""
    target_dir = folder.get_target_dir(library.library_folder)

    print_("\n[bold]Pre-flight checks[/bold]")
    test_dir_creation(target_dir)
    temp_dir = folder.get_temp_dir()
    test_dir_creation(temp_dir)
    # Test symlink with sibling of source dir - it should have similar permissions
    test_symlink_creation(temp_dir, target_dir)
    # TODO: check that destination drive has enough space

    print_("\n[bold]Actions[/bold]")
    rename_folder(folder.source_dir, temp_dir, dry_run=dry_run)
    run_robocopy(temp_dir, target_dir, dry_run=dry_run)
    create_symlink(folder.source_dir, target_dir, dry_run=dry_run)
    delete_folder(temp_dir, dry_run=dry_run)


def remove_folder_actions(
    folder: Folder, library: FolderLibrary, dry_run: bool
) -> None:
    """Filesystem actions for `remove` command"""
    target_dir = folder.get_target_dir(library.library_folder)
    if not target_dir.exists():
        raise ClickException(f"{target_dir} does not exist")
        # TODO: how to handle? remove library entry?
    temp_dir = folder.get_temp_dir()

    print_("\n[bold]Pre-flight checks[/bold]")
    test_dir_creation(temp_dir)
    test_dir_creation(library.get_test_dir())
    # TODO: check that destination drive has enough space

    print_("\n[bold]Actions[/bold]")
    run_robocopy(target_dir, temp_dir, dry_run=dry_run)
    delete_symlink(folder.source_dir, dry_run=dry_run)
    rename_folder(temp_dir, folder.source_dir, dry_run=dry_run)
    delete_folder(target_dir, dry_run=dry_run)
