from __future__ import annotations
from typing import TYPE_CHECKING, TypeAlias, Any

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

    Style: TypeAlias = dict[str, Any]
    Control: TypeAlias = dict[str, Any]
