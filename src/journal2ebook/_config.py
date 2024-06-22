import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from appdirs import user_config_dir

NAME: str = "journal2ebook"

CONFIG_FILE: str = "config.ini"
CONFIG_DIR: Path = Path(user_config_dir(NAME))
CONFIG_PATH: Path = CONFIG_DIR / CONFIG_FILE


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

    def __str__(self) -> str:
        return self.name


def parse(dct: dict[str, Any]) -> Path | Profile | dict[str, Any]:
    if "__path__" in dct:
        return Path(dct["path"])

    if "__dataclass__" in dct:
        _ = dct.pop("__dataclass__")
        return Profile(**dct)
    return dct


class JSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:  # noqa: ANN401
        if isinstance(obj, Path):
            return {"__path__": True, "path": str(obj)}

        if isinstance(obj, Profile):
            ret = asdict(obj)
            ret["__dataclass__"] = True
            return ret

        return super().default(obj)


CONFIG_DEFAULT = {
    "last_dir": Path("~"),
    "last_profile": 0,
    "profiles": [Profile("Default")],
    "k2pdfopt_path": None,
}


class Config:
    def __init__(self) -> None:
        self._path = CONFIG_PATH
        self._config = CONFIG_DEFAULT

        self.load()

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        with self._path.open("w", encoding="utf-8") as cfg:
            json.dump(self._config, cfg, indent=4, cls=JSONEncoder)

    def load(self) -> None:
        try:
            with self._path.open("r", encoding="utf-8") as cfg:
                self._config = json.load(cfg, object_hook=parse)
        except FileNotFoundError:
            return

    def __getitem__(self, name: str) -> Any:  # noqa: ANN401
        if name in self._config:
            return self._config[name]

        return None

    def __setitem__(self, name: str, value: Any) -> None:  # noqa: ANN401
        self._config[name] = value
        self.save()
