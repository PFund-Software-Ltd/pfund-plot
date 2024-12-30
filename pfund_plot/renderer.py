from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from bokeh.plotting import figure
    from plotly.graph_objects import Figure
    from panel.layout import Panel
    from panel.widgets import Widget
    from panel.pane import Pane
    from panel.io.threads import StoppableThread
    from panel.io.state import PeriodicCallback
    from holoviews.core.overlay import Overlay
    from pfund_plot.types.core import tOutput
    
import time
from threading import Thread
from multiprocessing import Process, Event

import panel as pn
import holoviews as hv

from pfund import print_warning
from pfund_plot.const.enums import DisplayMode, PlottingBackend, NotebookType
from pfund_plot.utils.utils import get_notebook_type, get_free_port
    

def run_webview(title: str, port: int, window_ready: Event):
    import webview as wv
    window = wv.create_window(
        title,
        url=f"http://localhost:{port}",
        resizable=True,
    )
    window.events.loaded.wait()
    window_ready.set()
    wv.start()


def _handle_periodic_callback(periodic_callback: PeriodicCallback | None):
    # the main idea is don't use the thread created by periodic_callback.start(), instead create a marimo thread to stream updates
    def _handle_marimo_streaming(periodic_callback: PeriodicCallback):
        import marimo as mo
        get_streaming_active, set_streaming_active = mo.state(True)
        
        def stream_updates():
            while get_streaming_active():  # Use the getter function
                periodic_callback.callback()
                time.sleep(periodic_callback.period / 1000)
        
        stream_thread = mo.Thread(target=stream_updates, daemon=True)
        stream_thread.start()

    notebook_type: NotebookType = get_notebook_type()
    if periodic_callback:
        if notebook_type == NotebookType.marimo:
            _handle_marimo_streaming(periodic_callback)
        else:
            periodic_callback.start()


def render(
    fig: Overlay | Panel | Pane | Widget,
    display_mode: Literal["notebook", "browser", "desktop"] | DisplayMode,
    raw_figure: bool = False,
    plotting_backend: Literal["bokeh", "plotly"] | PlottingBackend | None = None,
    periodic_callback: PeriodicCallback | None = None,
    use_iframe_in_notebook: bool = False,
    iframe_style: str | None = None,
) -> tOutput:
    '''
    Args:
        fig: the figure to render.
            supports plots from "hvplot", "holoviews" and panels, panes or widgets from "panel"
        display_mode: the mode to display the plot.
            supports "notebook", "browser" and "desktop"
        raw_figure: if True, return the figure object instead of rendering it.
            useful for customizing the figure.
        plotting_backend: the backend to use for rendering the figure.
            supports "bokeh" and "plotly"
        periodic_callback: panel's periodic callback to stream updates to the plot.
            It is created by `panel.state.add_periodic_callback`.
        use_iframe_in_notebook: if True, use an iframe to display the plot in a notebook.
            It is a workaround when the plot can't be displayed in a notebook.
        iframe_style: the style of the iframe when use_iframe_in_notebook is True.
    '''
    if isinstance(display_mode, str):
        display_mode = DisplayMode[display_mode.lower()]
    if isinstance(plotting_backend, str):
        plotting_backend = PlottingBackend[plotting_backend.lower()]

    if raw_figure:
        assert plotting_backend is not None, "plotting_backend must be provided when raw_figure is True"
        # fig is of type "Overlay" -> convert to tFigure (bokeh figure or plotly figure)
        fig: figure | Figure = hv.render(fig, backend=plotting_backend.value)
        return fig
    else:
        if display_mode == DisplayMode.notebook:
            if not use_iframe_in_notebook:
                panel_fig: Panel | Widget = fig
            else:
                if iframe_style is None:
                    print_warning("No iframe_style is provided for iframe in notebook")
                port = get_free_port()
                server: StoppableThread = pn.serve(fig, show=False, threaded=True, port=port)
                panel_fig: Pane = pn.pane.HTML(
                    f'''
                    <iframe 
                        src="http://localhost:{port}" 
                        style="{iframe_style}"
                    </iframe>
                    ''',
                )
            _handle_periodic_callback(periodic_callback)
            return panel_fig
        elif display_mode == DisplayMode.browser:
            server: StoppableThread = pn.serve(fig, show=True, threaded=True)
            _handle_periodic_callback(periodic_callback)
            return server
        elif display_mode == DisplayMode.desktop:
            port = get_free_port()
            server: StoppableThread = pn.serve(fig, show=False, threaded=True, port=port)
            title = getattr(fig, 'name', "PFund Plot")
            window_ready = Event()
            def run_process():
                try:
                    # NOTE: need to run in a separate process, otherwise jupyter notebook will hang after closing the webview window
                    process = Process(target=run_webview, name=title, args=(title, port, window_ready,), daemon=True)
                    process.start()
                    process.join()
                except Exception as e:
                    print(f"An error occurred: {e}")
                finally:
                    server.stop()
            # NOTE: need to run the process in a separate thread, otherwise periodic callbacks when streaming=True won't work
            # because process.join() will block the thread
            thread = Thread(target=run_process, daemon=True)
            thread.start()
            
            # wait for the window to be ready before starting the periodic callback to prevent data loss when streaming=True
            window_ready.wait()
            _handle_periodic_callback(periodic_callback)
            return server
        else:
            raise ValueError(f"Invalid display mode: {display_mode}")
