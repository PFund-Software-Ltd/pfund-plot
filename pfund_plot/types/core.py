from bokeh.plotting import figure
from plotly.graph_objects import Figure
from panel.io.threads import StoppableThread
from panel.layout import Panel
from panel.widgets import Widget


tFigure = figure | Figure
tOutput = tFigure | Panel | Widget | StoppableThread