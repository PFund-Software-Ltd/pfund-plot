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


hvplot.extension('bokeh', 'plotly')
pn.extension('tabulator', 'perspective', 'gridstack')
# used to throttle updates in panel plots
# NOTE: without it, e.g. dragging a slider will cause the plot to update rapidly and lead to an error
pn.config.throttled = True


Matplotlib = pn.pane.Matplotlib
Bokeh = pn.pane.Bokeh
Plotly = pn.pane.Plotly
Altair = Vega = pn.pane.Vega


__version__ = version("pfund_plot")
__all__ = (
    "__version__",
    "Matplotlib",
    "Bokeh",
    "Plotly",
    "Vega", "Altair",
    "get_config",
    "configure",
    "candlestick",
    "ohlc",
    "kline",
    "dataframe",
    "df",
    "layout",
)
def __dir__():
    return sorted(__all__)
