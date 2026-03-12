from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    import narwhals as nw
    import panel as pn
    from pfund_plot.plots.plot import MessageKey, StreamingDfs


class BaseWidget(ABC):
    @abstractmethod
    def __init__(self, df: nw.DataFrame[Any], control: dict[str, Any], update_callback: Callable[[nw.DataFrame[Any]], None]):
        ...

    @abstractmethod
    def update_df(self, df: nw.DataFrame[Any]) -> None:
        ...

    @abstractmethod
    def get_panel_objects(self) -> list[pn.widgets.Widget]:
        """Return the Panel widget objects to be placed in the toolbox."""
        ...


class BaseStreamingWidget(ABC):
    @abstractmethod
    def __init__(
        self,
        streaming_dfs: StreamingDfs,
        active_key: MessageKey,
        update_callback: Callable[[MessageKey], None],
    ):
        ...
    
    @abstractmethod
    def update_streaming_state(self, streaming_dfs: StreamingDfs) -> None:
        ...

    @abstractmethod
    def get_panel_objects(self) -> list[pn.widgets.Widget]:
        """Return the Panel widget objects to be placed in the toolbox."""
        ...
