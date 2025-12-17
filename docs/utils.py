from io import StringIO

from bokeh.resources import INLINE
from IPython.display import HTML, display

from pfund_plot.typing import Component


def display_html(component: Component):
    html_buffer = StringIO()
    component.save(html_buffer, resources=INLINE)
    html_buffer.seek(0)  # Go to the beginning of the buffer
    display(HTML(html_buffer.read()))
