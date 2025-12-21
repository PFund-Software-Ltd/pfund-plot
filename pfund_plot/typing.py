from __future__ import annotations
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from marimo import Html as MarimoHtml
    from anywidget import AnyWidget
    from panel.io.threads import StoppableThread
    from panel.layout import Panel
    from panel.widgets import Widget
    from holoviews.core.overlay import Overlay
    from bokeh.plotting._figure import figure as BokehFigure
    from plotly.graph_objects import Figure as PlotlyFigure
    from altair import Chart as AltairChart
    from matplotlib.figure import Figure as MatplotlibFigure
    
    RawFigure = BokehFigure | PlotlyFigure | AltairChart | MatplotlibFigure
    Figure = RawFigure | AnyWidget
    Plot = Overlay | AnyWidget
    Component = Panel | Widget | MarimoHtml
    RenderedResult = Component | StoppableThread

tDisplayMode = Literal["notebook", "browser", "desktop"]
tPlottingBackend = Literal[
    "panel", "bokeh", "svelte", "plotly", "altair", "matplotlib", "perspective",
]
tDataframeBackend = Literal["tabulator", "perspective"]
tPanelTheme = Literal["default", "light", "dark"]
tPanelDesign = Literal["native", "material", "fast", "bootstrap"]
