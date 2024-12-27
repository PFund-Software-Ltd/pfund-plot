from bokeh.plotting import figure
from plotly.graph_objects import Figure
from panel.io.threads import StoppableThread
from panel.layout import Panel
from panel.io.server import Server


tFigure = figure | Figure
tOutput = tFigure | Panel | Server | StoppableThread