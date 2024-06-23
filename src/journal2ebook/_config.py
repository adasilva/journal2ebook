import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from appdirs import user_config_dir

NAME: str = "journal2ebook"

CONFIG_FILE: str = "config.ini"

try:
    CONFIG_DIR = Path(user_config_dir(NAME))
except Exception:
    # Fallback to a directory in the user's home folder
    CONFIG_DIR = Path.home() / f".{NAME}"

print(f"Using config directory: {CONFIG_DIR}")

CONFIG_PATH = CONFIG_DIR / CONFIG_FILE

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
        self._config = CONFIG_DEFAULT.copy()  # Use a copy to avoid modifying the original

        print(f"Config file should be located at: {self._path}")
        print(f"Config directory exists: {os.path.exists(self._path.parent)}")
        print(f"Config file exists: {os.path.exists(self._path)}")

        self.load()

    def save(self):
        try:
            os.makedirs(self._path.parent, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as cfg:
                json.dump(self._config, cfg, indent=4, cls=JSONEncoder)
            print(f"Config saved successfully to {self._path}")
            print(f"Saved profiles: {[p.name for p in self._config['profiles']]}")
            print(f"Last profile index: {self._config['last_profile']}")
        except Exception as e:
            print(f"Error saving config to {self._path}: {str(e)}")

    def load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as cfg:
                loaded_config = json.load(cfg, object_hook=parse)
                self._config.update(loaded_config)  # Update instead of replace
            print(f"Config loaded successfully from {self._path}")
            print(f"Loaded profiles: {[p.name for p in self._config['profiles']]}")
            print(f"Last profile index: {self._config['last_profile']}")
        except FileNotFoundError:
            print(f"Config file not found at {self._path}. Using default configuration.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self._path}. Using default configuration.")
        except Exception as e:
            print(f"Error loading config from {self._path}: {str(e)}. Using default configuration.")

    def __getitem__(self, name: str) -> Any:
        return self._config.get(name)

    def __setitem__(self, name: str, value: Any):
        self._config[name] = value
        self.save()

# Initialize the config
config = Config()
