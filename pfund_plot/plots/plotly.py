from __future__ import annotations
from typing import TYPE_CHECKING, Callable, TypeAlias, ClassVar
if TYPE_CHECKING:
    from plotly.graph_objects import Figure as PlotlyFigure
    from pfeed.typing import GenericFrame
    from narwhals.typing import IntoFrame
    from pfeed.feeds.market_feed import MarketFeed
    PlotlyFunction: TypeAlias = Callable[[IntoFrame], PlotlyFigure]

import panel as pn

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class Plotly(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.plotly]
    REQUIRED_DATA: ClassVar[bool] = False
    
    def __init__(
        self, 
        fig_or_func: PlotlyFigure | PlotlyFunction,
        data: IntoFrame | MarketFeed | None = None,
    ):
        pn.extension("plotly")
        super().__init__(data=data)
        self._plotly_fig: PlotlyFigure | None = None
        self._plot: PlotlyFigure | None
        self._plotly_func: PlotlyFunction | None = None
        if callable(fig_or_func):
            self._plotly_func = fig_or_func
        else:
            self._plotly_fig = fig_or_func

    @property
    def _plot_func(self) -> PlotlyFunction | None:
        return self._plotly_func

    def _create_plot(self):
        self._plot: PlotlyFigure = self._plot_func(self._df) if self._plot_func is not None else self._plotly_fig
    
    def _create_component(self) -> None:
        self._component = pn.Column(self._pane)
