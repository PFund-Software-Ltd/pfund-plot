# pyright: reportUnusedParameter=false, reportArgumentType=false
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from pfund_plot.plots.lazy import LazyPlot
    from pfund_plot.typing import RawFigure

from panel import Tabs

__all__ = ["control", "plot", "style"]


def style(
    height: int | None = None,
    width: int | None = None,
):
    return locals()


def control(
    dynamic: bool = False,
    closable: bool = False,
    position: Literal["above", "below", "left", "right"] = "above",
    linked_axes: bool = True,
):
    """
    Args:
        dynamic: Dynamically populate only the active tab.
        closable: Whether it should be possible to close tabs.
        position: The location of the tabs relative to the tab contents.
        linked_axes: Whether to link axes across plots in different tabs.
    """
    return locals()


def plot(
    *plots: LazyPlot | RawFigure,
    style: dict[str, Any],
    control: dict[str, Any],
    **kwargs: Any,
) -> Tabs:
    # In the marimo + svelte combo the plot's component is a mo.vstack (see
    # Candlestick._create_component), which carries no name, so Panel assigns a
    # default tab label like "Column01805". Panel's Tabs accepts a (name, object)
    # tuple to label a tab explicitly, so pass the plot's name in that case.
    # Every other component is a pn.Column that already carries its own name.
    items = [
        (plot.name, plot.component)
        if plot._plot._is_using_marimo_svelte_combo()
        else plot.component
        for plot in plots
    ]
    return Tabs(
        *items,
        height=style["height"],
        width=style["width"],
        dynamic=control["dynamic"],
        closable=control["closable"],
        tabs_location=control["position"],
    )
