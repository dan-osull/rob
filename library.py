import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import WindowsPath
from typing import ClassVar, Optional, Union

from config import PROJECT_NAME


@dataclass
class Folder:
    """A folder being managed by the tool"""

    source_dir: WindowsPath
    """The path of the folder on the source disk. It becomes replaced by a symlink."""

    def __init__(self, source_dir: Union[WindowsPath, str]):
        self.source_dir = WindowsPath(source_dir)

    @property
    def target_dir_name(self) -> str:
        """A new name for the folder that includes a hash of its path"""
        # e.g. Git(6079d94ba840)
        return f"{self.source_dir.name}({self._source_dir_hash})"

    def get_target_dir(self, library_folder: WindowsPath) -> WindowsPath:
        """Target dir is subfolder of library. It is the destination for data."""
        return library_folder.joinpath(self.target_dir_name).resolve()

    @property
    def temp_dir_name(self) -> str:
        return f"_{PROJECT_NAME}_temp_{self.target_dir_name}"

    def get_temp_dir(self) -> WindowsPath:
        """Temp dir is a sibling of the source. It is used for shuffling data."""
        return self.source_dir.parent.joinpath(self.temp_dir_name).resolve()

    @property
    def _source_dir_hash(self) -> str:
        # lower() so paths get same hash regardless of capitalisation
        return sha256(str(self.source_dir).lower().encode("utf-8")).hexdigest()[:12]

    def get_table_data(self) -> dict:
        return {"Path": self.source_dir, "Name": self.target_dir_name}


@dataclass
class FolderLibrary:
    config_filename: ClassVar = f"{PROJECT_NAME}-folders.json"
    library_folder: WindowsPath
    """The library is the folder that contains the config file"""
    config_path: WindowsPath
    folders: list[Folder]

    def __init__(self, library_folder: WindowsPath):
        self.library_folder = library_folder
        self.config_path = library_folder.joinpath(self.config_filename).resolve()

        self.folders = []
        if self.config_path.exists():
            with open(self.config_path, encoding="utf8") as file:
                self.folders = [Folder(source_dir=item) for item in json.load(file)]

    @property
    def source_dirs(self) -> list[WindowsPath]:
        return [folder.source_dir for folder in self.folders]

    def find_folder(self, search_term: str) -> Optional[Folder]:
        """Search library using `source_dir` and `target_dir_name` fields"""
        match = next(
            (x for x in self.folders if x.source_dir == WindowsPath(search_term)), None
        )
        if match:
            return match
        return next((x for x in self.folders if x.target_dir_name == search_term), None)

    def get_table_data(self) -> list[dict]:
        return [item.get_table_data() for item in self.folders]

    def get_temp_dir(self) -> WindowsPath:
        """Temporary directory in library for testing write access"""
        return self.library_folder.joinpath(f"_{PROJECT_NAME}_temp_").resolve()

    def save(self) -> None:
        with open(self.config_path, "w", encoding="utf8") as file:
            file.write(json.dumps([str(item.source_dir) for item in self.folders]))
