# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias, cast

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame
    from panel.layout import Panel
    from pfund.datas.data_bar import BarData
    from pfund.typing import ProductName, ResolutionRepr
    from pfeed.feeds.market_feed import MarketFeed
    from pfeed.streaming import BarMessage
    MessageKey: TypeAlias = tuple[ProductName, ResolutionRepr]

import panel as pn
import narwhals as nw

from pfund_kit.style import cprint, RichColor, TextStyle
from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


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
    style = CandlestickStyle
    control = CandlestickControl

    def __init__(self, df: IntoFrame | None = None, streaming_feed: MarketFeed | None = None):
        super().__init__(data=df, streaming_feed=streaming_feed)
        self._streaming_bars: dict[MessageKey, BarData] = {}
        self._streaming_dfs: dict[MessageKey, nw.DataFrame[Any]] = {}
        self._active_key: MessageKey | None = None
    
    def _standardize_data(self, df: IntoFrame) -> nw.DataFrame[Any]:
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
    
    def _create_widgets(self):
        from pfund_plot.plots.candlestick.widgets import CandlestickWidgets
        self._widgets = CandlestickWidgets(self._data, self._control, self._update_pane)  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
    
    def _update_widgets(self, df: nw.DataFrame[Any]):
        if self._widgets is None:
            self._create_widgets()
        self._widgets.update_df(df)
        
    # TODO: add ticker selector: ticker = pn.widgets.Select(options=['AAPL', 'IBM', 'GOOG', 'MSFT'], name='Ticker')
    # TODO: use tick data to update the current candlestick
    def _create_component(self):
        # TODO: add volume plot when show_volume is True
        # show_volume = style['show_volume']
        if self._widgets is None:
            self._create_widgets()
            
        toolbox = pn.FlexBox(
            self._widgets.datetime_range_input,
            self._widgets.datetime_range_slider,
            align_items="center",
            justify_content="center",
        )

        # NOTE: somehow data update on anywidget (svelte) in marimo notebook doesn't work using Panel
        # (probably need a refresh of the marimo cell to reflect the changes), so use mo.vstack() as a workaround
        if self._is_using_marimo_svelte_combo():
            import marimo as mo

            # NOTE: self._style is NOT applied in this case
            self._component = mo.vstack([self._anywidget, toolbox])
        else:
            # total_height is the height of the component (including the figure + widgets)
            height = self._style["total_height"]
            width = self._style["width"]
            self._component: Panel = pn.Column(
                self._pane,
                toolbox,
                name="Candlestick Chart",
                # normally these 3 parameters aren't required, but when inside a layout (GridStack), they are useful
                sizing_mode=self._get_sizing_mode(height, width),
                height=height,
                width=width,
            )
    
    @staticmethod
    def _create_msg_key(msg: BarMessage) -> MessageKey:
        return (msg.product, msg.resolution)
    
    def _is_streaming_ready(self):
        '''Return True if all streaming dataframes have at least 2 rows (needed for hvplot ohlc to compute candle width).'''
        if not self._streaming_dfs:
            return False
        return all(df.shape[0] >= 2 for df in self._streaming_dfs.values())
    
    def _start_streaming(self):
        from pfeed.requests.market_feed_stream_request import MarketFeedStreamRequest
        from pfund.datas.resolution import Resolution

        requests = cast(list[MarketFeedStreamRequest], self._streaming_feed._requests)
        assert all(request.is_streaming() for request in requests), "Not all requests in the streaming feed are for streaming"
        assert all(cast(Resolution, request.target_resolution).is_bar() for request in requests), "candlestick streaming only supports bar data"

        if self._data is not None:
            stream_resolution = cast(Resolution, requests[0].target_resolution)
            stream_resolution_in_seconds = stream_resolution.to_seconds()
            date_col = self._data['date']
            df_resolution = (date_col[1] - date_col[0]).total_seconds()
            
            if df_resolution != stream_resolution_in_seconds:
                raise ValueError(f"DataFrame resolution does not match stream resolution {stream_resolution}")

        super()._start_streaming()
        
    def _on_streaming_callback(self, msg: BarMessage) -> BarMessage:
        import polars as pl
        from pfeed.streaming import BarMessage
        from pfund.datas.resolution import Resolution
        from pfund.datas.data_bar import BarData

        def create_new_bar(data: BarData) -> nw.DataFrame[Any]:
            bar = data.bar
            new_row = nw.from_native(
                pl.DataFrame({
                    "date": [bar.start_dt.replace(tzinfo=None)],  # strip tzinfo (already UTC) for Panel widget compatibility
                    "open": [bar.open],
                    "high": [bar.high],
                    "low": [bar.low],
                    "close": [bar.close],
                    "volume": [bar.volume],
                })
            )
            return new_row
        
        msg_key: MessageKey = self._create_msg_key(msg)
        # set the first product as active by default
        if self._active_key is None:
            self._active_key = msg_key
        
        
        # Step 1: create bar data from message and update the streaming bars
        if not isinstance(msg, BarMessage):
            raise ValueError(f"Unsupported streaming message type: {type(msg)}")
        if msg_key not in self._streaming_bars:
            data = BarData(
                data_source=msg.data_source,
                data_origin=msg.data_origin,
                product=self._streaming_feed.create_product(
                    basis=msg.basis,
                    name=msg.product,
                    symbol=msg.symbol,
                    **msg.specs
                ),
                resolution=Resolution(msg.resolution),
                shift=0,
                skip_first_bar=False,
            )
            self._streaming_bars[msg_key] = data
        data = self._streaming_bars[msg_key]
        data.on_bar(
            o=msg.open, h=msg.high, l=msg.low, c=msg.close, v=msg.volume,
            ts=msg.ts, start_ts=msg.start_ts, end_ts=msg.end_ts,
            msg_ts=msg.msg_ts,
            extra_data=msg.extra_data,
            is_incremental=msg.is_incremental,
        )
        

        # Step 2: update the streaming dataframe by adding a new row to it
        if not (self._control['incremental_update'] or data.is_closed()):
            return msg
        new_row = create_new_bar(data)
        
        if msg_key not in self._streaming_dfs:
            # prepend a dummy row so df starts with 2 rows,
            # needed for hvplot ohlc (candle width) and widgets (slider range)
            import datetime
            resolution_seconds = data.bar.resolution.to_seconds()
            dummy = new_row.with_columns(
                nw.col("date") - datetime.timedelta(seconds=resolution_seconds),
            )
            cprint(
                f"Prepending dummy row for {msg_key} to ensure at least 2 data points for the candlestick plot\n" +
                "i.e. The first candlestick is dummy data",
                style=TextStyle.BOLD + RichColor.YELLOW,
            )
            self._streaming_dfs[msg_key] = nw.concat([dummy, new_row])

        df = self._streaming_dfs[msg_key]
        last_date = df['date'][-1]
        new_date = new_row['date'][0]
        if new_date == last_date:
            # same candle period — replace last row (incomplete bar update)
            df = nw.concat([df.head(-1), new_row])
        elif new_date > last_date:
            # new candle period — append
            df = nw.concat([df, new_row])
        else:
            raise ValueError(f"New date {new_date} is before last date {last_date}, something is wrong with the streaming data")
        # if exceeds max_data, truncate the dataframe
        max_data = self._control['max_data']
        if max_data and df.shape[0] > max_data:
            df = df.tail(max_data)
        self._streaming_dfs[msg_key] = df


        # Step 3: update the data reference if the received message key is the active key
        if msg_key == self._active_key:
            self._update_data(df)
        return msg
