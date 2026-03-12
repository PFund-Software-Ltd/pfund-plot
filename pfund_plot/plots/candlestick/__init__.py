# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, ClassVar, cast

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame
    from panel.layout import Panel
    from pfeed.streaming import BarMessage
    from pfund_plot.widgets.base import BaseWidget, BaseStreamingWidget
    from pfund_plot.plots.plot import MessageKey

import panel as pn
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

    def _standardize_df(self, df: IntoFrame) -> nw.DataFrame[Any]:
        import datetime
        df = nw.from_native(df)
        if isinstance(df, nw.LazyFrame):
            df = df.collect()
        # convert all columns to lowercase
        df = df.rename({col: col.lower() for col in df.columns})
        # rename 'datetime' to 'date'
        if "datetime" in df.columns and "date" not in df.columns:
            df = df.rename({"datetime": "date"})
        missing_cols = [col for col in self.REQUIRED_COLS if col not in df.columns]  # pyright: ignore[reportOptionalIterable]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        date_value = df.select("date").row(0)[0]
        # convert date to datetime if not already
        if not isinstance(date_value, datetime.datetime):
            # REVIEW: this might mess up the datetime format
            df = df.with_columns(
                nw.col("date").str.to_datetime(format=None),
            )
        # normalize to naive UTC — Panel/Bokeh widgets don't handle tz-aware datetimes consistently
        date_dtype = df.collect_schema()["date"]
        if hasattr(date_dtype, 'time_zone') and date_dtype.time_zone is not None:  # pyright: ignore[reportAttributeAccessIssue]
            df = df.with_columns(
                nw.col("date").dt.convert_time_zone("UTC").dt.replace_time_zone(None)
            )
        return df
    
    def _create_component(self):
        # TODO: add volume plot when show_volume is True
        # show_volume = style['show_volume']

        # NOTE: somehow data update on anywidget (svelte) in marimo notebook doesn't work using Panel
        # (probably need a refresh of the marimo cell to reflect the changes), so use mo.vstack() as a workaround
        if self._is_using_marimo_svelte_combo():
            import marimo as mo

            # NOTE: self._style is NOT applied in this case
            self._component = mo.vstack([self._anywidget])
        else:
            # total_height is the height of the component (including the figure + widgets)
            height = self._style["total_height"]
            width = self._style["width"]
            self._component: Panel = pn.Column(
                self._pane,
                name="Candlestick Chart",
                # normally these 3 parameters aren't required, but when inside a layout (GridStack), they are useful
                sizing_mode=self._get_sizing_mode(height, width),
                height=height,
                width=width,
            )
    
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
