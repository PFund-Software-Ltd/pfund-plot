from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfund_plot.types.core import tFigure
    from pfund_plot.types.literals import tDisplayMode

import panel as pn
    
from pfund_plot.renderer import render


def layout_plot(
    *figs: tFigure,
    display_mode: tDisplayMode = 'notebook',
):
    # use gridstack to layout the plots automatically
    return render(combined_fig, display_mode)
