from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from panel.io.threads import StoppableThread
    from pfund_plot._typing import Component

try:
    import marimo as mo
except ImportError:
    mo = None

from pfund_plot.renderers.base import BaseRenderer
from pfund_plot.utils.utils import get_notebook_type


class BrowserRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()
        self._is_notebook_env: bool = get_notebook_type() is not None
    
    def render(self, component: Component):
        if self._is_notebook_env:  # run browser mode in a notebook environment
            thread: StoppableThread = self.serve(component, show=True, threaded=True)
            self.run_periodic_callbacks()
            return thread
        else:  # run in a python script
            self.run_periodic_callbacks()
            # this will block the main thread
            self.serve(component, show=True, threaded=False)