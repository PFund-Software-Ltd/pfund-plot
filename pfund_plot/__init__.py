from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfund_plot.plots.candlestick import (
        Candlestick as candlestick,
        Candlestick as ohlc,
        Candlestick as kline,
    )
    from pfund_plot.plots.line import (
        Line as line,
    )
    from pfund_plot.plots.layout import (
        Layout as layout,
    )
    from pfund_plot.plots.layout.tabs import (
        Tabs as tabs,
    )
    from pfund_plot.plots.plotly import (
        Plotly as plotly,
    )
    from pfund_plot.plots.altair import (
        Altair as altair,
        Altair as vega,
    )
    from pfund_plot.plots.matplotlib import (
        Matplotlib as matplotlib,
        Matplotlib as mpl,
    )
    from pfund_plot.plots.bokeh import (
        Bokeh as bokeh,
    )
    from pfund_plot.plots.holoviews import (
        Holoviews as holoviews,
        Holoviews as hv,
    )
    from pfund_plot.plots.scatter import (
        Scatter as scatter,
    )
    from pfund_plot.plots.scatter.marker import (
        Marker as marker,
    )
    from pfund_plot.plots.label import (
        Label as label,
    )
    from pfund_plot.plots.area import (
        Area as area,
    )
    from pfund_plot.plots.bar import (
        Bar as bar,
    )

from importlib.metadata import version

import panel as pn

from pfund_plot.config import get_config, configure


# NOTE: data update in anywidget (backend=svelte) may have issues (especially in marimo) after loading panel extensions
# if anywidget+svelte backend is not working, try to comment this out
pn.extension("plotly", "vega", 'ipywidgets')
# NOTE: this MUST be True, otherwise, some widgets won't work properly, e.g. candlestick widgets, slider and input will both trigger each other due to panel's async update, which leads to infinite loop.
pn.config.throttled = True  # If panel sliders and inputs should be throttled until release of mouse.
# NOTE: /assets can only be recognized when setting pn.serve(static_dirs=pfund_plot.config.static_dirs)
# see static_dirs in config.py
pn.config.js_files = {
    "widgets_amd_config": "/assets/widgets-amd-config.js",
}


def __getattr__(name: str):
    if name == 'plotly':
        from pfund_plot.plots.plotly import Plotly
        return Plotly
    elif name in ('candlestick', 'ohlc', 'kline'):
        from pfund_plot.plots.candlestick import Candlestick
        return Candlestick
    elif name == 'line':
        from pfund_plot.plots.line import Line
        return Line
    elif name == 'area':
        from pfund_plot.plots.area import Area
        return Area
    elif name == 'layout':
        from pfund_plot.plots.layout import Layout
        return Layout
    elif name == 'tabs':
        from pfund_plot.plots.layout.tabs import Tabs
        return Tabs
    elif name == 'scatter':
        from pfund_plot.plots.scatter import Scatter
        return Scatter
    elif name == 'marker':
        from pfund_plot.plots.scatter.marker import Marker
        return Marker
    elif name == 'label':
        from pfund_plot.plots.label import Label
        return Label
    elif name == 'bar':
        from pfund_plot.plots.bar import Bar
        return Bar
    elif name in ('altair', 'vega'):
        from pfund_plot.plots.altair import Altair
        return Altair
    elif name in ('matplotlib', 'mpl'):
        from pfund_plot.plots.matplotlib import Matplotlib
        return Matplotlib
    elif name == 'bokeh':
        from pfund_plot.plots.bokeh import Bokeh
        return Bokeh
    elif name in ('holoviews', 'hv'):
        from pfund_plot.plots.holoviews import Holoviews
        return Holoviews
    else:
        raise AttributeError(f"'{__name__}' has no attribute '{name}'")


__version__ = version("pfund_plot")
__all__ = (
    "__version__",
    "get_config", "configure",
    "plotly", "altair", "vega", "matplotlib", "mpl", "bokeh", "holoviews", "hv",
    "candlestick", "ohlc", "kline",
    "line",
    "layout", "tabs",
    "scatter",
    "marker",
    "label",
    "area",
    "bar",
)
def __dir__():
    return sorted(__all__)
