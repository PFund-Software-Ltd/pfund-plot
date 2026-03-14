from __future__ import annotations
from typing import TYPE_CHECKING, Callable, ClassVar, Any
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    import narwhals as nw
    import panel as pn
    from pfund_plot.plots.plot import MessageKey, StreamingDfs


class BaseWidget(ABC):
    # Columns this widget requires in the df (e.g. ["date"]).
    REQUIRED_COLS: ClassVar[list[str] | None] = None

    def __init__(self, df: nw.DataFrame[Any], control: dict[str, Any], update_callback: Callable[[nw.DataFrame[Any]], None]):
        self._df = df
        self._control: dict[str, Any] = control
        self._update_callback = update_callback
        self._overlays: list[BaseWidget] = []

    @abstractmethod
    def update_df(self, df: nw.DataFrame[Any]) -> None:
        ...

    @abstractmethod
    def get_panel_objects(self) -> list[pn.widgets.Widget]:
        """Return the Panel widget objects to be placed in the toolbox."""
        ...

    def can_merge_with(self, other: BaseWidget) -> bool:
        """Can this widget merge with another widget of the same class?
        Same class = same REQUIRED_COLS = always compatible.
        """
        return True

    def add_overlay(self, other: BaseWidget) -> None:
        """Register an overlay widget so this widget's actions also update the overlay."""
        self._overlays.append(other)


class BaseStreamingWidget(ABC):
    def __init__(
        self,
        streaming_dfs: StreamingDfs,
        active_key: MessageKey,
        update_callback: Callable[[MessageKey], None],
    ):
        self._streaming_dfs = streaming_dfs
        self._active_key = active_key
        self._update_callback = update_callback
        self._overlays: list[BaseStreamingWidget] = []

    @abstractmethod
    def update_streaming_state(self, streaming_dfs: StreamingDfs) -> None:
        ...

    @abstractmethod
    def get_panel_objects(self) -> list[pn.widgets.Widget]:
        """Return the Panel widget objects to be placed in the toolbox."""
        ...

    def can_merge_with(self, other: BaseStreamingWidget) -> bool:
        """Can this widget merge with another streaming widget of the same class?
        Merge if they operate on the same set of msg_keys (i.e. same feed).
        """
        return set(self._streaming_dfs.keys()) == set(other._streaming_dfs.keys())

    def add_overlay(self, other: BaseStreamingWidget) -> None:
        """Register an overlay streaming widget so this widget's actions also update the overlay."""
        self._overlays.append(other)
