from typing import Literal

from anywidget import AnyWidget
from panel.io.threads import StoppableThread
from panel.layout import Panel
from panel.widgets import Widget
from panel.pane import Pane
from holoviews.core.overlay import Overlay


Component = Panel | Pane | Widget | AnyWidget
Output = Component | Overlay | StoppableThread


tDisplayMode = Literal['notebook', 'browser', 'desktop']
tPlottingBackend = Literal['bokeh', 'svelte', 'plotly', 'altair', 'matplotlib']
tDataframeBackend = Literal['tabulator', 'perspective']