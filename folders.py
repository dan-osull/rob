from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import WindowsPath
from typing import ClassVar, Optional

import console as con
import filesystem
from constants import PROJECT_NAME


@dataclass
class Folder:
    """A folder being managed by the tool. It is identifed by `source_dir`."""

    source_dir: WindowsPath
    """The path of the folder on the source disk. It gets replaced by a symlink."""

    def __post_init__(self):
        self.source_dir = WindowsPath(self.source_dir)

    def get_library_subdir(self, library: Library) -> WindowsPath:
        """A subfolder of the library. It is the target for data."""
        return library.library_folder.joinpath(self.short_name).resolve()

    def get_temp_dir(self) -> WindowsPath:
        """A sibling of the source. It is used for shuffling data and testing access."""
        temp_dir_name = f"_{PROJECT_NAME}_temp_{self.short_name}"
        return self.source_dir.parent.joinpath(temp_dir_name).resolve()

    def get_library_data_size(self, library) -> int:
        return filesystem.get_dir_size(self.get_library_subdir(library))

    @property
    def short_name(self) -> str:
        """A new name for the folder that includes a hash of its path"""
        # e.g. Git(6079d94ba840)
        return f"{self.source_dir.name}({self._source_dir_hash})"

    @property
    def _source_dir_hash(self) -> str:
        # lower() so paths get same hash regardless of capitalisation
        return sha256(str(self.source_dir).lower().encode("utf-8")).hexdigest()[:12]

    def get_table_data(self, library: Library, show_size: bool = False) -> dict:
        result = {"Path": self.source_dir, "Name": self.short_name}
        if show_size:
            result["Size"] = con.style_bytes_as_gb(self.get_library_data_size(library))
        return result


@dataclass
class Library:
    """The library is a folder that contains target data folders and a config file"""

    config_filename: ClassVar = f"{PROJECT_NAME}-folders.json"
    library_folder: WindowsPath
    config_path: WindowsPath
    folders: list[Folder]

    def __init__(self, library_folder: WindowsPath):
        self.library_folder = library_folder
        self.config_path = library_folder.joinpath(self.config_filename).resolve()

        self.folders = []
        if self.config_path.exists():
            con.print_(
                f"[grey50]Loading folder list from {self.config_path}...[/grey50]"
            )
            with open(self.config_path, encoding="utf8") as file:
                self.folders = [Folder(source_dir=item) for item in json.load(file)]

    def add_folder(self, folder: Folder) -> None:
        if folder not in self.folders:
            self.folders.append(folder)

    def remove_folder(self, folder: Folder) -> None:
        if folder in self.folders:
            self.folders.remove(folder)

    @property
    def source_dirs(self) -> list[WindowsPath]:
        return [folder.source_dir for folder in self.folders]

    @property
    def disk_usage(self) -> list[filesystem.DiskUsage]:
        """Usage for disk containing library and any source disks"""
        paths = [self.library_folder] + self.source_dirs
        drives = sorted({path.drive for path in paths})
        return [filesystem.DiskUsage(drive) for drive in drives]

    def find_folder(self, search_term: str) -> Optional[Folder]:
        """Search library using `source_dir` and `target_dir_name` fields"""
        match = next(
            (x for x in self.folders if x.source_dir == WindowsPath(search_term)), None
        )
        if match:
            return match
        return next((x for x in self.folders if x.short_name == search_term), None)

    def get_table_data(self, show_size: bool = False) -> list[dict]:
        return [item.get_table_data(self, show_size=show_size) for item in self.folders]

    def get_test_dir(self) -> WindowsPath:
        """Directory in library for testing write access"""
        return self.library_folder.joinpath(f"_{PROJECT_NAME}_test").resolve()

    def save(self) -> None:
        if self.folders:
            con.print_(
                f"Saving folder list to {con.style_path(self.config_path)}", end=""
            )
            with open(self.config_path, "w", encoding="utf8") as file:
                file.write(json.dumps([str(item.source_dir) for item in self.folders]))
            con.print_success()
