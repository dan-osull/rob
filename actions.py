from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import WindowsPath

import console as con
from filesystem import (
    DiskUsage,
    create_symlink,
    delete_folder,
    delete_symlink,
    get_dir_size,
    rename_folder,
    test_dir_creation,
    test_disk_space,
    test_set_ntfs_permisisons,
    test_symlink_creation,
)
from folders import Folder, Library
from robocopy import run_robocopy


@dataclass
class FolderActions(ABC):
    folder: Folder
    library: Library
    dry_run: bool
    dont_copy_permissions: bool

    from_dir: WindowsPath = field(init=False)
    to_dir: WindowsPath = field(init=False)
    dir_size_bytes: int = field(init=False)

    @abstractmethod
    def preflight_checks(self) -> None:
        con.print_("\n[bold]Pre-flight checks[/bold]")

    @abstractmethod
    def actions(self) -> None:
        con.print_("\n[bold]Actions[/bold]")

    def confirm(self) -> None:
        con.print_(f"Folder size: {con.style_bytes_as_gb(self.dir_size_bytes)}")
        con.confirm_action(self.dry_run)

    def run(self) -> None:
        self.confirm()
        self.preflight_checks()
        self.actions()


@dataclass
class AddFolderActions(FolderActions):
    """
    Filesystem actions for `add` command

    Move data from `folder.source_dir` to `folder.get_library_subdir()`
    """

    def __post_init__(self):
        self.from_dir = self.folder.source_dir
        self.to_dir = self.folder.get_library_subdir(self.library)
        self.dir_size_bytes = get_dir_size(self.from_dir)

    def preflight_checks(self) -> None:
        super().preflight_checks()
        test_dir_creation(self.to_dir)
        test_dir_creation(self.folder.get_temp_dir())
        # Test symlink with sibling of source dir - it should have similar permissions
        test_symlink_creation(self.folder.get_temp_dir(), self.to_dir)
        test_disk_space(self.dir_size_bytes, DiskUsage(self.to_dir.drive))
        if not self.dont_copy_permissions:
            # Use empty source directory to test permissions
            test_set_ntfs_permisisons(self.folder.get_temp_dir(), self.to_dir)

    def actions(self) -> None:
        super().actions()
        rename_folder(self.from_dir, self.folder.get_temp_dir(), dry_run=self.dry_run)
        run_robocopy(
            self.folder.get_temp_dir(),
            self.to_dir,
            self.dir_size_bytes,
            dry_run=self.dry_run,
            copy_permissions=not self.dont_copy_permissions,
        )
        create_symlink(self.from_dir, self.to_dir, dry_run=self.dry_run)
        delete_folder(self.folder.get_temp_dir(), dry_run=self.dry_run)


@dataclass
class RemoveFolderActions(FolderActions):
    """
    Filesystem actions for `remove` command

    Move data from `folder.get_library_subdir()` to `folder.source_dir`
    """

    def __post_init__(self):
        self.from_dir = self.folder.get_library_subdir(self.library)
        self.to_dir = self.folder.source_dir
        self.dir_size_bytes = get_dir_size(self.from_dir)

    def preflight_checks(self) -> None:
        super().preflight_checks()
        # Sibling of source dir
        test_dir_creation(self.folder.get_temp_dir())
        # Subdir of library
        test_dir_creation(self.library.get_test_dir())
        test_disk_space(self.dir_size_bytes, DiskUsage(self.to_dir.drive))
        if not self.dont_copy_permissions:
            # Use empty source directory to test permissions
            test_set_ntfs_permisisons(
                self.library.get_test_dir(), self.folder.get_temp_dir()
            )

    def actions(self) -> None:
        super().actions()
        run_robocopy(
            self.from_dir,
            self.folder.get_temp_dir(),
            self.dir_size_bytes,
            dry_run=self.dry_run,
            copy_permissions=not self.dont_copy_permissions,
        )
        delete_symlink(self.to_dir, dry_run=self.dry_run)
        rename_folder(self.folder.get_temp_dir(), self.to_dir, dry_run=self.dry_run)
        delete_folder(self.from_dir, dry_run=self.dry_run)
