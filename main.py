from pathlib import WindowsPath, Path
from pydantic import BaseModel
from hashlib import sha256
import click

JSON_FILENAME = "folders.json"


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
    # https://pydantic-docs.helpmanual.io/usage/models/#custom-root-types
    __root__: list[Folder]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


def save_json(folder_list: FolderList, filename=JSON_FILENAME) -> None:
    json = folder_list.json()
    with open(filename, "w") as file:
        file.write(json)


def load_json(filename=JSON_FILENAME) -> FolderList:
    return FolderList.parse_file(filename)


def main():
    managed_folders = [
        Folder(source_dir=Path("C:\Temp")),
        Folder(source_dir=Path("C:\Windows")),
    ]
    managed_folders = FolderList.parse_obj(managed_folders)
    save_json(managed_folders)
    loaded_folders = load_json()


if __name__ == "__main__":
    main()
