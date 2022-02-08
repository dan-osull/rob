import os
import shutil
from dataclasses import dataclass
from pathlib import WindowsPath

from click import ClickException

import rob.console as con
from rob.robocopy import run_robocopy


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
    """Return total size of files in given path and subdirs"""
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
        raise ClickException(f"\nDrive {target_disk.drive} does have enough free space")
    con.print_success()


def test_dir_creation(path: WindowsPath) -> None:
    """Test write access by creating and deleting an empty folder"""
    con.print_(f"Testing write access to {con.style_path(path)}", end="")
    if path.exists():
        raise ClickException(f"\n{path} already exists")
    try:
        path.mkdir()
    except PermissionError as e:
        raise ClickException(
            f"\nCould not create {path}. Do you need to run Command Prompt as Administrator?"
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
        if (
            "Copying NTFS Security to Destination Directory" in e.message
            or "You do not have the Manage Auditing user right" in e.message
        ):
            raise ClickException(
                "\nUnable to set permissions. Do you need to run Command Prompt as Administrator?"
            ) from e
        raise e
    finally:
        if source.exists():
            source.rmdir()
        if target.exists():
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
            f"\nUnable to rename {source} to {target}. Is an application locking the folder open?"
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
        raise ClickException(f"\n{target} does not exist")
    try:
        source.symlink_to(target, target_is_directory=True)
    except FileExistsError as e:
        raise ClickException(f"\n{source} already exists") from e
    except OSError as e:
        raise ClickException(
            "\nPermission denied when creating symlink. Run Command Prompt as Administrator or enable Windows Developer Mode."
        ) from e
    if not quiet:
        con.print_success()


def delete_symlink(
    path: WindowsPath, quiet: bool = False, dry_run: bool = False
) -> None:
    if not quiet:
        con.print_(f"Deleting symlink {con.style_path(path)}", end="")
    if not path.is_symlink():
        raise ClickException(f"\n{path} is not a symlink")
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
        raise ClickException(f"\nCannot delete. {path} is a symlink.")
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
