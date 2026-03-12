# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from holoviews.core.overlay import Overlay

import narwhals as nw

from pfund_plot.enums import PlottingBackend


__all__ = ["plot", "style", "control"]


DEFAULT_HEIGHT = 280
DEFAULT_NUM_DATA = 150


def style(
    title: str = "",
    xlabel: str = "date",
    ylabel: str = "price",
    pos_color: str = "green",
    neg_color: str = "red",
    bg_color: str = '',  # empty string by default because Panel will automatically use the theme color
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
    show_volume: bool = True,
    datetime_precision: Literal["d", "s", "ms"] = "s",
):
    """
    Args:
        num_data: the initial number of data points to display.
            This can be changed by a slider in the plot.
        max_data: the maximum number of data points kept in memory.
            If None, data will continue to grow unbounded.
        slider_step: the step size of the datetime range slider. if None, it will be derived from the data.
        widgets: whether to show widgets (datetime range, ticker select, etc.). default is True.
            For granular control, use remove_widgets() to remove specific widget classes.
        linked_axes: whether to link the axes of bokeh plots inside this pane across a panel layout.
            i.e. when multiple plots are placed in a layout (plt.layout(...)), the axes of the plots will be linked.
        incremental_update: whether to update the plot even when the bar is incomplete during streaming. default is True.
        update_interval: the interval in milliseconds to update the plot during streaming. default is 5000 ms.
        show_volume: whether to show the volume plot. default is True.
        datetime_precision: the precision of datetime formatting on the hover tooltip.
            "d" for days (%Y-%m-%d), "s" for seconds (default, %Y-%m-%d %H:%M:%S), "ms" for milliseconds (%Y-%m-%d %H:%M:%S.%3N).
    """
    return locals()


def plot(df: nw.DataFrame[Any], style: dict[str, Any], control: dict[str, Any], **kwargs: Any) -> Overlay:
    '''
    Args:
        df: the dataframe to plot
        style: the style of the plot
        kwargs: additional keyword arguments (not used in this plot) to be compatible with other plots
            - x: the column name of the x-axis
            - y: the column name of the y-axis
            - control: the control of the plot
    '''
    import hvplot
    from bokeh.models import HoverTool, CrosshairTool
    from pfund_plot.plots.candlestick import Candlestick
    from pfund_plot.utils.bokeh import create_number_formatter_for_hover_tool, get_datetime_hover_format

    def _create_hover_tool() -> HoverTool:
        date_format = get_datetime_hover_format(control["datetime_precision"])
        num_formatter = create_number_formatter_for_hover_tool()
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

    _ = hvplot.extension(PlottingBackend.bokeh)

    REQUIRED_COLS = Candlestick.REQUIRED_COLS[:]
    return (
        df.to_native()
        .hvplot.ohlc(
            REQUIRED_COLS[0],
            REQUIRED_COLS[1:-1],
            hover_cols=REQUIRED_COLS,
            tools=[
                _create_hover_tool(),
                _create_crosshair_tool(),
            ],
            responsive=True,
            grid=style["grid"],
            pos_color=style["pos_color"],
            neg_color=style["neg_color"],
            bgcolor=style["bg_color"],
        )
        .opts(
            title=style["title"],
            xlabel=style["xlabel"],
            ylabel=style["ylabel"],
            height=style["height"],
        )
    )
