from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from pfund_plot._typing import tFigure

from contextlib import contextmanager

from panel.layout.gridstack import GridStack
   
from pfund_plot.state import state
from pfund_plot.renderer import render


__all__ = ['layout']


@contextmanager
def layout(
    streaming: bool = False,
    mode: Literal['browser', 'desktop'] = 'browser', 
    num_cols: int = 3,
    allow_drag: bool = True,
    # FIXME: plots can't be resized when using GridStack, not sure if it's a bottleneck or a bug
    # allow_resize: bool = True,
):
    assert mode.lower() in ['browser', 'desktop'], "mode must be 'browser' or 'desktop'"

    # Setup state
    state.layout.in_layout = True
    state.layout.streaming = streaming
    state.layout.components = []
    
    try:
        yield state.layout
    finally:
        components = state.layout.components
        return _layout_plot(
            *components,
            mode=mode,
            num_cols=num_cols,
            allow_drag=allow_drag,
            # allow_resize=allow_resize,
        )
    

def _layout_plot(
    *figs: tFigure,
    mode: Literal['browser', 'desktop'] = 'browser',
    num_cols: int = 3,
    allow_drag: bool = True,
    # allow_resize: bool = False,
):
    if not state.layout.in_layout:
        raise ValueError("layout_plot() must be called within a layout context manager")
        
    gstack = GridStack(
        sizing_mode='stretch_both',
        allow_drag=allow_drag,
        allow_resize=False,
    )

    # standardize the figures
    max_height = max(fig.height or 0 for fig in figs)
    for fig in figs:
        fig.param.update(height=max_height, width=None, sizing_mode='stretch_width')
    
    num_figs = len(figs)
    # num_rows = math.ceil(num_figs / num_cols)
    for i in range(num_figs):
        gstack[i // num_cols, i % num_cols] = figs[i]

    periodic_callbacks = state.layout.periodic_callbacks
    state.reset_layout()
    return render(gstack, mode, periodic_callbacks=periodic_callbacks)
