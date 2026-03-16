# pyright: reportUnusedParameter=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from holoviews.core.overlay import Overlay

import narwhals as nw

from pfund_plot.enums import PlottingBackend


__all__ = ["plot", "style", "control"]


DEFAULT_COLOR = 'black'
DEFAULT_FONT_SIZE = '10pt'
DEFAULT_HEIGHT = 280


def style(
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = DEFAULT_COLOR,
    font_size: str = DEFAULT_FONT_SIZE,
    text_align: Literal['left', 'center', 'right'] = 'center',
    total_height: int | None = None,
    height: int = DEFAULT_HEIGHT,
    width: int | None = None,
):
    """
    Args:
        title: the title of the plot
        xlabel: the label of the x-axis
        ylabel: the label of the y-axis
        color: text color
        font_size: text font size (e.g. '10pt', '12px')
        text_align: horizontal text alignment ('left', 'center', 'right')
        total_height: the height of the component (including the figure + widgets).
            Default is None, Panel will automatically adjust its height.
        height: the height of the figure
        width: the width of the plot, since the plot is responsive, this is only used in panel layout
    """
    return locals()


def control(
    widgets: bool = True,
    linked_axes: bool = True,
):
    """
    Args:
        widgets: whether to show widgets. default is True.
        linked_axes: whether to link axes across plots in a layout (plt.layout(...)).
    """
    return locals()


def plot(
    df: nw.DataFrame[Any],
    x: str | None,
    y: str | list[str] | None,
    text: str,
    style: dict[str, Any],
    **kwargs: Any,
) -> Overlay:
    import hvplot

    _ = hvplot.extension(PlottingBackend.bokeh)

    return (
        df.to_native().hvplot.labels(
            x=x,
            y=y,
            text=text,
            responsive=True,
        )
        .opts(
            title=style['title'],
            xlabel=style['xlabel'],
            ylabel=style['ylabel'],
            height=style['height'],
            text_color=style['color'],
            text_font_size=style['font_size'],
            text_align=style['text_align'],
        )
    )
