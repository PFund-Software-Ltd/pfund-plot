from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from panel.io.callbacks import PeriodicCallback
    from panel.io.server import Server
    from panel.io.threads import StoppableThread

    from pfund_plot.enums import NotebookType
    from pfund_plot.typing import Component, RenderedResult

from abc import ABC, abstractmethod

import panel as pn


class BaseRenderer(ABC):
    def __init__(self):
        from pfund_kit.utils import get_notebook_type

        self._periodic_callbacks: list[PeriodicCallback] = []
        self._port: int | None = None
        self._server: StoppableThread | Server | None = None
        self._notebook_type: NotebookType | None = get_notebook_type()

    def is_in_notebook_env(self) -> bool:
        return self._notebook_type is not None

    @property
    def server(self) -> StoppableThread | Server | None:
        return self._server

    def add_periodic_callback(self, periodic_callback: PeriodicCallback):
        from panel.io.callbacks import PeriodicCallback

        if not isinstance(periodic_callback, PeriodicCallback):
            raise ValueError(
                "periodic_callback must be a panel.io.callbacks.PeriodicCallback instance"
            )
        self._periodic_callbacks.append(periodic_callback)

    def run_periodic_callbacks(self):
        for periodic_callback in self._periodic_callbacks:
            periodic_callback.start()

    def set_port_in_use(self, port: int):
        self._port = port

    @staticmethod
    def _get_free_port() -> int:
        from pfund_kit.utils import get_free_port

        return get_free_port()

    @abstractmethod
    def render(self, component: Component, *args: Any, **kwargs: Any) -> RenderedResult:
        pass

    def serve(
        self,
        # component or factory function that returns a component
        renderable: Component | Callable[[], Component],
        show: bool = False,
        threaded: bool = True,
        port: int | None = None,
    ) -> StoppableThread | Server:
        from pfund_plot.config import get_config

        if port is None:
            port = self._get_free_port()
        if self._server is not None:
            raise ValueError("Server is already running")
        config = get_config()
        self.set_port_in_use(port)
        self._server = pn.serve(  # pyright: ignore[reportUnknownMemberType]
            renderable,  # pyright: ignore[reportArgumentType]
            show=show,
            threaded=threaded,
            port=port,
            static_dirs=config.static_dirs,
        )
        return self._server
