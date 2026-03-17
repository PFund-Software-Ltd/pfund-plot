from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, Any
if TYPE_CHECKING:
    from holoviews.core import Dimensioned

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class Holoviews(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.holoviews]
    REQUIRED_DATA: ClassVar[bool] = False
    
    def __init__(self, fig: Dimensioned, sizing_mode: str | None = None, **pane_kwargs: Any):
        '''
        Args:
            fig: A Holoviews Dimensioned object.
            sizing_mode: Panel sizing mode: e.g. "stretch_width", "stretch_height", or "stretch_both".
            **pane_kwargs: Additional keyword arguments passed to pn.pane.HoloViews,
                e.g. height, width, max_width, margin.
        '''
        super().__init__(data=None)
        self._plot: Dimensioned = fig
        self._pane_kwargs = pane_kwargs
        if sizing_mode is not None:
            self._pane_kwargs["sizing_mode"] = sizing_mode
