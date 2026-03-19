# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from holoviews.core.overlay import Overlay

import narwhals as nw

from pfund_plot.enums import PlottingBackend


__all__ = ["plot", "style", "control"]


# Marker mapping from user-friendly names to Bokeh scatter types
MARKER_MAP = {
    'triangle_up': 'triangle',
    'triangle_down': 'inverted_triangle',
}

DEFAULT_MARKER = 'circle'
DEFAULT_SIZE = 100  # hvplot takes sqrt(size), so 100 -> rendered size of 10
DEFAULT_COLOR = 'steelblue'
DEFAULT_HEIGHT = 280


def style(
    title: str = "Scatter",
    xlabel: str = "",
    ylabel: str = "",
    color: str = DEFAULT_COLOR,
    marker: Literal['circle', 'square', 'triangle_up', 'triangle_down', 'diamond', 'cross', 'x', 'star'] | str = DEFAULT_MARKER,
    size: int | str = DEFAULT_SIZE,
    opacity: float = 0.8,
    grid: bool = False,
    total_height: int | None = None,
    height: int = DEFAULT_HEIGHT,
    width: int | None = None,
):
    """
    Args:
        title: the title of the plot
        xlabel: the label of the x-axis
        ylabel: the label of the y-axis
        color: Column name for per-point color, or a literal color string
        marker: Column name for per-point marker, or a literal marker string.
            Supported markers: circle, square, triangle_up, triangle_down,
            diamond, cross, x, star
        size: Point size. Either a fixed int (e.g. size=15) for uniform sizing,
            or a column name (e.g. size='volume') for per-point sizing from data.
        opacity: scatter opacity (0.0 to 1.0)
        grid: whether to show the grid
        total_height: the height of the component (including the figure + widgets).
            Default is None, Panel will automatically adjust its height.
        height: the height of the figure
        width: the width of the plot, since the plot is responsive, this is only used in panel layout
    """
    return locals()


def control(
    num_data: int | None = None,
    slider_step: int | None = None,
    widgets: bool = True,
    linked_axes: bool = True,
    include_extra_cols: bool = False,
):
    """
    Args:
        num_data: (DatetimeRangeWidget) initial number of most recent data points to display.
        slider_step: (DatetimeRangeWidget) step size in ms for the datetime range slider.
            If None, derived from data resolution.
        widgets: whether to show widgets. default is True.
            For granular control, use remove_widgets() to remove specific widget classes.
        linked_axes: whether to link axes across plots in a layout (plt.layout(...)).
        include_extra_cols: whether to include extra columns in the hover tooltip.
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

    _ = hvplot.extension(PlottingBackend.bokeh)

    color = style['color']
    marker = style['marker']
    size = style['size']

    columns = df.columns

    if control['include_extra_cols']:
        exclude: set[str] = set()
        if x:
            exclude.add(x)
        if isinstance(y, list):
            exclude.update(y)
        elif y:
            exclude.add(y)
        kwargs['hover_cols'] = [c for c in columns if c not in exclude]

    color_is_col = isinstance(color, str) and color in columns
    size_is_col = isinstance(size, str) and size in columns
    marker_is_col = isinstance(marker, str) and marker in columns

    if color_is_col:
        kwargs['c'] = color
    else:
        kwargs['color'] = color

    if size_is_col:
        kwargs['s'] = size
    else:
        kwargs['size'] = size
    
    if marker_is_col:
        df = df.with_columns(nw.col(marker).replace_strict(MARKER_MAP, default=nw.col(marker)))
        kwargs['marker'] = marker
    else:
        kwargs['marker'] = MARKER_MAP.get(marker, marker)


    return (
        df.to_native().hvplot.scatter(
            x=x,
            y=y,
            responsive=True,
            alpha=style['opacity'],
            grid=style['grid'],
            **kwargs,
        )
        .opts(
            title=style['title'],
            xlabel=style['xlabel'],
            ylabel=style['ylabel'],
            height=style['height'],
        )
    )

