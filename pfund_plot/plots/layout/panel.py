from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pfund_plot.plots.lazy import LazyPlot

import panel as pn
from panel.layout.gridstack import GridStack


__all__ = ["plot", "style", "control"]
DEFAULT_NUM_COLS = 3


def style():
    return locals()


def control(
    num_cols: int = DEFAULT_NUM_COLS,
    allow_drag: bool = True,
    allow_resize: bool = True,
):
    return locals()


def plot(*plots: LazyPlot, style: dict, control: dict) -> GridStack:
    gstack = GridStack(
        sizing_mode="stretch_both",
        allow_drag=control["allow_drag"],
        allow_resize=control["allow_resize"],
    )

    grid_specs = [plot._grid_spec for plot in plots]
    if all(grid_spec is not None for grid_spec in grid_specs):
        for plot, grid_spec in zip(plots, grid_specs):
            row_slice, col_slice = grid_spec
            gstack[row_slice, col_slice] = plot.component
    else:
        num_plots = len(plots)
        num_cols = control["num_cols"]
        # num_rows = math.ceil(num_plots / num_cols)
        for i in range(num_plots):
            gstack[i // num_cols, i % num_cols] = plots[i].component
    return gstack
