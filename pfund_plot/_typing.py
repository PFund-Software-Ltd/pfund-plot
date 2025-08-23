from typing import Literal

from panel.io.threads import StoppableThread
from panel.layout import Panel
from panel.widgets import Widget
from panel.pane import Pane
from holoviews.core.overlay import Overlay


tFigure = Panel | Pane | Widget
tOutput = tFigure | Overlay | StoppableThread


tDisplayMode = Literal['notebook', 'browser', 'desktop']
tPlottingBackend = Literal['bokeh', 'plotly']
tDataframeBackend = Literal['tabulator', 'perspective']