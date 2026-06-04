# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import Any, Literal

from pathlib import Path

from anywidget import AnyWidget
import narwhals as nw
import traitlets


__all__ = ["CandlestickWidget", "plot", "style", "control"]


DEFAULT_HEIGHT = 280
DEFAULT_WIDTH = 670
DEFAULT_NUM_DATA = 150

# Live build output in the repo, written by `pixi run js-watch`
# (vite build --watch). Present only in a source checkout.
_DEV_BUNDLE = Path(__file__).parents[3] / "js-tap" / "dist" / "components" / "candlestick.js"
# Packaged copy shipped inside the wheel (`pixi run js-package` copies dist ->
# pfund_plot/js_tap/components/ before build; `dashboards/` will sit alongside).
# parents[2] == the pfund_plot package root.
_DIST_BUNDLE = Path(__file__).parents[2] / "js_tap" / "components" / "candlestick.js"

# No PYTHON_ENV / VITE_PORT, no dev server, no port to detect: `_esm` is always a
# built file. In a source checkout the repo build output exists, so we load that;
# anywidget watches the file (with ANYWIDGET_HMR=1) and live-reloads on rebuild.
# Installed from a wheel, only the packaged copy exists, so we load that.
_ESM = _DEV_BUNDLE if _DEV_BUNDLE.exists() else _DIST_BUNDLE


class CandlestickWidget(AnyWidget):
    _esm = _ESM
    # data plus the two config groups the frontend renders from: `style` (visual)
    # and `control` (behavior). They mirror the Python-side style()/control() dicts,
    # carrying only the keys the chart actually uses (e.g. total_height is a
    # Panel-layer concern and stays out). All are set in __init__, so no
    # default_value is needed.
    data = traitlets.List().tag(sync=True)  # list of dicts with OHLC + time
    style = traitlets.Dict().tag(sync=True)
    control = traitlets.Dict().tag(sync=True)

    def __init__(
        self,
        df: nw.DataFrame[Any],
        style: dict[str, Any],
        control: dict[str, Any],
    ) -> None:
        super().__init__()
        self.style = {
            "height": style["height"],
            "width": style["width"],
            "title": style["title"],
            "xlabel": style["xlabel"],
            "ylabel": style["ylabel"],
            "pos_color": style["pos_color"],
            "neg_color": style["neg_color"],
            "bg_color": style["bg_color"],
            "grid": style["grid"],
        }
        self.control = {"datetime_precision": control["datetime_precision"]}
        self.update_data(df)

    @staticmethod
    def _format_data(df: nw.DataFrame[Any]) -> list[dict[str, Any]]:
        """
        Convert dataframe to format supported by lightweight-charts,
        e.g. [ { "open": 10, "high": 10.63, "low": 9.49, "close": 9.55, "time": 1642377600 } ]

        `time` is sent as a UNIX timestamp in seconds (UTCTimestamp). Stringifying
        the datetime instead (e.g. '2025-01-01 09:00:00') is NOT a format
        lightweight-charts parses for intraday: it collapses every bar within a day
        onto a single point. Epoch seconds keep hourly/minute bars distinct and work
        for daily bars too. `dt.timestamp` yields the UTC epoch (naive datetimes are
        read as UTC wall-clock), which lightweight-charts renders back in UTC, so
        input time == displayed time.
        """
        if "date" in df.columns:
            # narwhals' dt.timestamp only goes down to milliseconds; floor to seconds.
            df = df.with_columns(
                time=nw.col("date").dt.timestamp("ms") // 1_000
            ).drop("date")
        return df.rows(named=True)

    def update_data(self, df: nw.DataFrame[Any]):
        """Update the widget's data from a DataFrame"""
        self.data = self._format_data(df)

    def append_data(self, new_df: nw.DataFrame[Any]):
        """Append new data points for streaming"""
        self.data += self._format_data(new_df)


def style(
    title: str = "Candlestick",
    xlabel: str = "date",
    ylabel: str = "price",
    pos_color: str = "#26a69a",
    neg_color: str = "#ef5350",
    bg_color: str = "white",
    grid: bool = True,
    total_height: int | None = None,
    height: int = DEFAULT_HEIGHT,
    width: int = DEFAULT_WIDTH,
):
    """
    Args:
        title: the title shown above the plot. Pass an empty string to hide it.
            (lightweight-charts has no native title, so it's rendered as HTML.)
        xlabel: the x-axis label shown below the plot. Empty string to hide.
            (lightweight-charts has no axis titles, so it's rendered as HTML.)
        ylabel: the y-axis label shown left of the plot. Empty string to hide.
            (lightweight-charts has no axis titles, so it's rendered as HTML.)
        pos_color: the color of the upward candle, hex code is supported
        neg_color: the color of the downward candle, hex code is supported
        bg_color: the background color of the plot, hex code is supported
        grid: whether to show the grid
        total_height: the height of the component (including the figure + widgets)
        height: the height of the figure
        width: the width of the plot
    """
    return locals()


def control(
    num_data: int = DEFAULT_NUM_DATA,
    max_data: int | None = None,
    slider_step: int | None = None,
    update_interval: int = 5000,  # ms
    incremental_update: bool = True,
    widgets: bool = True,
    datetime_precision: Literal["d", "s"] = "s",
):
    """
    Args:
        num_data: (DatetimeRangeWidget) initial number of most recent data points to display.
        max_data: (streaming) maximum number of data points kept in memory.
            If None, data will continue to grow unbounded.
        slider_step: (DatetimeRangeWidget) step size in ms for the datetime range slider.
            If None, derived from data resolution.
        update_interval: (streaming) interval in ms to update the plot. default is 5000 ms.
        incremental_update: (streaming) whether to update even when the bar is incomplete. default is True.
        widgets: whether to show widgets. default is True.
            For granular control, use remove_widgets() to remove specific widget classes.
        datetime_precision: the precision of datetime shown on the time axis / crosshair.
            "d" for days (date only), "s" for seconds (default, %H:%M:%S). Sub-second
            ("ms") is not supported: the time field is a UTCTimestamp (second-resolution).
    """
    return locals()


def plot(
    df: nw.DataFrame[Any],
    style: dict[str, Any],
    control: dict[str, Any],
    **kwargs: Any,
) -> CandlestickWidget:
    return CandlestickWidget(df, style, control)
