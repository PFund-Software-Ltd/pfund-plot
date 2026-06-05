# pyright: reportUnusedParameter=false
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from holoviews.core.overlay import Overlay

import narwhals as nw

from pfund_plot.enums import PlottingBackend

__all__ = ["control", "plot", "style"]


DEFAULT_HEIGHT = 280
DEFAULT_NUM_DATA = 150


def style(
    title: str = "Candlestick",
    xlabel: str = "date",
    ylabel: str = "price",
    pos_color: str = "green",
    neg_color: str = "red",
    bg_color: str = "",  # empty string by default because Panel will automatically use the theme color
    grid: bool = True,
    total_height: int | None = None,
    height: int = DEFAULT_HEIGHT,
    width: int | None = None,
):
    """
    Args:
        title: the title of the plot
        xlabel: the label of the x-axis
        ylabel: the label of the y-axis
        pos_color: the color of the upward candle, hex code is supported
        neg_color: the color of the downward candle, hex code is supported
        bg_color: the background color of the plot, hex code is supported
        total_height: the height of the component (including the figure + widgets)
            Default is None, when it is None, Panel will automatically adjust its height
        height: the height of the figure
        width: the width of the plot, since the plot is responsive, this is only used in panel layout
        grid: whether to show the grid
    """
    return locals()


def control(
    num_data: int = DEFAULT_NUM_DATA,
    max_data: int | None = None,
    slider_step: int | None = None,
    linked_axes: bool = True,
    update_interval: int = 5000,  # ms
    incremental_update: bool = True,
    widgets: bool = True,
    datetime_precision: Literal["d", "s", "ms"] = "s",
):
    """
    Args:
        num_data: (DatetimeRangeWidget) initial number of most recent data points to display.
        max_data: (streaming) maximum number of data points kept in memory.
            If None, data will continue to grow unbounded.
        slider_step: (DatetimeRangeWidget) step size in ms for the datetime range slider.
            If None, derived from data resolution.
        linked_axes: whether to link axes across plots in a layout (plt.layout(...)).
        update_interval: (streaming) interval in ms to update the plot. default is 5000 ms.
        incremental_update: (streaming) whether to update even when the bar is incomplete. default is True.
        widgets: whether to show widgets. default is True.
            For granular control, use remove_widgets() to remove specific widget classes.
        datetime_precision: the precision of datetime formatting on the hover tooltip.
            "d" for days (%Y-%m-%d), "s" for seconds (default, %Y-%m-%d %H:%M:%S), "ms" for milliseconds (%Y-%m-%d %H:%M:%S.%3N).
    """
    return locals()


def plot(
    df: nw.DataFrame[Any],
    style: dict[str, Any],
    control: dict[str, Any],
    x: str | None = None,
    y: str | list[str] | None = None,
    **kwargs: Any,
) -> Overlay:
    import hvplot
    from bokeh.models import CrosshairTool

    from pfund_plot.plots.candlestick import Candlestick
    from pfund_plot.utils.bokeh import create_bundled_hover_tool

    _ = hvplot.extension(PlottingBackend.bokeh)

    date_col = Candlestick.REQUIRED_COLS[0]
    ohlc_cols = Candlestick.REQUIRED_COLS[1:]
    # include optional cols (e.g. volume) only when present in the df
    value_cols = ohlc_cols + [
        col for col in Candlestick.OPTIONAL_COLS if col in df.columns
    ]
    return (
        df.to_native()
        .hvplot.ohlc(
            date_col,
            ohlc_cols,
            hover_cols=[date_col, *value_cols],
            tools=[
                create_bundled_hover_tool(
                    df, date_col, value_cols, control["datetime_precision"]
                ),
                CrosshairTool(dimensions="height", line_color="gray", line_alpha=0.3),
            ],
            responsive=True,
            grid=style["grid"],
            pos_color=style["pos_color"],
            neg_color=style["neg_color"],
            bgcolor=style["bg_color"],
            **kwargs,
        )
        .opts(
            title=style["title"],
            xlabel=style["xlabel"],
            ylabel=style["ylabel"],
            height=style["height"],
        )
    )
