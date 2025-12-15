from __future__ import annotations
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pfund_plot._typing import Component, RenderedResult
    from panel.io.callbacks import PeriodicCallback
    from panel.io.threads import StoppableThread
    from panel.io.server import Server

from abc import ABC, abstractmethod

import panel as pn

import pfund_plot as plt
from pfund_plot.state import state


class BaseRenderer(ABC):
    def __init__(self):
        self._periodic_callbacks: list[PeriodicCallback] = []
        self._port: int | None = None
        self._server: StoppableThread | Server | None = None
    
    @property
    def server(self) -> StoppableThread | Server | None:
        return self._server

    def add_periodic_callback(self, periodic_callback: PeriodicCallback):
        if not isinstance(periodic_callback, PeriodicCallback):
            raise ValueError(
                "periodic_callback must be a panel.io.callbacks.PeriodicCallback instance"
            )
        self._periodic_callbacks.append(periodic_callback)
        if state.layout.in_layout:
            state.layout.add_periodic_callback(periodic_callback)

    def run_periodic_callbacks(self):
        # layout has its own renderer to handle periodic callbacks, so don't start the callbacks here
        if state.layout.in_layout:
            return
        for periodic_callback in self._periodic_callbacks:
            periodic_callback.start()

    def set_port_in_use(self, port: int):
        self._port = port
    
    @staticmethod
    def _get_free_port() -> int:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    @abstractmethod
    def render(self, component: Component, *args, **kwargs) -> RenderedResult:
        pass

    def serve(
        self,
        # component or factory function that returns a component
        renderable: Component | Callable[[], Component],
        show: bool = False,
        threaded: bool = True,
        port: int | None = None,
    ) -> StoppableThread | Server:
        if port is None:
            port = self._get_free_port()
        if self._server is not None:
            raise ValueError("Server is already running")
        self.set_port_in_use(port)
        self._server: StoppableThread | Server = pn.serve(
            renderable,
            show=show,
            threaded=threaded,
            port=port,
            static_dirs=plt.config.static_dirs,
        )
        return self._server