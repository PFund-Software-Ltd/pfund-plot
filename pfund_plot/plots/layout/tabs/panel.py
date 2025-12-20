from __future__ import annotations
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pfund_plot.plots.lazy import LazyPlot

from panel import Tabs


__all__ = ["plot", "style", "control"]


def style(
    height: int | None = None,
    width: int | None = None,
):
    return locals()


def control(
    dynamic: bool = False,
    closable: bool = False,
    position: Literal["above", "below", "left", "right"] = "above",
):
    '''
    Args:
        dynamic: Dynamically populate only the active tab.
        closable: Whether it should be possible to close tabs.
        position: The location of the tabs relative to the tab contents.
    '''
    return locals()


def plot(*plots: LazyPlot, style: dict, control: dict) -> Tabs:
    return Tabs(
        *[plot.component for plot in plots],
        height=style["height"],
        width=style["width"],
        dynamic=control["dynamic"],
        closable=control["closable"],
        tabs_location=control["position"],
    )