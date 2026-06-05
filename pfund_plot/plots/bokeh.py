from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

if TYPE_CHECKING:
    from bokeh.model import Model as BokehModel

from pfund_plot.enums import PlottingBackend
from pfund_plot.plots.plot import BasePlot


class Bokeh(BasePlot):
    SUPPORTED_BACKENDS: ClassVar[list[Literal[PlottingBackend.bokeh]]] = [
        PlottingBackend.bokeh
    ]
    REQUIRED_DATA: ClassVar[bool] = False

    def __init__(
        self, fig: BokehModel, sizing_mode: str | None = None, **pane_kwargs: Any
    ):
        """
        Args:
            fig: A Bokeh Model object.
            sizing_mode: Panel sizing mode: e.g. "stretch_width", "stretch_height", or "stretch_both".
            **pane_kwargs: Additional keyword arguments passed to pn.pane.Bokeh,
                e.g. height, width, max_width, margin.
        """
        super().__init__(data=None)
        self._plot: BokehModel = fig
        self._pane_kwargs = pane_kwargs
        if sizing_mode is not None:
            self._pane_kwargs["sizing_mode"] = sizing_mode
