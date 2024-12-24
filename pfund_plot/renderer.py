from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfund_plot.types.core import tFigure
    from panel.layout import Panel
    from panel.io.threads import StoppableThread
    from holoviews.core.overlay import Overlay

import socket
from multiprocessing import Process

import panel as pn
import holoviews as hv

from pfund_plot.const.enums import DisplayMode, PlottingBackend
    

def run_webview(title: str, port: int):
    import webview as wv
    wv.create_window(
        title,
        url=f"http://localhost:{port}",
        resizable=True,
    )
    wv.start() 
    
    
def render(
    fig: Overlay | Panel,
    display_mode: DisplayMode,
    plotting_backend: PlottingBackend,
    raw_figure: bool,
) -> tFigure | Panel | StoppableThread | Process:
    if raw_figure:
        # fig is of type "Overlay" -> convert to tFigure (bokeh figure or plotly figure)
        fig: tFigure = hv.render(fig, backend=plotting_backend.value)
        return fig
    else:
        if display_mode == DisplayMode.notebook:
            panel_fig: Panel = fig
            return panel_fig
        elif display_mode == DisplayMode.browser:
            server: StoppableThread = pn.serve(fig, show=True, threaded=True)
            return server
        elif display_mode == DisplayMode.desktop:
            def _get_free_port():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))  # Bind to a random free port
                    return s.getsockname()[1]
            port = _get_free_port()
            server: StoppableThread = pn.serve(fig, show=False, threaded=True, port=port)
            title = getattr(fig, 'name', "PFund Plot")
            try:
                # NOTE: need to run in a separate process, otherwise jupyter notebook will hang after closing the webview window
                process = Process(target=run_webview, name=title, args=(title, port, ), daemon=True)
                process.start()
                process.join()
                return process
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                server.stop()
        else:
            raise ValueError(f"Invalid display mode: {display_mode}")