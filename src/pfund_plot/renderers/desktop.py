# pyright: reportUnknownMemberType=false
from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from panel.io.threads import StoppableThread

    from pfund_plot.typing import Component

from multiprocessing import Event as create_event
from multiprocessing import Process
from multiprocessing.synchronize import Event
from threading import Thread

from pfund_kit.style import RichColor, TextStyle, cprint

from pfund_plot.renderers.browser import BrowserRenderer


def _run_webview(title: str, port: int, window_ready: Event):
    import webview as wv

    _ = wv.create_window(
        title,
        url=f"http://localhost:{port}",
        resizable=True,
    )
    window_ready.set()
    wv.start()


class DesktopRenderer(BrowserRenderer):
    def render(self, component: Component):
        port = self._get_free_port()
        title = getattr(component, "name", "PFund Plot")
        window_ready = create_event()
        if self.is_in_notebook_env():
            server = cast(
                "StoppableThread",
                self.serve(component, show=False, threaded=True, port=port),
            )

            def run_process():
                try:
                    process = Process(
                        target=_run_webview,
                        name=title,
                        args=(
                            title,
                            port,
                            window_ready,
                        ),
                        daemon=True,
                    )
                    process.start()
                    process.join()
                except Exception as e:
                    cprint(
                        f"An error occurred: {e}", style=TextStyle.BOLD + RichColor.RED
                    )
                finally:
                    server.stop()

            thread = Thread(target=run_process, daemon=True)
            thread.start()
            # wait for the window to be ready before starting the periodic callback to prevent data loss during streaming
            _ = window_ready.wait()
            self.run_periodic_callbacks()
            return server
        else:
            process = Process(
                target=_run_webview,
                name=title,
                args=(
                    title,
                    port,
                    window_ready,
                ),
                daemon=True,
            )
            try:
                process.start()
            except RuntimeError as e:
                if "freeze_support" in str(
                    e
                ) or "current process has finished its bootstrapping phase" in str(e):
                    raise RuntimeError(
                        "Failed to start desktop renderer process.\n"
                        + "Please wrap your code with:\n\n"
                        + "    if __name__ == '__main__':\n"
                        + "        # your code here\n"
                    ) from None
                raise
            _ = window_ready.wait()

            def _servable():
                self.run_periodic_callbacks()
                return component

            thread = Thread(
                target=lambda: self.serve(
                    _servable, show=False, threaded=False, port=port
                ),
                daemon=True,
            )
            thread.start()

            process.join()
