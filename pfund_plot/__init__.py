from importlib.metadata import version

import hvplot
import panel as pn

from pfund_plot.config_handler import get_config, configure
from pfund_plot.plots.line import line_plot as line
from pfund_plot.plots.dataframe import dataframe_plot as dataframe, dataframe_plot as df
from pfund_plot.plots.candlestick import candlestick_plot as candlestick, candlestick_plot as ohlc


config = get_config()
hvplot.extension('bokeh', 'plotly')
pn.extension('tabulator', 'perspective')
# used to throttle updates in panel plots
# NOTE: without it, e.g. dragging a slider will cause the plot to update rapidly and lead to an error
pn.config.throttled = True


__version__ = version("pfund_plot")
__all__ = (
    "__version__",
    "get_config",
    "configure",
    "line",
    "candlestick",
    "ohlc",
)
