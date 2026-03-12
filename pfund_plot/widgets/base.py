from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    import narwhals as nw
    import panel as pn


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
