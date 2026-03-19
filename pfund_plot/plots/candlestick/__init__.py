# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from pfund_plot.widgets.base import BaseWidget, BaseStreamingWidget

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend
from pfund_plot.widgets.datetime_widget import DatetimeRangeWidget
from pfund_plot.widgets.ticker_widget import TickerSelectWidget
from pfund_plot.mixins.streaming_market_feed_mixin import StreamingMarketFeedMixin


__all__ = ["Candlestick"]


class CandlestickStyle:
    from pfund_plot.plots.candlestick.bokeh import style as bokeh_style
    from pfund_plot.plots.candlestick.svelte import style as svelte_style

    bokeh = bokeh_style
    svelte = svelte_style

    
class CandlestickControl:
    from pfund_plot.plots.candlestick.bokeh import control as bokeh_control
    from pfund_plot.plots.candlestick.svelte import control as svelte_control
    
    bokeh = bokeh_control
    svelte = svelte_control


class Candlestick(StreamingMarketFeedMixin, BasePlot):
    REQUIRED_COLS: ClassVar[list[str]] = ["date", "open", "high", "low", "close", "volume"]
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = [
        PlottingBackend.bokeh, 
        # TODO: add back svelte
        # PlottingBackend.svelte,
    ]
    SUPPORT_STREAMING: ClassVar[bool] = True
    SUPPORTED_WIDGETS: ClassVar[list[type[BaseWidget]]] = [DatetimeRangeWidget]
    SUPPORTED_STREAMING_WIDGETS: ClassVar[list[type[BaseStreamingWidget]]] = [TickerSelectWidget]
    style = CandlestickStyle
    control = CandlestickControl

    def _create_component(self):
        # NOTE: somehow data update on anywidget (svelte) in marimo notebook doesn't work using Panel
        # (probably need a refresh of the marimo cell to reflect the changes), so use mo.vstack() as a workaround
        if self._is_using_marimo_svelte_combo():
            import marimo as mo

            # NOTE: self._style is NOT applied in this case
            self._component = mo.vstack([self._anywidget])
        else:
            super()._create_component()
    
    def _start_streaming(self):
        from pfeed.requests.market_feed_stream_request import MarketFeedStreamRequest
        from pfund.datas.resolution import Resolution

        requests = cast(list[MarketFeedStreamRequest], self._feed._requests)
        assert all(cast(Resolution, request.target_resolution).is_bar() for request in requests), "candlestick streaming only supports bar data"

        super()._start_streaming()
