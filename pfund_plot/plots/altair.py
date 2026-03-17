from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, Any
if TYPE_CHECKING:
    from altair import Chart as AltairChart

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class Altair(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.altair]
    REQUIRED_DATA: ClassVar[bool] = False
    
    def __init__(self, fig: AltairChart, sizing_mode: str | None = None, **pane_kwargs: Any):
        '''
        Args:
            fig: An Altair Chart object.
            sizing_mode: Panel sizing mode: e.g. "stretch_width", "stretch_height", or "stretch_both".
            **pane_kwargs: Additional keyword arguments passed to pn.pane.Vega,
                e.g. height, width, max_width, margin.
        '''
        super().__init__(data=None)
        self._plot: AltairChart = fig
        self._pane_kwargs = pane_kwargs
        if sizing_mode is not None:
            self._pane_kwargs["sizing_mode"] = sizing_mode
