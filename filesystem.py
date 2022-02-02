import os
import shutil
from dataclasses import dataclass
from pathlib import WindowsPath

from click import ClickException

import console as con
from folders import Folder, Library
from robocopy import run_robocopy


@dataclass
class DiskUsage:
    drive: str
    "Accepts `Path().drive`"
    usage: shutil._ntuple_diskusage
    """
    _ntuple_diskusage.total.__doc__ = 'Total space in bytes' \n
    _ntuple_diskusage.used.__doc__ = 'Used space in bytes' \n
    _ntuple_diskusage.free.__doc__ = 'Free space in bytes'
    """

    def __init__(self, drive: str):
        self.drive = drive
        self.usage = shutil.disk_usage(drive)


def get_dir_size(path: WindowsPath) -> int:
    """Return total size of files in given path and subdirs."""
    if not path.exists():
        # Avoid race with file creation
        return 0

    def get_tree_size(path) -> int:
        # https://www.python.org/dev/peps/pep-0471/
        total = 0
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                total += get_tree_size(entry.path)
            else:
                total += entry.stat(follow_symlinks=False).st_size
        return total

    return get_tree_size(path)


def test_disk_space(dir_size_bytes, target_disk: DiskUsage) -> None:
    con.print_(
        f"Testing free space in drive {con.style_path(target_disk.drive)}", end=""
    )
    if dir_size_bytes > target_disk.usage.free:
        raise ClickException(f"Drive {target_disk.drive} does have enough free space")
    con.print_success()


def test_dir_creation(path: WindowsPath) -> None:
    """Test write access by creating and deleting an empty folder"""
    con.print_(f"Testing write access to {con.style_path(path)}", end="")
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
    con.print_success()


def test_set_ntfs_permisisons(source: WindowsPath, target: WindowsPath) -> None:
    con.print_(
        f"Testing access to copy permissions from {con.style_path(source)} to {con.style_path(target)}",
        end="",
    )
    try:
        source.mkdir()
        run_robocopy(source, target, copy_permissions=True, quiet=True)
    except ClickException as e:
        if "Copying NTFS Security to Destination Directory" in e.message:
            raise ClickException(
                "Unable to set permissions. Do you need to run Command Prompt as Administrator?"
            ) from e
        raise e
    finally:
        source.rmdir()
        target.rmdir()
    con.print_success()


def test_symlink_creation(source: WindowsPath, target: WindowsPath) -> None:
    con.print_(
        f"Testing symlink creation from {con.style_path(source)} to {con.style_path(target)}",
        end="",
    )
    target.mkdir()
    try:
        create_symlink(source, target, quiet=True)
        delete_symlink(source, quiet=True)
    finally:
        if target.exists():
            target.rmdir()
    con.print_success()


def rename_folder(
    source: WindowsPath, target: WindowsPath, dry_run: bool = False
) -> None:
    con.print_(f"Renaming {con.style_path(source)} to {con.style_path(target)}", end="")
    if dry_run:
        con.print_skipped()
        return

    try:
        source.rename(target)
    except PermissionError as e:
        raise ClickException(
            f"Unable to rename {source} to {target}. Is an application locking the folder open?"
        ) from e
    con.print_success()


def create_symlink(
    source: WindowsPath, target: WindowsPath, quiet: bool = False, dry_run: bool = False
) -> None:
    if not quiet:
        con.print_(
            f"Making symlink from {con.style_path(source)} to {con.style_path(target)}",
            end="",
        )
    if dry_run:
        con.print_skipped()
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
        con.print_success()


def delete_symlink(
    path: WindowsPath, quiet: bool = False, dry_run: bool = False
) -> None:
    if not quiet:
        con.print_(f"Deleting symlink {con.style_path(path)}", end="")
    if not path.is_symlink():
        raise ClickException(f"{path} is not a symlink")
    if dry_run and not quiet:
        con.print_skipped()
    if dry_run:
        return

    path.unlink()
    if not quiet:
        con.print_success()


def delete_folder(path: WindowsPath, dry_run: bool = False) -> None:
    con.print_(f"Deleting folder {con.style_path(path)}", end="")
    if path.is_symlink():
        raise ClickException(f"Cannot delete. {path} is a symlink.")
    if dry_run:
        con.print_skipped()
        return
    try:
        shutil.rmtree(path)
    except PermissionError:
        # Rarely, it might not be possible to delete a folder, even if earlier (folder renaming) checks pass.
        # The example I've seen of this is an Explorer extension DLL that's still loaded.
        # TODO: could be avoided by checking open file handles pre-flight?
        # Not throwing exception, as this is a tidy up action, and we should still update DB.
        con.print_fail()
        con.print_(
            "[red]Unable to delete {path}, probably because an application is locking it open.[/red]"
        )
        con.print_(
            "[red]To tidy up, restart your PC and delete this folder manually.[/red]"
        )
    con.print_success()


def add_folder_actions(
    folder: Folder, library: Library, dry_run: bool, dont_copy_permissions: bool
) -> None:
    """
    Filesystem actions for `add` command

    Move data from `folder.source_dir` to `folder.get_target_dir()`
    """
    from_dir = folder.source_dir
    to_dir = folder.get_library_subdir(library)
    temp_dir = folder.get_temp_dir()
    dir_size_bytes = get_dir_size(from_dir)

    con.print_("\n[bold]Pre-flight checks[/bold]")
    test_dir_creation(to_dir)
    test_dir_creation(temp_dir)
    # Test symlink with sibling of source dir - it should have similar permissions
    test_symlink_creation(temp_dir, to_dir)
    test_disk_space(dir_size_bytes, DiskUsage(to_dir.drive))
    if not dont_copy_permissions:
        # Use empty source directory to test permissions
        test_set_ntfs_permisisons(temp_dir, to_dir)

    con.print_("\n[bold]Actions[/bold]")
    rename_folder(from_dir, temp_dir, dry_run=dry_run)
    run_robocopy(
        temp_dir,
        to_dir,
        dir_size_bytes,
        dry_run=dry_run,
        copy_permissions=not dont_copy_permissions,
    )
    create_symlink(from_dir, to_dir, dry_run=dry_run)
    delete_folder(temp_dir, dry_run=dry_run)


def remove_folder_actions(folder: Folder, library: Library, dry_run: bool) -> None:
    """
    Filesystem actions for `remove` command

    Move data from `folder.get_target_dir()` to `folder.source_dir`
    """
    from_dir = folder.get_library_subdir(library)
    to_dir = folder.source_dir
    temp_dir = folder.get_temp_dir()
    dir_size_bytes = get_dir_size(from_dir)

    con.print_("\n[bold]Pre-flight checks[/bold]")
    # Sibling of source dir
    test_dir_creation(temp_dir)
    # Subdir of library
    test_dir_creation(library.get_test_dir())
    test_disk_space(dir_size_bytes, DiskUsage(to_dir.drive))

    con.print_("\n[bold]Actions[/bold]")
    run_robocopy(from_dir, temp_dir, dir_size_bytes, dry_run=dry_run)
    delete_symlink(to_dir, dry_run=dry_run)
    rename_folder(temp_dir, to_dir, dry_run=dry_run)
    delete_folder(from_dir, dry_run=dry_run)
