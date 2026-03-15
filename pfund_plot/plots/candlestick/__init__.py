# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, ClassVar, cast

if TYPE_CHECKING:
    from pfeed.streaming import BarMessage
    from pfund_plot.widgets.base import BaseWidget, BaseStreamingWidget
    from pfund_plot.plots.plot import MessageKey

import narwhals as nw

from pfund_kit.style import cprint, RichColor, TextStyle
from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend
from pfund_plot.widgets.datetime_widget import DatetimeRangeWidget
from pfund_plot.widgets.ticker_widget import TickerSelectWidget


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


class Candlestick(BasePlot):
    REQUIRED_COLS: ClassVar[list[str]] = ["date", "open", "high", "low", "close", "volume"]
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = [PlottingBackend.bokeh, PlottingBackend.svelte]
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
    
    def _is_streaming_ready(self):
        '''Return True if all streaming dataframes have at least 2 rows (needed for hvplot ohlc to compute candle width).'''
        if not self._streaming_dfs:
            return False
        return all(df.shape[0] >= 2 for df in self._streaming_dfs.values())
    
    def _start_streaming(self):
        from pfeed.requests.market_feed_stream_request import MarketFeedStreamRequest
        from pfund.datas.resolution import Resolution

        requests = cast(list[MarketFeedStreamRequest], self._feed._requests)
        assert all(cast(Resolution, request.target_resolution).is_bar() for request in requests), "candlestick streaming only supports bar data"

        super()._start_streaming()
    
    def _create_streaming_row(self, msg: BarMessage) -> nw.DataFrame[Any]:
        import polars as pl
        from pfund_kit.utils.temporal import convert_ts_to_dt
        return nw.from_native(
            pl.DataFrame({
                # strip tzinfo (already UTC) for Panel widget compatibility
                "date": [convert_ts_to_dt(msg.start_ts).replace(tzinfo=None)],  
                "open": [msg.open],
                "high": [msg.high],
                "low": [msg.low],
                "close": [msg.close],
                "volume": [msg.volume],
            })
        )
    
    def _create_streaming_df(self, msg_key: MessageKey, msg: BarMessage) -> nw.DataFrame[Any]:
        new_row = self._create_streaming_row(msg)

        if msg_key not in self._streaming_dfs:
            import datetime
            from pfund.datas.resolution import Resolution
            # prepend a dummy row so df starts with 2 rows,
            # needed for hvplot ohlc (candle width) and widgets (slider range)
            resolution_seconds = Resolution(msg.resolution).to_seconds()
            dummy = new_row.with_columns(
                nw.col("date") - datetime.timedelta(seconds=resolution_seconds),
            )
            cprint(
                f"Prepending dummy row for {msg_key} to ensure at least 2 data points for the candlestick plot\n" +
                "i.e. The first candlestick is dummy data",
                style=TextStyle.BOLD + RichColor.YELLOW,
            )
            df = nw.concat([dummy, new_row])
        else:
            # update the streaming dataframe
            existing_df = self._streaming_dfs[msg_key]
            last_date = existing_df['date'][-1]
            new_date = new_row['date'][0]
            if new_date == last_date:
                # same candle period — replace last row (incomplete bar update)
                df = nw.concat([existing_df.head(-1), new_row])
            elif new_date > last_date:
                # new candle period — append
                df = nw.concat([existing_df, new_row])
            else:
                raise ValueError(f"New date {new_date} is before last date {last_date}, something is wrong with the streaming data")
        return df

    # NOTE: this is added to streaming feed as a custom transformation
    def _on_streaming_callback(self, msg: BarMessage) -> BarMessage:
        if not self._control['incremental_update'] and msg.is_incremental:
            return msg

        msg_key = self._create_msg_key(msg)
        df = self._create_streaming_df(msg_key, msg)
        self._update_streaming_df(msg_key, df)

        return msg
