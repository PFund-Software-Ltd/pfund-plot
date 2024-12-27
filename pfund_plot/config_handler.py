import os
import shutil
from dataclasses import dataclass, asdict

import yaml

from pfund_plot.const.paths import (
    PROJ_NAME, 
    DATA_PATH,
    CACHE_PATH,
    CONFIG_PATH, 
    CONFIG_FILE_PATH
)


__all__ = [
    'get_config',
    'configure',
]


@dataclass
class ConfigHandler:
    data_path: str = str(DATA_PATH)
    cache_path: str = str(CACHE_PATH)
    
    _instance = None
    _verbose = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls.load()
        return cls._instance

    @classmethod
    def set_verbose(cls, verbose: bool):
        cls._verbose = verbose
    
    @classmethod
    def load(cls):
        '''Loads user's config file and returns a ConfigHandler object'''
        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Create default config from dataclass fields
        default_config = {
            field.name: field.default 
            for field in cls.__dataclass_fields__.values()
            if not field.name.startswith('_')  # Skip private fields
        }
        needs_update = False
        if CONFIG_FILE_PATH.is_file():
            with open(CONFIG_FILE_PATH, 'r') as f:
                saved_config = yaml.safe_load(f) or {}
                if cls._verbose:
                    print(f"{PROJ_NAME} config loaded from {CONFIG_FILE_PATH}.")
                # Check for new or removed fields
                new_fields = set(default_config.keys()) - set(saved_config.keys())
                removed_fields = set(saved_config.keys()) - set(default_config.keys())
                needs_update = bool(new_fields or removed_fields)
                
                if cls._verbose and needs_update:
                    if new_fields:
                        print(f"New config fields detected: {new_fields}")
                    if removed_fields:
                        print(f"Removed config fields detected: {removed_fields}")
                        
                # Filter out removed fields and merge with defaults
                saved_config = {k: v for k, v in saved_config.items() if k in default_config}
                config = {**default_config, **saved_config}
        else:
            config = default_config
            needs_update = True
        config_handler = cls(**config)
        if needs_update:
            config_handler.dump()
        return config_handler
    
    @classmethod
    def reset(cls):
        '''Resets the config by deleting the user config directory and reloading the config'''
        shutil.rmtree(CONFIG_PATH)
        if cls._verbose:
            print(f"{PROJ_NAME} config successfully reset.")
        return cls.load()
    
    def dump(self):
        with open(CONFIG_FILE_PATH, 'w') as f:
            yaml.dump(asdict(self), f, default_flow_style=False)
            if self._verbose:
                print(f"{PROJ_NAME} config saved to {CONFIG_FILE_PATH}.")
    
    def __post_init__(self):
        self._initialize_configs()
    
    def _initialize_configs(self):
        for path in [self.data_path, self.cache_path]:
            if not os.path.exists(path):
                os.makedirs(path)
                if self._verbose:
                    print(f'{PROJ_NAME} created {path}')
                

def configure(
    data_path: str | None = None,
    cache_path: str | None = None,
    verbose: bool = False,
    write: bool = False,
):
    '''Configures the global config object.
    It will override the existing config values from the existing config file or the default values.
    Args:
        write: If True, the config will be saved to the config file.
    '''
    NON_CONFIG_KEYS = ['verbose', 'write']
    config_updates = locals()
    for k in NON_CONFIG_KEYS:
        config_updates.pop(k)
    config_updates.pop('NON_CONFIG_KEYS')

    config = get_config(verbose=verbose)

    # Apply updates for non-None values
    for k, v in config_updates.items():
        if v is not None:
            setattr(config, k, v)
            
    if write:
        config.dump()
        
    config._initialize_configs()
    return config


def get_config(verbose: bool = False) -> ConfigHandler:
    ConfigHandler.set_verbose(verbose)
    return ConfigHandler.get_instance()
