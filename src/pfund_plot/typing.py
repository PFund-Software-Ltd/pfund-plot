from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

# NOTE: these are kept under TYPE_CHECKING because the backend libs (plotly, altair,
# matplotlib, marimo, ...) are OPTIONAL dependencies. Importing them at runtime would
# make `import pfund_plot.typing` crash for users who didn't install that extra.
# Guarding here (+ `from __future__ import annotations` in consumers) keeps the names
# available to type-checkers/IDEs while never importing the optional libs at runtime.
if TYPE_CHECKING:
    from altair import Chart as AltairChart
    from anywidget import AnyWidget
    from bokeh.plotting._figure import figure as BokehFigure
    from holoviews.core.overlay import Overlay
    from marimo import Html as MarimoHtml
    from matplotlib.figure import Figure as MatplotlibFigure
    from panel.io.threads import StoppableThread
    from panel.layout import Panel
    from panel.widgets import Widget
    from plotly.graph_objects import Figure as PlotlyFigure

    RawFigure = BokehFigure | PlotlyFigure | AltairChart | MatplotlibFigure
    Figure = RawFigure | AnyWidget
    Plot = Overlay | AnyWidget
    Component = Panel | Widget | MarimoHtml
    RenderedResult = Component | StoppableThread

    Style: TypeAlias = dict[str, Any]
    Control: TypeAlias = dict[str, Any]
