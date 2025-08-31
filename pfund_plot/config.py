from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, asdict, field, MISSING

from pfund.utils.utils import load_yaml_file, dump_yaml_file
from pfund_plot.const.paths import (
    PROJ_NAME, 
    MAIN_PATH,
    DATA_PATH,
    CACHE_PATH,
    CONFIG_FILE_PATH
)


__all__ = [
    'get_config',
    'configure',
]


@dataclass
class Configuration:
    data_path: str = str(DATA_PATH)
    cache_path: str = str(CACHE_PATH)
    static_dirs: dict[str, str] = field(default_factory=dict)
    
    _instance = None
    _verbose = False
    
    # REVIEW: this won't be needed if we use pydantic.BaseModel instead of dataclass
    def _enforce_types(self):
        config_dict = asdict(self)
        for k, v in config_dict.items():
            _field = self.__dataclass_fields__[k]
            if _field.type == 'Path' and isinstance(v, str):
                setattr(self, k, Path(v))

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._load_env_file()
            cls._instance = cls.load()
        return cls._instance

    @classmethod
    def set_verbose(cls, verbose: bool):
        cls._verbose = verbose
    
    @classmethod   
    def _load_env_file(cls):
        from dotenv import find_dotenv, load_dotenv
        env_file_path = find_dotenv(usecwd=True, raise_error_if_not_found=False)
        if env_file_path:
            load_dotenv(env_file_path, override=True)
            if cls._verbose:
                print(f'{PROJ_NAME} .env file loaded from {env_file_path}')
        else:
            if cls._verbose:
                print(f'{PROJ_NAME} .env file is not found')
    
    @classmethod
    def load(cls) -> Configuration:
        '''Loads user's config file and returns a Configuration object'''
        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Create default config from dataclass fields
        default_config = {}
        for _field in cls.__dataclass_fields__.values():
            if _field.name.startswith('_'):  # Skip private fields
                continue
            if _field.default_factory is not MISSING:
                default_config[_field.name] = _field.default_factory()
            else:
                default_config[_field.name] = _field.default
        needs_update = False
        if CONFIG_FILE_PATH.is_file():
            current_config = load_yaml_file(CONFIG_FILE_PATH) or {}
            if cls._verbose:
                print(f"Loaded {CONFIG_FILE_PATH}")
            # Check for new or removed fields
            new_fields = set(default_config.keys()) - set(current_config.keys())
            removed_fields = set(current_config.keys()) - set(default_config.keys())
            needs_update = bool(new_fields or removed_fields)
            
            if cls._verbose and needs_update:
                if new_fields:
                    print(f"New config fields detected: {new_fields}")
                if removed_fields:
                    print(f"Removed config fields detected: {removed_fields}")
                    
            # Filter out removed fields and merge with defaults
            current_config = {k: v for k, v in current_config.items() if k in default_config}
            config = {**default_config, **current_config}
        else:
            config = default_config
            needs_update = True
        config = cls(**config)
        if needs_update:
            config.dump()
        return config
    
    def dump(self):
        dump_yaml_file(CONFIG_FILE_PATH, asdict(self))
        if self._verbose:
            print(f"Created {CONFIG_FILE_PATH}")
    
    @property
    def file_path(self):
        return CONFIG_FILE_PATH
    
    def __post_init__(self):
        self._initialize()
    
    def _initialize(self):
        self._enforce_types()
        self._initialize_static_dirs()
        self._initialize_file_paths()
        
    def _initialize_static_dirs(self):
        if 'assets' not in self.static_dirs:
            self.static_dirs['assets'] = str((Path(MAIN_PATH) / "ui" / "static"))
        
    def _initialize_file_paths(self):
        for path in [self.data_path, self.cache_path]:
            if not os.path.exists(path):
                os.makedirs(path)
                if self._verbose:
                    print(f'{PROJ_NAME} created {path}')
                

def configure(
    data_path: str | None = None,
    cache_path: str | None = None,
    static_dirs: dict[str, str] | None = None,
    verbose: bool = False,
    write: bool = False,
):
    '''Configures the global config object.
    It will override the existing config values from the existing config file or the default values.
    Args:
        static_dirs: a dict of static directories to be used in pn.serve(static_dirs=...)
        write: If True, the config will be saved to the config file.
    '''
    NON_CONFIG_KEYS = ['verbose', 'write']
    config_updates = locals()
    for k in NON_CONFIG_KEYS:
        config_updates.pop(k)
    config_updates.pop('NON_CONFIG_KEYS')

    static_dirs = static_dirs or {}
    assert 'assets' not in static_dirs, "'assets' is a reserved key in static_dirs"

    Configuration.set_verbose(verbose)
    config = get_config()

    # Apply updates for non-None values
    for k, v in config_updates.items():
        if v is not None:
            setattr(config, k, v)
            
    if write:
        config.dump()
        
    config._initialize()
    return config


def get_config() -> Configuration:
    return Configuration.get_instance()
