# pyright: reportUnknownMemberType=false, reportOptionalMemberAccess=false, reportCallIssue=false, reportUnusedVariable=false, reportOperatorIssue=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from panel.io.callbacks import PeriodicCallback
    from pfund_plot.typing import Component, RenderedResult
    
import time

try:
    import marimo as mo
except ImportError:
    mo = None

from pfund_plot.enums import NotebookType
from pfund_plot.renderers.base import BaseRenderer
from pfund_kit.utils import get_notebook_type


class NotebookRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()
        self._notebook_type: NotebookType | None = get_notebook_type()
        if self._notebook_type is None:
            raise ValueError("Not in a notebook environment")
    
    def run_periodic_callbacks(self):
        if self._notebook_type != NotebookType.marimo:
            super().run_periodic_callbacks()
            return
        # Don't use the thread created by periodic_callback.start(),
        # instead create a marimo thread to stream updates.
        # mo.Thread integrates with marimo's runtime context so UI mutations
        # propagate to the frontend. Its `should_exit` property is set when the
        # cell is re-run/deleted/interrupted, giving us graceful shutdown.
        def stream_updates(_periodic_callback: PeriodicCallback):
            thread = mo.current_thread()
            # REVIEW: add it back if theres data loss during streaming
            # time.sleep(1)  # HACK: wait some time to avoid data loss
            while not thread.should_exit:
                _periodic_callback.callback()
                time.sleep(_periodic_callback.period / 1000)

        for periodic_callback in self._periodic_callbacks:
            stream_thread = mo.Thread(target=stream_updates, args=(periodic_callback,), daemon=True)
            stream_thread.start()
    
    def render(self, component: Component, use_iframe: bool=False, iframe_style: str | None=None) -> RenderedResult:
        """
        Args:
            use_iframe: if True, use an iframe to display the plot in a notebook.
                It is a workaround when the plot can't be displayed in a notebook.
            iframe_style: the style of the iframe when use_iframe is True.
        """
        from pfund_kit.style import cprint, RichColor, TextStyle

        if not use_iframe:
            self.run_periodic_callbacks()
            if self._notebook_type == NotebookType.marimo:
                return mo.as_html(component)
            else:
                return component
        else:
            raise NotImplementedError("Iframe is not supported in notebook mode yet")
            # if iframe_style is None:
            #     cprint(
            #         "No iframe_style is provided for iframe in notebook", 
            #         style=TextStyle.BOLD + RichColor.YELLOW
            #     )
            # port = self._get_free_port()
            # if self._notebook_type == NotebookType.jupyter:
            #     cprint(
            #         f"If the plot can't be displayed, try to use 'from IPython.display import IFrame' and 'IFrame(src='http://localhost:{port}', width=..., height=...)'", 
            #         style=TextStyle.BOLD + RichColor.YELLOW
            #     )
            # html_pane: Pane = pn.pane.HTML(
            #     f'''
            #     <iframe 
            #         src="http://localhost:{port}" 
            #         style="{iframe_style}"
            #     </iframe>
            #     ''',
            # )
            # # let pane HTML inherit the height, width and sizing_mode from the figure, useful in layout_plot()
            # html_pane.param.update(
            #     height=component.height,
            #     width=component.width,
            #     sizing_mode=component.sizing_mode,
            # )
            # thread: StoppableThread = self.serve(component, show=False, threaded=True, port=port)
            # self.run_periodic_callbacks()
            # return thread
            # FIXME: should return html_pane instead of thread?
            # if self._notebook_type == NotebookType.marimo:
            #     return mo.as_html(html_pane)
            # else:
            #     return html_pane