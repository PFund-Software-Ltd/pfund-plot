from __future__ import annotations
from typing import Any, ClassVar

from pathlib import Path

import panel as pn

from pfund_kit.config import Configuration
from pfund_plot.enums import PanelTheme, PanelDesign


__all__ = [
    'get_config',
    'configure',
]


project_name = 'pfund_plot'
_config: PFundPlotConfig | None = None


def get_config() -> PFundPlotConfig:
    """Lazy singleton - only creates config when first called.
    Also loads the .env file.
    """
    global _config
    if _config is None:
        _config = PFundPlotConfig()
    return _config


def configure(
    data_path: str | None = None,
    cache_path: str | None = None,
    static_dirs: dict[str, str] | None = None,
    disable_widgets: bool | None = None,
    theme: PanelTheme | str | None = None,
    design: PanelDesign | str | None = None,
    persist: bool = False,
):
    '''Configures the global config object.
    It will override the existing config values from the existing config file or the default values.
    Args:
        theme: the theme to use for the panel, equivalent to pn.config.theme. default is 'default'.
        static_dirs: a dict of static directories to be used in pn.serve(static_dirs=...)
        write: If True, the config will be saved to the config file.
    '''
    config = get_config()
    config_dict = config.to_dict()
    config_dict.pop('__version__')
    
    static_dirs = static_dirs or {}
    assert isinstance(static_dirs, dict), "static_dirs must be a dict"
    assert 'assets' not in static_dirs, "'assets' is a reserved key in static_dirs"

    # Apply updates for non-None values
    for k in config_dict:
        v = locals().get(k)
        if v is not None:
            if '_path' in k:
                v = Path(v)
            elif k == 'theme':
                v = PanelTheme[v.lower()]
            elif k == 'design':
                v = PanelDesign[v.lower()]
            setattr(config, k, v)
    
    config.ensure_dirs()
    
    if persist:
        config.save()
        
    return config


class PFundPlotConfig(Configuration):
    DEFAULT_FILES: ClassVar[list[str]] = []
    
    def __init__(self):
        from pfund_kit.utils import load_env_file
        _ = load_env_file(verbose=False)
        super().__init__(project_name=project_name, source_file=__file__)
    
    def _initialize_from_data(self):
        assert isinstance(self._data, dict), "self._data is not a dict"
        
        self.disable_widgets: bool = self._data.get('disable_widgets', False)
        self.theme = self._data.get('theme', PanelTheme.default)
        self.design = self._data.get('design', PanelDesign.native)
        pn.extension(theme=self.theme)
        pn.extension(design=self.design)

        self.static_dirs = self._data.get('static_dirs', {})
        project_root = self._paths.project_root
        assert project_root is not None, "project_root is not set"
        self.static_dirs['assets'] = str((project_root / "ui" / "static"))
    
    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            'disable_widgets': self.disable_widgets,
            'theme': self.theme,
            'design': self.design,
            'static_dirs': self.static_dirs,
        }
        
    def prepare_docker_context(self):
        '''Prepare docker context (e.g. env variables) before running compose.yml'''
        pass
