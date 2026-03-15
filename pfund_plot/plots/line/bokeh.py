# pyright: reportUnusedParameter=false, reportArgumentType=false
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
        color: the color of the line, hex code is supported, only used when there is only one line
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
    from holoviews import opts
    from bokeh.models import HoverTool, CrosshairTool, CustomJSHover
    from pfund_plot.utils.bokeh import create_number_formatter_for_hover_tool, get_datetime_hover_format
    from pfund_plot.plots.line import Line

    def _create_crosshair_tool():
        return CrosshairTool(dimensions="height", line_color="gray", line_alpha=0.3)

    def _create_hover_config(
        x_col: str | None,
        y_cols: list[str],
    ) -> tuple[list[tuple[str, str]], dict[str, str | CustomJSHover]]:
        num_formatter = create_number_formatter_for_hover_tool()
        tooltips: list[tuple[str, str]] = []
        formatters: dict[str, str | CustomJSHover] = {}
        schema = df.collect_schema()
        if x_col is not None:
            x_dtype = schema[x_col]
            is_x_datetime = 'datetime' in str(x_dtype).lower() or 'date' in str(x_dtype).lower()
            is_x_numeric = x_dtype.is_numeric()
            if is_x_datetime:
                date_format = get_datetime_hover_format(control["datetime_precision"])
                tooltips.append((x_col, f"@{{{x_col}}}{{{date_format}}}"))
                formatters[f"@{{{x_col}}}"] = "datetime"
            elif is_x_numeric:
                tooltips.append((x_col, f"@{{{x_col}}}{{custom}}"))
                formatters[f"@{{{x_col}}}"] = num_formatter
            else:
                tooltips.append((x_col, f"@{{{x_col}}}"))
        for col in y_cols:
            col_dtype = schema[col]
            if col_dtype.is_numeric():
                tooltips.append((col, f"@{{{col}}}{{custom}}"))
                formatters[f"@{{{col}}}"] = num_formatter
            else:
                tooltips.append((col, f"@{{{col}}}"))
        return tooltips, formatters

    def _create_hover_tool(x_col: str | None, y_cols: list[str]) -> HoverTool:
        tooltips, formatters = _create_hover_config(x_col, y_cols)
        return HoverTool(tooltips=tooltips, formatters=formatters, mode="vline")

    def _create_multiline_hover_opts(x_col: str | None, y_cols: list[str]):
        tooltips, formatters = _create_hover_config(x_col, y_cols)
        return opts.Curve(
            tools=["hover"],
            hover_mode="vline",
            hover_tooltips=[("series", "@{Variable}"), *tooltips],
            hover_formatters=formatters,
        )
    
    _ = hvplot.extension(PlottingBackend.bokeh)

    # resolve x and y column names
    x_col = Line._derive_x_col(df, x)
    y_cols = Line._derive_y_cols(df, x, y)

    is_single_line = len(y_cols) == 1
    if is_single_line:
        tools = [
            _create_hover_tool(x_col, y_cols),
            _create_crosshair_tool()
        ]
    else:
        tools = [_create_crosshair_tool()]

    line_kwargs: dict[str, Any] = {
        "responsive": True,
    }
    if is_single_line:
        line_kwargs["color"] = style["color"]
    else:
        line_kwargs["hover_cols"] = y_cols

    plot = (
        df.to_native()
        .hvplot.line(
            x=x,
            y=y,
            tools=tools,
            grid=style["grid"],
            bgcolor=style["bg_color"],
            **line_kwargs,
        )
        .opts(
            title=style["title"],
            xlabel=style["xlabel"],
            ylabel=style["ylabel"],
            height=style["height"],
        )
    )
    if not is_single_line:
        plot = plot.opts(_create_multiline_hover_opts(x_col, y_cols))

    return plot