from panel.io.threads import StoppableThread
from panel.layout import Panel
from panel.widgets import Widget
from panel.pane import Pane
from holoviews.core.overlay import Overlay
from bokeh.plotting import figure
from plotly.graph_objects import Figure


tFigure = figure | Figure | Overlay | Panel | Pane | Widget
tOutput = tFigure | StoppableThread
