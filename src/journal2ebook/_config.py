import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from appdirs import user_config_dir

NAME: str = "journal2ebook"

CONFIG_FILE: str = "config.ini"
CONFIG_DIR: Path = Path(user_config_dir(NAME))
CONFIG_PATH: Path = CONFIG_DIR / CONFIG_FILE


def parse(dct: dict[str, Any]) -> Any:
    if "__path__" in dct:
        return Path(dct["path"])
    elif "__dataclass__" in dct:
        _ = dct.pop("__dataclass__")
        return Profile(**dct)
    return dct


class JSONEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        if isinstance(obj, Path):
            return {"__path__": True, "path": str(obj)}
        elif isinstance(obj, Profile):
            ret = asdict(obj)
            ret["__dataclass__"] = True
            return ret
        return super().default(obj)


@dataclass
class Profile:
    name: str
    skip_first_page: bool = False
    many_cols: bool = False
    color: bool = False
    leftmargin: float = 0.0
    rightmargin: float = 1.0
    topmargin: float = 0.0
    bottommargin: float = 1.0

    def __str__(self):
        return self.name


CONFIG_DEFAULT = {
    "last_dir": Path("~"),
    "last_profile": 0,
    "profiles": [Profile("Default")],
    "k2pdfopt_path": None,
}


class Config:
    def __init__(self):
        self._path = CONFIG_PATH
        self._config = CONFIG_DEFAULT

        self.load()

    def save(self):
        try:
            os.makedirs(self._path.parent)
        except FileExistsError:
            pass

        with open(self._path, "w", encoding="utf-8") as cfg:
            json.dump(self._config, cfg, indent=4, cls=JSONEncoder)

    def load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as cfg:
                self._config = json.load(cfg, object_hook=parse)
        except FileNotFoundError:
            return

    def __getitem__(self, name: str) -> Any:
        if name in self._config:
            return self._config[name]

        return None

    def __setitem__(self, name: str, value: Any):
        self._config[name] = value
        self.save()
