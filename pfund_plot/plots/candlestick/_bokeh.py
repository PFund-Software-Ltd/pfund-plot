from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from narwhals.typing import Frame
    from holoviews.core.overlay import Overlay

from bokeh.models import HoverTool, CrosshairTool


__all__ = ["plot", "style", "control"]
PLOT_OPTIONS = [
    "title",
    "xlabel",
    "ylabel",
    "height",
]  # specified options supported in .opts()
DEFAULT_HEIGHT = 280
DEFAULT_NUM_DATA = 150
DEFAULT_SLIDER_STEP = 3_600_000  # 1 hour in milliseconds


def style(
    title: str = "Candlestick Chart",
    xlabel: str = "Date",
    ylabel: str = "Price",
    up_color: str = "green",
    down_color: str = "red",
    bg_color: str = "white",
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
        up_color: the color of the up candle, hex code is supported
        down_color: the color of the down candle, hex code is supported
        bg_color: the background color of the plot, hex code is supported
        total_height: the height of the component (including the figure + widgets)
            Default is None, when it is None, Panel will automatically adjust its height
        height: the height of the figure
        width: the width of the plot
    """
    return locals()


def control(
    num_data: int = DEFAULT_NUM_DATA,
    slider_step: int = DEFAULT_SLIDER_STEP,
    show_volume: bool = True,
):
    """
    Args:
        num_data: the initial number of data points to display.
            This can be changed by a slider in the plot.
        slider_step: the step size of the datetime range slider. default is 60 min (3600000 ms).
        show_volume: whether to show the volume plot. default is True.
    """
    return locals()


def plot(df: Frame, style: dict, control: dict) -> Overlay:
    import hvplot
    from pfund_plot.plots.candlestick import Candlestick
    from pfund_plot.utils.utils import is_daily_data
    from pfund_plot.enums import PlottingBackend

    def _create_hover_tool(date_format: str) -> HoverTool:
        return HoverTool(
            tooltips=[
                ("date", f"@date{{{date_format}}}"),
                ("open", "@open"),
                ("high", "@high"),
                ("low", "@low"),
                ("close", "@close"),
                ("volume", "@volume"),
            ],
            formatters={"@date": "datetime"},
            mode="vline",
        )


    def _create_crosshair_tool():
        return CrosshairTool(dimensions="height", line_color="gray", line_alpha=0.3)

    hvplot.extension(PlottingBackend.bokeh)

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
            grid=style["grid"],
            pos_color=style["up_color"],
            neg_color=style["down_color"],
            responsive=True,
            bgcolor=style["bg_color"],
        )
        .opts(**plot_options)
    )
