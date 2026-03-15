# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from holoviews import Element
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
    title: str = "",
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
):
    """
    Args:
        num_data: (DatetimeRangeWidget) initial number of most recent data points to display.
        slider_step: (DatetimeRangeWidget) step size in ms for the datetime range slider.
            If None, derived from data resolution.
        widgets: whether to show widgets. default is True.
            For granular control, use remove_widgets() to remove specific widget classes.
        linked_axes: whether to link axes across plots in a layout (plt.layout(...)).
    """
    return locals()


def plot(
    df: nw.DataFrame[Any],
    x: str,
    y: str,
    style: dict[str, Any],
    **kwargs: Any,
) -> Element | Overlay:
    import hvplot

    _ = hvplot.extension(PlottingBackend.bokeh)

    color = style['color']
    marker = style['marker']
    size = style['size']

    columns = df.columns

    scatter_kwargs: dict[str, Any] = {
        'alpha': style['opacity'],
        'responsive': True,
        'grid': style['grid'],
        # Collect extra columns for hover tooltip
        'hover_cols': [c for c in columns if c not in (x, y)],
    }

    color_is_col = isinstance(color, str) and color in columns
    size_is_col = isinstance(size, str) and size in columns
    marker_is_col = isinstance(marker, str) and marker in columns

    if color_is_col:
        scatter_kwargs['c'] = color
    else:
        scatter_kwargs['color'] = color

    if size_is_col:
        scatter_kwargs['s'] = size
    else:
        scatter_kwargs['size'] = size
    
    if marker_is_col:
        df = df.with_columns(nw.col(marker).replace_strict(MARKER_MAP, default=nw.col(marker)))
        scatter_kwargs['marker'] = marker
    else:
        scatter_kwargs['marker'] = MARKER_MAP.get(marker, marker)


    scatter = (
        df.to_native().hvplot.scatter(
            x=x,
            y=y,
            **scatter_kwargs,
        )
        .opts(
            title=style['title'],
            xlabel=style['xlabel'],
            ylabel=style['ylabel'],
            height=style['height'],
        )
    )

    return scatter
