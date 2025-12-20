from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfund_plot.plots.dataframe import (
        dataframe_plot as dataframe,
        dataframe_plot as df,
    )
    from pfund_plot.plots.candlestick import (
        Candlestick as candlestick,
        Candlestick as ohlc,
        Candlestick as kline,
    )
    from pfund_plot.plots.layout import (
        Layout as layout,
    )
    from pfund_plot.plots.plotly import (
        Plotly as plotly,
    )

from importlib.metadata import version

import panel as pn

from pfund_plot.config import get_config, configure


# NOTE: this MUST be True, otherwise, some widgets won't work properly, e.g. candlestick widgets, slider and input will both trigger each other due to panel's async update, which leads to infinite loop.
pn.config.throttled = True  # If panel sliders and inputs should be throttled until release of mouse.
# NOTE: /assets can only be recognized when setting pn.serve(static_dirs=pfund_plot.config.static_dirs)
# see static_dirs in config.py
pn.config.js_files = {
    "widgets_amd_config": "/assets/widgets-amd-config.js",
}


print_warning = lambda msg: print(f'\033[95m{msg}\033[0m')


def __getattr__(name: str):
    if name == 'plotly':
        from pfund_plot.plots.plotly import Plotly
        return Plotly
    elif name in ('candlestick', 'ohlc', 'kline'):
        from pfund_plot.plots.candlestick import Candlestick
        return Candlestick
    elif name == 'layout':
        from pfund_plot.plots.layout import Layout
        return Layout
    else:
        raise AttributeError(f"'{__name__}' has no attribute '{name}'")
    # TODO
    # elif name in ('dataframe', 'df'):
    #     from pfund_plot.plots.dataframe import dataframe_plot
    


__version__ = version("pfund_plot")
__all__ = (
    "__version__",
    "get_config", "configure",
    "plotly",
    "candlestick", "ohlc", "kline",
    "dataframe", "df",
    "layout",
)
def __dir__():
    return sorted(__all__)
