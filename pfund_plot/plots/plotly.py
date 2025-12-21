from __future__ import annotations
from typing import TYPE_CHECKING, Callable, TypeAlias
if TYPE_CHECKING:
    from plotly.graph_objects import Figure as PlotlyFigure
    from pfeed.typing import GenericFrame
    from narwhals.typing import Frame
    from pfeed.feeds.market_feed import MarketFeed
    PlotlyFunction: TypeAlias = Callable[[Frame], PlotlyFigure]

import panel as pn

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class Plotly(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.plotly]
    
    def __init__(
        self, 
        fig_or_func: PlotlyFigure | PlotlyFunction,
        df: GenericFrame | None = None,
        streaming_feed: MarketFeed | None = None,
        streaming_freq: int = BasePlot.STREAMING_FREQ,
    ):
        pn.extension("plotly")
        super().__init__(df=df, streaming_feed=streaming_feed, streaming_freq=streaming_freq)
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
    
    def _standardize_df(self, df: GenericFrame) -> Frame:
        import narwhals as nw
        df: Frame = nw.from_native(df)
        return df

    def _create_widgets(self) -> None:
        pass

    def _create_component(self) -> None:
        self._component = pn.Column(self._pane)