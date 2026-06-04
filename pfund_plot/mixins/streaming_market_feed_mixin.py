# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pfund.datas.resolution import Resolution
    from pfeed.streaming import BarMessage, TickMessage
    from pfeed.streaming.market_data_message import MarketDataMessage
    from pfeed.requests.market_feed_stream_request import MarketFeedStreamRequest
    from pfund_plot.plots.plot import MessageKey

import narwhals as nw

from pfund_kit.style import cprint, RichColor, TextStyle


class StreamingMarketFeedMixin:
    def _is_streaming_ready(self) -> bool:
        '''Return True if all streaming dataframes have at least 2 rows (needed for e.g. ohlc to compute candle width).'''
        if not self._streaming_dfs:
            return False
        return all(df.shape[0] >= 2 for df in self._streaming_dfs.values())

    def _start_streaming(self):
        from pfund_plot.utils import import_hvplot_df_module

        # streaming always uses polars internally (see _create_streaming_row)
        import_hvplot_df_module('polars')

        requests = cast("list[MarketFeedStreamRequest]", self._feed._requests)
        for request in requests:
            resolution = cast("Resolution", request.target_resolution)
            if resolution.is_bar():
                if self._y is not None:
                    assert self._y in ['open', 'high', 'low', 'close', 'volume'], "y must be 'open', 'high', 'low', 'close', or 'volume' when streaming bar data"
            elif resolution.is_tick():
                if self._y is not None:
                    assert self._y in ['price', 'volume'], "y must be 'price' or 'volume' when streaming tick data"
            else:
                raise ValueError(f"Unsupported resolution: {resolution}")

        super()._start_streaming()

    def _create_streaming_row(self, msg: MarketDataMessage) -> nw.DataFrame[Any]:
        import polars as pl

        if msg.is_tick():
            tick_msg = cast("TickMessage", msg)
            return nw.from_native(
                pl.DataFrame({
                    # msg.ts is int64 ns since epoch; from_epoch yields a tz-naive
                    # (already UTC) datetime[ns], preserving nanosecond precision
                    "date": pl.from_epoch(pl.Series([tick_msg.ts]), time_unit="ns"),
                    "price": [tick_msg.price],
                    # volume can be None (e.g. yahoo finance); pin dtype so a leading
                    # None row doesn't become a Null column and break later concats
                    "volume": pl.Series([tick_msg.volume], dtype=pl.Float64),
                })
            )
        elif msg.is_bar():
            bar_msg = cast("BarMessage", msg)
            return nw.from_native(
                pl.DataFrame({
                    # bar_msg.start_ts is int64 ns since epoch (start of bar);
                    # from_epoch yields a tz-naive (already UTC) datetime[ns]
                    "date": pl.from_epoch(pl.Series([bar_msg.start_ts]), time_unit="ns"),
                    "open": [bar_msg.open],
                    "high": [bar_msg.high],
                    "low": [bar_msg.low],
                    "close": [bar_msg.close],
                    "volume": [bar_msg.volume],
                })
            )
        else:
            raise ValueError(f"Unsupported streaming message type: {type(msg)}")

    def _create_streaming_df(self, msg_key: MessageKey, msg: MarketDataMessage) -> nw.DataFrame[Any]:
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
                # cast back to ns: subtracting a timedelta downcasts datetime[ns] -> datetime[us],
                # which would then fail to concat with the ns-precision new_row below
                (nw.col("date") - datetime.timedelta(seconds=resolution_seconds)).cast(nw.Datetime("ns")),
            )
            cprint(
                f"Prepending dummy row for {msg_key} to ensure at least 2 data points for the {self._class_name}\n" +
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

    def _create_msg_key(self, msg: MarketDataMessage) -> MessageKey:
        '''Create a message key for streaming'''
        msg_key = (msg.product, msg.resolution)
        # set the first product as active by default
        if self._active_msg_key is None:
            self._active_msg_key = msg_key
        return msg_key

    # NOTE: this is added to streaming feed as a custom transformation
    def _on_streaming_callback(self, msg: MarketDataMessage) -> MarketDataMessage:
        # for bar data, skip incremental updates unless incremental_update is enabled
        if msg.is_bar() and not self._control['incremental_update'] and msg.is_incremental:  # pyright: ignore[reportAttributeAccessIssue]
            return msg

        msg_key = self._create_msg_key(msg)
        df = self._create_streaming_df(msg_key, msg)
        self._update_streaming_df(msg_key, df)

        return msg
