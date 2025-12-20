from __future__ import annotations
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from pfeed.typing import GenericFrame
    from narwhals.typing import Frame
    from pfund_plot.plots.lazy import LazyPlot

import importlib

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class TabsStyle:
    from pfund_plot.plots.layout.tabs.panel import style as panel_style
    
    panel = panel_style

class TabsControl:
    from pfund_plot.plots.layout.tabs.panel import control as panel_control
    
    panel = panel_control
    
    
class Tabs(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.panel]

    style = TabsStyle
    control = TabsControl
    
    def __init__(self, *plots: LazyPlot):
        self._plots: tuple[LazyPlot, ...] = plots
        super().__init__(df=None, streaming_feed=None)
    
    # tabs is not at the top level of plots, it's inside layout/tabs, so we need to override the _plot property
    @property
    def _plot_func(self) -> Callable:
        """Runs the plot function for the current backend."""
        module_path = f"pfund_plot.plots.layout.{self.name}.{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")

    def _standardize_df(self, df: GenericFrame) -> Frame:
        return df
        
    def _create_widgets(self):
        pass

    def _create_component(self):
        self._component = self._plot(*self._plots, style=self._style, control=self._control)