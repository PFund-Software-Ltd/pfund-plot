from io import StringIO

from bokeh.resources import INLINE
from IPython.display import HTML, display

from pfund_plot.types.core import tFigure


def display_html(fig: tFigure):
    html_buffer = StringIO()
    fig.save(html_buffer, resources=INLINE)
    html_buffer.seek(0)  # Go to the beginning of the buffer
    display(HTML(html_buffer.read()))