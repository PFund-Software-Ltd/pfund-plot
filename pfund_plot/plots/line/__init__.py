# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import ClassVar, TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame
    from panel.layout import Panel
    from pfeed.streaming.streaming_message import StreamingMessage
    from pfund_plot.widgets.base import BaseWidget, BaseStreamingWidget
    from pfund_plot.plots.plot import MessageKey

import narwhals as nw
import panel as pn

from pfund_kit.style import cprint, RichColor, TextStyle
from pfund_plot.enums import PlottingBackend
from pfund_plot.plots.plot import BasePlot
from pfund_plot.widgets.datetime_widget import DatetimeRangeWidget
from pfund_plot.widgets.ticker_widget import TickerSelectWidget


__all__ = ["Line"]


class LineStyle:
    from pfund_plot.plots.line.bokeh import style as bokeh_style

    bokeh = bokeh_style

    
class LineControl:
    from pfund_plot.plots.line.bokeh import control as bokeh_control
    
    bokeh = bokeh_control



class Line(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.bokeh]
    SUPPORT_STREAMING: ClassVar[bool] = True
    SUPPORTED_WIDGETS: ClassVar[list[type[BaseWidget]]] = [DatetimeRangeWidget]
    SUPPORTED_STREAMING_WIDGETS: ClassVar[list[type[BaseStreamingWidget]]] = [TickerSelectWidget]
    style = LineStyle
    control = LineControl

    def _standardize_df(self, df: IntoFrame) -> nw.DataFrame[Any]:
        df = nw.from_native(df)
        if isinstance(df, nw.LazyFrame):
            df = df.collect()
        return df

    def _update_df(self, df: nw.DataFrame[Any]):
        self._df = df

    def _create_component(self) -> None:
        # total_height is the height of the component (including the figure + widgets)
        height = self._style["total_height"]
        width = self._style["width"]
        self._component: Panel = pn.Column(
            self._pane,
            name="Line Chart",
            # normally these 3 parameters aren't required, but when inside a layout (GridStack), they are useful
            sizing_mode=self._get_sizing_mode(height, width),
            height=height,
            width=width,
        )
    
    def _is_streaming_ready(self) -> bool:
        if not self._streaming_dfs:
            return False
        return all(df.shape[0] >= 2 for df in self._streaming_dfs.values())
    
    def _start_streaming(self):
        from pfeed.requests.market_feed_stream_request import MarketFeedStreamRequest
        from pfund.datas.resolution import Resolution

        requests = cast(list[MarketFeedStreamRequest], self._feed._requests)
        for request in requests:
            resolution = cast(Resolution, request.target_resolution)
            if resolution.is_bar():
                if self._y is not None:
                    assert self._y in ['open', 'high', 'low', 'close', 'volume'], "y must be 'open', 'high', 'low', 'close', or 'volume' when streaming bar data"
            elif resolution.is_tick():
                if self._y is not None:
                    assert self._y in ['price', 'volume'], "y must be 'price' or 'volume' when streaming tick data"
            else:
                raise ValueError(f"Unsupported resolution: {resolution}")

        super()._start_streaming()
    
    def _create_streaming_row(self, msg: StreamingMessage) -> nw.DataFrame[Any]:
        import polars as pl
        from pfund_kit.utils.temporal import convert_ts_to_dt

        if msg.is_tick():
            from pfeed.streaming import TickMessage
            tick_msg = cast(TickMessage, msg)
            return nw.from_native(
                pl.DataFrame({
                    # strip tzinfo (already UTC) for Panel widget compatibility
                    "date": [convert_ts_to_dt(msg.ts).replace(tzinfo=None)],  
                    "price": [tick_msg.price],
                    "volume": [tick_msg.volume],
                })
            )
        elif msg.is_bar():
            from pfeed.streaming import BarMessage
            bar_msg = cast(BarMessage, msg)
            return nw.from_native(
                pl.DataFrame({
                    # strip tzinfo (already UTC) for Panel widget compatibility
                    "date": [convert_ts_to_dt(bar_msg.start_ts).replace(tzinfo=None)],  
                    "open": [bar_msg.open],
                    "high": [bar_msg.high],
                    "low": [bar_msg.low],
                    "close": [bar_msg.close],
                    "volume": [bar_msg.volume],
                })
            )
        else:
            raise ValueError(f"Unsupported streaming message type: {type(msg)}")
    
    def _create_streaming_df(self, msg_key: MessageKey, msg: StreamingMessage) -> nw.DataFrame[Any]:
        new_row = self._create_streaming_row(msg)

        if msg_key not in self._streaming_dfs:
            import datetime
            from pfund.datas.resolution import Resolution
            # prepend a dummy row so df starts with 2 rows,
            # needed for DatetimeRangeWidget to derive slider step from date_col[1] - date_col[0]
            if msg.is_bar():
                resolution_seconds = Resolution(msg.resolution).to_seconds()
            else:
                # for tick data, use 1 second as the dummy interval
                resolution_seconds = 1
            dummy = new_row.with_columns(
                nw.col("date") - datetime.timedelta(seconds=resolution_seconds),
            )
            cprint(
                f"Prepending dummy row for {msg_key} to ensure at least 2 data points for the line chart\n" +
                "i.e. The first data point is dummy data",
                style=TextStyle.BOLD + RichColor.YELLOW,
            )
            df = nw.concat([dummy, new_row])
        else:
            # update the streaming dataframe
            existing_df = self._streaming_dfs[msg_key]
            last_date = existing_df['date'][-1]
            new_date = new_row['date'][0]
            if new_date == last_date:
                # same bar — replace last row
                if msg.is_bar():
                    df = nw.concat([existing_df.head(-1), new_row])
                # NOTE: tick data could have the same timestamp!
                elif msg.is_tick():
                    df = nw.concat([existing_df, new_row])
                else:
                    raise ValueError(f"Unsupported streaming message type: {type(msg)}")
            elif new_date > last_date:
                df = nw.concat([existing_df, new_row])
            else:
                raise ValueError(f"New date {new_date} is before last date {last_date}, something is wrong with the streaming data")
        return df
        
    # NOTE: this is added to streaming feed as a custom transformation
    def _on_streaming_callback(self, msg: StreamingMessage) -> StreamingMessage:
        # for bar data, skip incremental updates unless incremental_update is enabled
        if msg.is_bar() and not self._control['incremental_update'] and msg.is_incremental:  # pyright: ignore[reportAttributeAccessIssue]
            return msg
        
        msg_key = self._create_msg_key(msg)
        df = self._create_streaming_df(msg_key, msg)
        self._update_streaming_df(msg_key, df)
        
        return msg