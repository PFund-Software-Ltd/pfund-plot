from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import Frame
    from pfeed.typing import GenericFrame
    from pfund_plot.plots.lazy import LazyPlot

import panel as pn

import pfund_plot as plt
from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class LayoutStyle:
    from pfund_plot.plots.layout.panel import style as panel_style
    
    panel = panel_style

class LayoutControl:
    from pfund_plot.plots.layout.panel import control as panel_control
    
    panel = panel_control
    

class Layout(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.panel]
    _MAX_COLS = 12  # maximum number of columns in a grid when using GridStack

    style = LayoutStyle
    control = LayoutControl

    def __init__(self, *plots: LazyPlot):
        pn.extension("gridstack")

        self._plots: tuple[LazyPlot, ...] = plots
        super().__init__(df=None, streaming_feed=None)
        if self._notebook_type:
            raise ValueError("Layout cannot be used in notebook environment.")

    # just a layout of plots, it has no data for itself to standardize
    def _standardize_df(self, df: GenericFrame) -> Frame:
        return df
    
    # no widgets for layout
    def _create_widgets(self):
        pass

    def _validate_grid_specs(self):
        # Check grid_spec consistency: either all plots have it or none do
        grid_specs = [plot._grid_spec for plot in self._plots]
        has_grid_spec = [grid_spec is not None for grid_spec in grid_specs]
        all_has_grid_spec = all(has_grid_spec)
        if any(has_grid_spec):
            if not all_has_grid_spec:
                raise ValueError("All plots must have grid_spec defined if any do.")
            else:
                # REVIEW: somehow when column index exceeds 12, GridStack doesn't work, columns must be within 0-12
                if any(grid_spec[1].stop is not None and grid_spec[1].stop > self._MAX_COLS for grid_spec in grid_specs):
                    raise ValueError(f"Column index exceeds maximum of {self._MAX_COLS}. Grid uses a {self._MAX_COLS}-column system.")
        assert self._control['num_cols'] <= self._MAX_COLS, f"'num_cols' must be less than or equal to {self._MAX_COLS}"

    def _create_component(self):
        self._validate_grid_specs()
        self._component = self._plot(*self._plots, style=self._style, control=self._control)


# TODO: where to put this?
plt.dashboard = lambda *plots: Layout(*plots).mode('browser').show()