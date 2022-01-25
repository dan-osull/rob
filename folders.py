from pydantic import BaseModel
from pathlib import WindowsPath
from hashlib import sha256


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

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]

    @property
    def source_dirs(self) -> list[WindowsPath]:
        return [folder.source_dir for folder in list(self)]
