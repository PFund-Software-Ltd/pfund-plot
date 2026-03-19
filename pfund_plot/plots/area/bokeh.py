# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from holoviews.core.overlay import NdOverlay

import narwhals as nw

from pfund_plot.enums import PlottingBackend


__all__ = ["plot", "style", "control"]


DEFAULT_COLOR = "steelblue"
DEFAULT_HEIGHT = 280


def style(
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = DEFAULT_COLOR,
    alpha: float = 0.5,
    marker: Literal['circle', 'square', 'triangle_up', 'triangle_down', 'diamond', 'cross', 'x', 'star'] | None = None,
    stacked: bool = True,
    bg_color: str = '',  # empty string by default because Panel will automatically use the theme color
    grid: bool = False,
    total_height: int | None = None,
    height: int = DEFAULT_HEIGHT,
    width: int | None = None,
):
    '''
    Args:
        title: the title of the plot
        xlabel: the label of the x-axis
        ylabel: the label of the y-axis
        color: the color of the plot, hex code is supported, only used when there is only one area chart
        alpha: the alpha of the plot, 0.0 to 1.0
        marker: marker shape for data points. None hides markers, any value shows them.
            Default is None (hidden). Options: 'circle', 'square', 'triangle_up',
            'triangle_down', 'diamond', 'cross', 'x', 'star'.
        stacked: Whether to stack multiple areas. Default is True.
        bg_color: the background color of the plot, hex code is supported
        total_height: the height of the component (including the figure + widgets)
            Default is None, when it is None, Panel will automatically adjust its height
        height: the height of the figure
        width: the width of the plot, since the plot is responsive, this is only used in panel layout
        grid: whether to show the grid
    '''
    return locals()


def control(
    num_data: int | None = None,
    max_data: int | None = None,
    slider_step: int | None = None,
    widgets: bool = True,
    linked_axes: bool = True,
    update_interval: int = 5000,  # ms
    incremental_update: bool = True,
    datetime_precision: Literal["d", "s", "ms"] = "s",
):
    """
    Args:
        num_data: (DatetimeRangeWidget) initial number of most recent data points to display.
        max_data: (streaming) maximum number of data points kept in memory.
            If None, data will continue to grow unbounded.
        slider_step: (DatetimeRangeWidget) step size in ms for the datetime range slider.
            If None, derived from data resolution.
        widgets: whether to show widgets. default is True.
            For granular control, use remove_widgets() to remove specific widget classes.
        linked_axes: whether to link axes across plots in a layout (plt.layout(...)).
        incremental_update: (streaming) whether to update even when the bar is incomplete. default is True.
        update_interval: (streaming) interval in ms to update the plot. default is 5000 ms.
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
) -> NdOverlay:
    import hvplot
    from bokeh.models import CrosshairTool
    from pfund_plot.plots.area import Area

    _ = hvplot.extension(PlottingBackend.bokeh)

    # resolve y column names
    x_col = x
    y_cols = Area._derive_y_cols(df, x, y)
    datetime_precision = control["datetime_precision"]

    crosshair_tool = CrosshairTool(dimensions="height", line_color="gray", line_alpha=0.3)

    if len(y_cols) == 1:
        kwargs["color"] = style["color"]

    area_plot = (
        df.to_native().hvplot.area(
            x=x,
            y=y,
            tools=[crosshair_tool],
            grid=style["grid"],
            bgcolor=style["bg_color"],
            stacked=style["stacked"],
            alpha=style["alpha"],
            responsive=True,
            # Disable hvplot's built-in hover (shows "???") because hvplot converts
            # area to Patch polygons, destroying original column data in ColumnDataSource
            hover=False,
            **kwargs,
        )
        .opts(
            title=style["title"],
            xlabel=style["xlabel"],
            ylabel=style["ylabel"],
            height=style["height"],
        )
    )

    # NOTE: this is not needed if hvplot has fixed the tooltip issue in area plot
    # Overlay invisible scatter points that carry the real data for hover tooltips
    from pfund_plot.utils.bokeh import create_hover_scatter
    hover_scatter = create_hover_scatter(df, x_col, y_cols, datetime_precision, marker=style.get("marker"))
    return area_plot * hover_scatter