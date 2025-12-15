from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from panel.layout import Panel
    from panel.widgets import Widget
    from panel.pane import Pane
    from panel.io.threads import StoppableThread
    from pfund_plot._typing import RenderedResult, tDisplayMode
    
import time
from threading import Thread
from multiprocessing import Process, Event

import panel as pn
try:
    import marimo as mo
except ImportError:
    mo = None
import pfund_plot as plt
from panel.io.callbacks import PeriodicCallback

from pfund import print_warning
from pfund_plot.enums import DisplayMode, NotebookType
from pfund_plot.utils.utils import get_notebook_type
from pfund_plot.state import state
    

def run_webview(title: str, port: int, window_ready: Event):
    import webview as wv
    window = wv.create_window(
        title,
        url=f"http://localhost:{port}",
        resizable=True,
    )
    window_ready.set()
    wv.start()


def _handle_periodic_callback(periodic_callback: PeriodicCallback | None, notebook_type: NotebookType | None):
    # the main idea is don't use the thread created by periodic_callback.start(), instead create a marimo thread to stream updates
    def _handle_marimo_streaming(periodic_callback: PeriodicCallback):
        get_streaming_active, set_streaming_active = mo.state(True)
        
        def stream_updates():
            time.sleep(1)  # HACK: wait some time to avoid data loss
            while get_streaming_active():  # Use the getter function
                periodic_callback.callback()
                time.sleep(periodic_callback.period / 1000)
        
        stream_thread = mo.Thread(target=stream_updates, daemon=True)
        stream_thread.start()
        
    if periodic_callback:
        # postpone the periodic callback until the layout plot is called; otherwise there will be data loss
        if state.layout.in_layout:
            state.layout.add_periodic_callback(periodic_callback)
        else:
            if mo and notebook_type == NotebookType.marimo:
                _handle_marimo_streaming(periodic_callback)
            else:
                periodic_callback.start()


def run_callbacks(periodic_callbacks: list[PeriodicCallback], notebook_type: NotebookType | None):
    for callback in periodic_callbacks:
        _handle_periodic_callback(callback, notebook_type)


def render(
    fig: Panel | Pane | Widget,
    mode: tDisplayMode,
    periodic_callbacks: list[PeriodicCallback] | PeriodicCallback | None = None,
    use_iframe_in_notebook: bool = False,
    iframe_style: str | None = None,
) -> RenderedResult:
    '''
    Args:
        fig: the figure to render.
            supports plots from "hvplot", "holoviews" and panels, panes or widgets from "panel"
        mode: the mode to display the plot.
            supports "notebook", "browser" and "desktop"
        plotting_backend: the backend to use for rendering the figure.
            supports "bokeh" and "plotly"
        periodic_callback: panel's periodic callback to stream updates to the plot.
            It is created by `panel.state.add_periodic_callback`.
        use_iframe_in_notebook: if True, use an iframe to display the plot in a notebook.
            It is a workaround when the plot can't be displayed in a notebook.
        iframe_style: the style of the iframe when use_iframe_in_notebook is True.
    '''
    mode = DisplayMode[mode.lower()]
    
    if isinstance(periodic_callbacks, PeriodicCallback):
        periodic_callbacks = [periodic_callbacks]
    
    static_dirs = plt.config.static_dirs
    notebook_type: NotebookType | None = get_notebook_type()
    # NOTE: handling differs between notebook environment and python script
    is_notebook_env = (notebook_type is not None)
    
    if mode == DisplayMode.notebook:
        if not use_iframe_in_notebook:
            panel_fig: Panel | Pane | Widget = fig
            run_callbacks(periodic_callbacks, notebook_type)
            if mo and notebook_type == NotebookType.marimo:
                return mo.as_html(panel_fig)
        else:
            if iframe_style is None:
                print_warning("No iframe_style is provided for iframe in notebook")
            port = get_free_port()
            if notebook_type == NotebookType.jupyter:
                print_warning(f"If the plot can't be displayed, try to use 'from IPython.display import IFrame' and 'IFrame(src='http://localhost:{port}', width=..., height=...)'")
            panel_fig: Pane = pn.pane.HTML(
                f'''
                <iframe 
                    src="http://localhost:{port}" 
                    style="{iframe_style}"
                </iframe>
                ''',
            )
            # let pane HTML inherit the height, width and sizing_mode from the figure, useful in layout_plot()
            panel_fig.param.update(
                height=fig.height,
                width=fig.width,
                sizing_mode=fig.sizing_mode,
            )
            if is_notebook_env:
                server: StoppableThread = pn.serve(fig, show=False, threaded=True, port=port, static_dirs=static_dirs)
                run_callbacks(periodic_callbacks, notebook_type)
            # NOTE: only happens when running layout_plot() where components are all using mode="notebook" in a python script 
            else:
                def run_server():
                    run_callbacks(periodic_callbacks, notebook_type)
                    pn.serve(fig, show=False, threaded=True, port=port, static_dirs=static_dirs)  # this will block the main thread
                thread = Thread(target=run_server, daemon=True)
                thread.start()
        return panel_fig
    elif mode == DisplayMode.browser:
        if is_notebook_env:
            server: StoppableThread = pn.serve(fig, show=True, threaded=True, static_dirs=static_dirs)
            run_callbacks(periodic_callbacks, notebook_type)
            return server
        else:  # run in a python script
            run_callbacks(periodic_callbacks, notebook_type)
            pn.serve(fig, show=True, threaded=False, static_dirs=static_dirs)  # this will block the main thread
    elif mode == DisplayMode.desktop:
        port = get_free_port()
        title = getattr(fig, 'name', "PFund Plot")
        window_ready = Event()
        if is_notebook_env:
            server: StoppableThread = pn.serve(fig, show=False, threaded=True, port=port, static_dirs=static_dirs)
            def run_process():
                try:
                    process = Process(target=run_webview, name=title, args=(title, port, window_ready,), daemon=True)
                    process.start()
                    process.join()
                except Exception as e:
                    print(f"An error occurred: {e}")
                finally:
                    server.stop()
            thread = Thread(target=run_process, daemon=True)
            thread.start()
            # wait for the window to be ready before starting the periodic callback to prevent data loss when streaming=True
            window_ready.wait()
            run_callbacks(periodic_callbacks, notebook_type)
            return server
        else:
            process = Process(target=run_webview, name=title, args=(title, port, window_ready,), daemon=True)
            process.start()
            def app():
                run_callbacks(periodic_callbacks, notebook_type)
                return fig
                
            window_ready.wait()
            thread = Thread(
                target=lambda: pn.serve(app, show=False, threaded=False, port=port, static_dirs=static_dirs),
                daemon=True
            )
            thread.start()
            process.join()
    else:
        raise ValueError(f"Invalid display mode: {mode}")
