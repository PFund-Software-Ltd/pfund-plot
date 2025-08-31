from importlib.metadata import version

import hvplot
import panel as pn

from pfund_plot.config import get_config, configure
from pfund_plot.plots.dataframe import (
    dataframe_plot as dataframe,
    dataframe_plot as df,
)
from pfund_plot.plots.candlestick import (
    candlestick,
    candlestick as ohlc,
    candlestick as kline,
)
from pfund_plot.layout import layout


config = get_config()



hvplot.extension('bokeh', 'plotly', 'matplotlib')
pn.extension('ipywidgets', 'gridstack', 'tabulator', 'perspective')
pn.config.throttled = True  # If panel sliders and inputs should be throttled until release of mouse.
# NOTE: /assets can only recognized when setting pn.serve(static_dirs=pfund_plot.config.static_dirs)
# see static_dirs in config.py
pn.config.js_files = {
    "widgets_amd_config": "/assets/widgets-amd-config.js",
}


Matplotlib = pn.pane.Matplotlib
Bokeh = pn.pane.Bokeh
Plotly = pn.pane.Plotly
Altair = Vega = pn.pane.Vega


__version__ = version("pfund_plot")
__all__ = (
    "__version__",
    "config",
    "configure",
    "Matplotlib",
    "Bokeh",
    "Plotly",
    "Vega", "Altair",
    "candlestick",
    "ohlc",
    "kline",
    "dataframe",
    "df",
    "layout",
)
def __dir__():
    return sorted(__all__)
