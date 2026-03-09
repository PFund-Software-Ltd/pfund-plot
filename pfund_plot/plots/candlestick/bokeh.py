# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from holoviews.core.overlay import Overlay

import narwhals as nw
from bokeh.models import HoverTool, CrosshairTool, CustomJSHover


__all__ = ["plot", "style", "control"]


PLOT_OPTIONS = [
    "title",
    "xlabel",
    "ylabel",
    "height",
]  # specified options supported in .opts()
DEFAULT_HEIGHT = 280
DEFAULT_NUM_DATA = 150


def style(
    title: str = "Candlestick Chart",
    xlabel: str = "Date",
    ylabel: str = "Price",
    up_color: str = "green",
    down_color: str = "red",
    bg_color: str = '',  # empty string by default because Panel will automatically use the theme color
    total_height: int | None = None,
    height: int = DEFAULT_HEIGHT,
    width: int | None = None,
    grid: bool = True,
):
    """
    Args:
        title: the title of the plot
        xlabel: the label of the x-axis
        ylabel: the label of the y-axis
        up_color: the color of the upward candle, hex code is supported
        down_color: the color of the downward candle, hex code is supported
        bg_color: the background color of the plot, hex code is supported
        total_height: the height of the component (including the figure + widgets)
            Default is None, when it is None, Panel will automatically adjust its height
        height: the height of the figure
        width: the width of the plot
    """
    return locals()


def control(
    num_data: int = DEFAULT_NUM_DATA,
    max_data: int | None = None,
    slider_step: int | None = None,
    show_volume: bool = True,
    linked_axes: bool = True,
    incremental_update: bool = True,
    update_interval: int = 5000,  # ms
):
    """
    Args:
        num_data: the initial number of data points to display.
            This can be changed by a slider in the plot.
        max_data: the maximum number of data points kept in memory.
            If None, data will continue to grow unbounded.
        slider_step: the step size of the datetime range slider. if None, it will be derived from the data.
        show_volume: whether to show the volume plot. default is True.
        linked_axes: whether to link the axes of bokeh plots inside this pane
            across a panel layout.
        incremental_update: whether to update the plot even when the bar is incomplete during streaming. default is True.
        update_interval: the interval in milliseconds to update the plot during streaming. default is 5000 ms.
    """
    return locals()


def plot(df: nw.DataFrame[Any], style: dict[str, Any], control: dict[str, Any]) -> Overlay:
    import hvplot
    from pfund_plot.plots.candlestick import Candlestick
    from pfund_plot.utils import is_daily_data
    from pfund_plot.enums import PlottingBackend

    def _create_hover_tool(date_format: str) -> HoverTool:
        # Format numbers with appropriate precision:
        # - Large numbers (>= 1): up to 4 decimal places, trailing zeros removed
        # - Small numbers (< 1): up to 8 significant digits to preserve meaningful precision
        num_formatter = CustomJSHover(code="""
            if (Math.abs(value) >= 1) {
                return value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4});
            }
            return value.toPrecision(8).replace(/0+$/, '').replace(/\\.$/, '');
        """)
        return HoverTool(
            tooltips=[
                ("date", f"@date{{{date_format}}}"),
                ("open", "@open{custom}"),
                ("high", "@high{custom}"),
                ("low", "@low{custom}"),
                ("close", "@close{custom}"),
                ("volume", "@volume{custom}"),
            ],
            formatters={
                "@date": "datetime",
                "@open": num_formatter,
                "@high": num_formatter,
                "@low": num_formatter,
                "@close": num_formatter,
                "@volume": num_formatter,
            },
            mode="vline",
        )


    def _create_crosshair_tool():
        return CrosshairTool(dimensions="height", line_color="gray", line_alpha=0.3)

    _ = hvplot.extension(PlottingBackend.bokeh)  # pyright: ignore[reportCallIssue]

    date_format = "%Y-%m-%d" if is_daily_data(df) else "%Y-%m-%d %H:%M:%S"
    REQUIRED_COLS = Candlestick.REQUIRED_COLS[:]
    plot_options = {k: v for k, v in style.items() if k in PLOT_OPTIONS}
    return (
        df.to_native()
        .hvplot.ohlc(
            REQUIRED_COLS[0],
            REQUIRED_COLS[1:-1],
            hover_cols=REQUIRED_COLS,
            tools=[
                _create_hover_tool(date_format),
                _create_crosshair_tool(),
            ],
            responsive=True,
            grid=style["grid"],
            pos_color=style["up_color"],
            neg_color=style["down_color"],
            bgcolor=style["bg_color"],
        )
        .opts(**plot_options)
    )
