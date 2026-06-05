from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

if TYPE_CHECKING:
    from plotly.graph_objects import Figure as PlotlyFigure

from pfund_plot.enums import PlottingBackend
from pfund_plot.plots.plot import BasePlot


class Plotly(BasePlot):
    SUPPORTED_BACKENDS: ClassVar[list[Literal[PlottingBackend.plotly]]] = [
        PlottingBackend.plotly
    ]
    REQUIRED_DATA: ClassVar[bool] = False

    def __init__(
        self, fig: PlotlyFigure, sizing_mode: str | None = None, **pane_kwargs: Any
    ):
        """
        Args:
            fig: A Plotly Figure object.
            sizing_mode: Panel sizing mode: e.g. "stretch_width", "stretch_height", or "stretch_both".
            **pane_kwargs: Additional keyword arguments passed to pn.pane.Plotly,
                e.g. height, width, max_width, margin.
        """
        super().__init__(data=None)
        self._plot: PlotlyFigure = fig
        self._pane_kwargs = pane_kwargs
        if sizing_mode is not None:
            self._pane_kwargs["sizing_mode"] = sizing_mode
