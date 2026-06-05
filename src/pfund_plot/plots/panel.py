from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

if TYPE_CHECKING:
    from panel.viewable import Viewable

import panel as pn

from pfund_plot.enums import PlottingBackend
from pfund_plot.plots.plot import BasePlot


class Panel(BasePlot):
    """Wraps a pre-built Panel ``Viewable`` so it can participate in layouts.

    Combining plots with ``+`` or ``|`` produces a ``LazyRow``/``LazyColumn``
    (raw Panel components), not a ``LazyPlot``. This adapter lets such a
    component be dropped into ``plt.tabs`` / ``plt.layout`` like any other plot.
    """

    SUPPORTED_BACKENDS: ClassVar[list[Literal[PlottingBackend.panel]]] = [
        PlottingBackend.panel
    ]
    REQUIRED_DATA: ClassVar[bool] = False

    def __init__(self, viewable: Viewable, name: str | None = None):
        super().__init__(data=None, name=name)
        self._viewable: Viewable = viewable

    # the viewable is already fully built — no plot/pane construction needed
    def _create_plot(self) -> None:
        pass

    def _create_pane(self) -> None:
        pass

    def _create_component(self) -> None:
        # The viewable is already a finished component (no plot/pane layer here),
        # but Panel makes `name` a constant param — it can't be renamed after
        # construction, and the pre-built viewable keeps Panel's auto name like
        # "LazyRow03407". So wrap it in a named pn.Column (the only way to attach a
        # name); that name is what plt.tabs shows as the tab label. With no name=
        # passed, self.name falls back to the class name "panel".
        self._component = pn.Column(self._viewable, name=self.name)
