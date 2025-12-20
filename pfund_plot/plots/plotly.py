from __future__ import annotations
from typing import TYPE_CHECKING, Callable, TypeAlias
if TYPE_CHECKING:
    from plotly.graph_objects import Figure as PlotlyFigure
    from pfeed.typing import GenericFrame
    from narwhals.typing import Frame
    from pfeed.feeds.market_feed import MarketFeed
    PlotFunction: TypeAlias = Callable[[Frame], PlotlyFigure]

import panel as pn

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class Plotly(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.plotly]
    
    def __init__(
        self, 
        figure_or_plot_func: PlotlyFigure | PlotFunction,
        df: GenericFrame | None = None,
        streaming_feed: MarketFeed | None = None,
        streaming_freq: int = BasePlot.STREAMING_FREQ,
    ):
        pn.extension("plotly")
        super().__init__(df=df, streaming_feed=streaming_feed, streaming_freq=streaming_freq)
        self._fig = None
        self._plot_func = None
        if callable(figure_or_plot_func):
            self._plot_func = figure_or_plot_func
        else:
            self._fig = figure_or_plot_func

    @property
    def _plot(self) -> PlotFunction | None:
        return self._plot_func
    
    @property
    def plot(self) -> PlotlyFigure:
        return self._plot(self._df) if self._plot is not None else self._fig
    
    def _standardize_df(self, df: GenericFrame) -> Frame:
        import narwhals as nw
        df: Frame = nw.from_native(df)
        return df

    def _create_widgets(self) -> None:
        pass

    def _create_component(self) -> None:
        self._component = pn.Column(self._pane)