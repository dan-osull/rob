from hashlib import sha256
from pathlib import WindowsPath
from typing import ClassVar, Optional

from pydantic import BaseModel


class Folder(BaseModel):
    """
    A folder being managed by the tool
    """

    field_names: ClassVar = ["source_dir", "target_dir_name"]

    source_dir: WindowsPath
    "The path of the folder on the source disk"

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


class FolderList(BaseModel):
    # Apparently this is the "Pydantic" way of storing a list of objects
    # https://pydantic-docs.helpmanual.io/usage/models/#custom-root-types
    __root__: list[Folder] = []
    json_filename: str = "folders.json"

    @property
    def folders(self) -> list[Folder]:
        return self.__root__

    @property
    def source_dirs(self) -> list[WindowsPath]:
        return [folder.source_dir for folder in self.folders]

    def get_folder_by_path(self, path: WindowsPath) -> Optional[Folder]:
        return next((x for x in self.folders if x.source_dir == path), None)

    def add_folder(self, folder: Folder):
        self.folders.append(folder)

    def remove_folder(self, folder: Folder):
        self.folders.remove(folder)

    def get_table_data(self) -> list[dict]:
        return [item.get_table_data() for item in self.folders]

    def save_json(self, json_filename=json_filename) -> None:
        json = self.json()
        with open(json_filename, "w") as file:
            file.write(json)


def get_folder_list(json_filename=FolderList.json_filename) -> FolderList:
    """
    Load FolderList from JSON file
    """
    json_path = WindowsPath(json_filename)
    if json_path.exists():
        return FolderList.parse_file(json_path)
    else:
        return FolderList()
