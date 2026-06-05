from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pfund_plot.plots.altair import (
        Altair as altair,
    )
    from pfund_plot.plots.altair import (
        Altair as vega,
    )
    from pfund_plot.plots.area import (
        Area as area,
    )
    from pfund_plot.plots.bar import (
        Bar as bar,
    )
    from pfund_plot.plots.bokeh import (
        Bokeh as bokeh,
    )
    from pfund_plot.plots.candlestick import (
        Candlestick as candlestick,
    )
    from pfund_plot.plots.candlestick import (
        Candlestick as kline,
    )
    from pfund_plot.plots.candlestick import (
        Candlestick as ohlc,
    )
    from pfund_plot.plots.holoviews import (
        Holoviews as holoviews,
    )
    from pfund_plot.plots.holoviews import (
        Holoviews as hv,
    )
    from pfund_plot.plots.label import (
        Label as label,
    )
    from pfund_plot.plots.layout import (
        Layout as layout,
    )
    from pfund_plot.plots.layout.tabs import (
        Tabs as tabs,
    )
    from pfund_plot.plots.line import (
        Line as line,
    )
    from pfund_plot.plots.matplotlib import (
        Matplotlib as matplotlib,
    )
    from pfund_plot.plots.matplotlib import (
        Matplotlib as mpl,
    )
    from pfund_plot.plots.plotly import (
        Plotly as plotly,
    )
    from pfund_plot.plots.scatter import (
        Scatter as scatter,
    )
    from pfund_plot.plots.scatter.marker import (
        Marker as marker,
    )

# NOTE: data update in anywidget (backend=svelte) may have issues (especially in marimo) after loading panel extensions
# if anywidget+svelte backend is not working, try to comment this out
#
# plotly/vega resolve to panel.models.* (bundled with Panel) — they don't import the
# plotly/altair libs, so they're safe even when those optional extras aren't installed.
# "ipywidgets" pulls in panel.io.ipywidget -> ipywidgets_bokeh, which is absent in WASM
# (and where the anywidget/svelte backend isn't available anyway), so guard only that one.
import importlib.util

import panel as pn

from pfund_plot.config import configure, get_config

_panel_extensions = ["plotly", "vega"]
if importlib.util.find_spec("ipywidgets_bokeh") is not None:
    _panel_extensions.append("ipywidgets")
pn.extension(*_panel_extensions)
# NOTE: this MUST be True, otherwise, some widgets won't work properly, e.g. candlestick widgets, slider and input will both trigger each other due to panel's async update, which leads to infinite loop.
pn.config.throttled = (
    True  # If panel sliders and inputs should be throttled until release of mouse.
)


def __getattr__(name: str):
    if name == "__version__":
        from importlib.metadata import version

        return version("pfund_plot")
    elif name == "plotly":
        from pfund_plot.plots.plotly import Plotly

        return Plotly
    elif name in ("candlestick", "ohlc", "kline"):
        from pfund_plot.plots.candlestick import Candlestick

        return Candlestick
    elif name == "line":
        from pfund_plot.plots.line import Line

        return Line
    elif name == "area":
        from pfund_plot.plots.area import Area

        return Area
    elif name == "layout":
        from pfund_plot.plots.layout import Layout

        return Layout
    elif name == "tabs":
        from pfund_plot.plots.layout.tabs import Tabs

        return Tabs
    elif name == "scatter":
        from pfund_plot.plots.scatter import Scatter

        return Scatter
    elif name == "marker":
        from pfund_plot.plots.scatter.marker import Marker

        return Marker
    elif name == "label":
        from pfund_plot.plots.label import Label

        return Label
    elif name == "bar":
        from pfund_plot.plots.bar import Bar

        return Bar
    elif name in ("altair", "vega"):
        from pfund_plot.plots.altair import Altair

        return Altair
    elif name in ("matplotlib", "mpl"):
        from pfund_plot.plots.matplotlib import Matplotlib

        return Matplotlib
    elif name == "bokeh":
        from pfund_plot.plots.bokeh import Bokeh

        return Bokeh
    elif name in ("holoviews", "hv"):
        from pfund_plot.plots.holoviews import Holoviews

        return Holoviews
    else:
        raise AttributeError(f"'{__name__}' has no attribute '{name}'")


__all__ = (
    "altair",
    "area",
    "bar",
    "bokeh",
    "candlestick",
    "configure",
    "get_config",
    "holoviews",
    "hv",
    "kline",
    "label",
    "layout",
    "line",
    "marker",
    "matplotlib",
    "mpl",
    "ohlc",
    "plotly",
    "scatter",
    "tabs",
    "vega",
)


def __dir__():
    return sorted(__all__)
