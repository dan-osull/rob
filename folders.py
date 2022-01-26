import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import WindowsPath
from typing import ClassVar, Optional, Union


@dataclass
class Folder:
    """
    A folder being managed by the tool
    """

    field_names: ClassVar = ["source_dir", "target_dir_name"]
    source_dir: WindowsPath
    "The path of the folder on the source disk"

    def __init__(self, source_dir: Union[WindowsPath, str]):
        self.source_dir = WindowsPath(source_dir)

    @property
    def target_dir_name(self) -> str:
        "A new name for the folder that includes a hash of its path"
        # e.g. Git(6079d94ba840)
        return f"{self.source_dir.name}({self._source_dir_hash})"

    @property
    def temp_dir_name(self) -> str:
        return f"_temp_{self.target_dir_name}"

    @property
    def _source_dir_hash(self) -> str:
        # lower() so paths get same hash regardless of capitalisation
        return sha256(str(self.source_dir).lower().encode("utf-8")).hexdigest()[:12]

    def get_table_data(self) -> dict:
        return {field: getattr(self, field) for field in self.field_names}


@dataclass
class FolderLibrary:
    config_filename: ClassVar = "symbox-folders.json"
    config_path: WindowsPath
    folders: list[Folder]

    def __init__(self, library_folder: Optional[WindowsPath] = None) -> None:
        if not library_folder:
            # Defaults to current folder (".")
            library_folder = WindowsPath()
        self.config_path = library_folder.joinpath(self.config_filename).resolve()

        self.folders = []
        if self.config_path.exists():
            with open(self.config_path) as file:
                self.folders = [Folder(source_dir=item) for item in json.load(file)]

    @property
    def library_folder(self) -> WindowsPath:
        "Library is folder that contains config file"
        return self.config_path.parent

    @property
    def source_dirs(self) -> list[WindowsPath]:
        return [folder.source_dir for folder in self.folders]

    def get_folder_by_path(self, path: WindowsPath) -> Optional[Folder]:
        return next((x for x in self.folders if x.source_dir == path), None)

    def get_table_data(self) -> list[dict]:
        return [item.get_table_data() for item in self.folders]

    def save(self) -> None:
        with open(self.config_path, "w") as file:
            file.write(json.dumps([str(item.source_dir) for item in self.folders]))
