from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfund_plot._typing import Component, RenderedResult
    from panel.io.threads import StoppableThread

from threading import Thread
from multiprocessing import Process, Event

from pfund_plot.renderers.browser import BrowserRenderer


def _run_webview(title: str, port: int, window_ready: Event):
    import webview as wv
    window = wv.create_window(
        title,
        url=f"http://localhost:{port}",
        resizable=True,
    )
    window_ready.set()
    wv.start()
    

class DesktopRenderer(BrowserRenderer):
    def render(self, component: Component) -> RenderedResult:
        port = self._get_free_port()
        title = getattr(component, 'name', "PFund Plot")
        window_ready = Event()
        if self._is_notebook_env:
            server: StoppableThread = self.serve(component, show=False, threaded=True, port=port)
            def run_process():
                try:
                    process = Process(target=_run_webview, name=title, args=(title, port, window_ready,), daemon=True)
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
            self.run_periodic_callbacks()
            return server
        else:
            process = Process(target=_run_webview, name=title, args=(title, port, window_ready,), daemon=True)
            process.start()
            def app():
                self.run_periodic_callbacks()
                return component
                
            window_ready.wait()
            thread = Thread(
                target=lambda: self.serve(app, show=False, threaded=False, port=port),
                daemon=True
            )
            thread.start()
            process.join()