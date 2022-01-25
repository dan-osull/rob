from pydantic import BaseModel
from pathlib import WindowsPath
from hashlib import sha256
from typing import Optional
from config import JSON_FILENAME


class Folder(BaseModel):
    source_dir: WindowsPath

    @property
    def source_dir_hash(self) -> str:
        # e.g. str(self.source_dir) == 'C:\\Temp'
        return sha256(str(self.source_dir).encode("utf-8")).hexdigest()[:12]

    @property
    def destination_dir_name(self) -> str:
        # e.g. Temp(3a301fe2caf3)
        return f"{self.source_dir.name}({self.source_dir_hash})"


class FolderList(BaseModel):
    # Apparently this is the "Pydantic" way of storing a list of objects
    # https://pydantic-docs.helpmanual.io/usage/models/#custom-root-types
    __root__: list[Folder]

    @property
    def source_dirs(self) -> list[WindowsPath]:
        return [folder.source_dir for folder in self.__root__]

    def get_folder_by_path(self, path: WindowsPath) -> Optional[Folder]:
        return next((x for x in self.__root__ if x.source_dir == path), None)

    def add_folder(self, folder: Folder):
        self.__root__.append(folder)

    def remove_folder(self, folder: Folder):
        self.__root__.remove(folder)


def save_json(folder_list: FolderList, filename=JSON_FILENAME) -> None:
    json = folder_list.json()
    with open(filename, "w") as file:
        file.write(json)


def load_json(filename=JSON_FILENAME) -> FolderList:
    return FolderList.parse_file(filename)
