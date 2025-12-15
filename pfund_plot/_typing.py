from __future__ import annotations
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from marimo import Html as MarimoHtml
    from anywidget import AnyWidget
    from panel.io.threads import StoppableThread
    from panel.layout import Panel
    from panel.widgets import Widget
    from bokeh.plotting._figure import figure as BokehFigure
    from plotly.graph_objects import Figure as PlotlyFigure
    from matplotlib.figure import Figure as MatplotlibFigure
    from holoviews.core.overlay import Overlay
    
    Component = Panel | MarimoHtml | Widget
else:
    MarimoHtml = None
    Component = Panel | Widget
    

RawFigure = BokehFigure | PlotlyFigure | MatplotlibFigure | AnyWidget
WrappedFigure = Overlay | AnyWidget
RenderedResult = Component | StoppableThread


tDisplayMode = Literal['notebook', 'browser', 'desktop']
tPlottingBackend = Literal['bokeh', 'svelte', 'plotly', 'altair', 'matplotlib', 'perspective']
tDataframeBackend = Literal['tabulator', 'perspective']