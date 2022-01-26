import json
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import WindowsPath
from typing import ClassVar, Optional


@dataclass
class Folder:
    """
    A folder being managed by the tool
    """

    field_names: ClassVar = ["source_dir", "target_dir_name"]
    source_dir: WindowsPath
    "The path of the folder on the source disk"

    def __init__(self, source_dir):
        self.source_dir = WindowsPath(source_dir)

    @property
    def target_dir_name(self) -> str:
        "A new name for the folder that includes a hash of its path"
        # e.g. Temp(3a301fe2caf3)
        return f"{self.source_dir.name}({self._source_dir_hash})"

    @property
    def _source_dir_hash(self) -> str:
        # lower() so paths get same hash regardless of capitalisation
        return sha256(str(self.source_dir).lower().encode("utf-8")).hexdigest()[:12]

    def get_table_data(self) -> dict:
        return {field: getattr(self, field) for field in self.field_names}


@dataclass
class FolderList:
    config_filename: str = "symbox-folders.json"
    folders: list[Folder] = field(default_factory=list)

    def __post_init__(self):
        config_path = WindowsPath(self.config_filename)
        if config_path.exists():
            with open(config_path) as file:
                self.folders = [Folder(source_dir=item) for item in json.load(file)]

    @property
    def source_dirs(self) -> list[WindowsPath]:
        return [folder.source_dir for folder in self.folders]

    def get_folder_by_path(self, path: WindowsPath) -> Optional[Folder]:
        return next((x for x in self.folders if x.source_dir == path), None)

    def get_table_data(self) -> list[dict]:
        return [item.get_table_data() for item in self.folders]

    def save(self, config_filename=config_filename) -> None:
        with open(config_filename, "w") as file:
            file.write(json.dumps([str(item.source_dir) for item in self.folders]))
