from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from panel.pane import Pane
    from panel.io.server import Server
    from pfund_plot.typing import (
        RenderedResult,
        tPlottingBackend,
        tDisplayMode,
        Component,
        Plot,
        Figure,
    )

from pfund_plot.plots.plot import BasePlot


class LazyPlot:
    """Lazy plot builder that defers rendering until display.

    Enables method chaining for configuring plots:
        plt.ohlc(df).style(height=600, width=800).control(num_data=100)

    Auto-renders when displayed in notebooks or at end of scripts.
    """

    def __init__(self, plot_instance: BasePlot):
        self._plot = plot_instance
        self._grid_spec: tuple[slice, slice] | None = None
    
    def __getitem__(self, key: tuple[int | slice, int | slice]) -> LazyPlot:
        """Set grid position for use with plt.layout (GridStack).

        Args:
            key: A tuple of two elements (row, col) specifying the grid position.
                 Each element can be an int (single position) or slice (range).
                 Examples: [1, 3], [1:2, 3:4], [1, 3:5]

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df)[0, 0]         # single cell at row 0, col 0
            plt.ohlc(df)[0:2, 0:6]     # spans rows 0-1, cols 0-5
            plt.ohlc(df)[1, 0:3]       # row 1, cols 0-2
            plt.layout(plot1[0:1, 0:2], plot2[0:1, 2:4])
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError("Grid spec must be a tuple of two elements, e.g., [1, 3] or [1:2, 3:4]")
        row_spec, col_spec = key
        if not isinstance(row_spec, (int, slice)) or not isinstance(col_spec, (int, slice)):
            raise TypeError("Grid spec elements must be int or slice, e.g., [1, 3] or [1:2, 3:4]")

        # Convert ints to slices for consistency
        row_slice = slice(row_spec, row_spec + 1) if isinstance(row_spec, int) else row_spec
        col_slice = slice(col_spec, col_spec + 1) if isinstance(col_spec, int) else col_spec

        self._grid_spec = (row_slice, col_slice)
        return self

    @property
    def name(self) -> str:
        return self._plot.name
    
    @property
    def figure(self) -> Figure:
        return self._plot.figure

    @property
    def plot(self) -> Plot:
        if self._plot._plot is None:
            self._plot._create_plot()
        return self._plot._plot
    
    @property
    def pane(self) -> Pane:
        if self._plot._pane is None:
            self._plot._create_pane()
        return self._plot._pane
    
    @property
    def widgets(self) -> Any:
        if self._plot._widgets is None:
            self._plot._create_widgets()
        return self._plot._widgets

    @property
    def component(self) -> Component:
        self._plot._create()  # create pane+widgets+component
        return self._plot._component
    
    def style(self, **kwargs) -> LazyPlot:
        """Configure style options.

        Args:
            **kwargs: Style parameters (e.g., height, width, colors, etc.)

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).style(height=600, width=800)
        """
        self._plot._set_style(kwargs)
        return self
    
    def get_style(self) -> dict:
        return self._plot._style
    
    def control(self, **kwargs) -> LazyPlot:
        """Configure control options.

        Args:
            **kwargs: Control parameters (e.g., num_data, etc.)

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).control(num_data=100)
        """
        self._plot._set_control(kwargs)
        return self
    
    def get_control(self) -> dict:
        return self._plot._control

    def backend(self, backend: tPlottingBackend) -> LazyPlot:
        """Override backend for this plot only.

        Args:
            backend: Backend to use ('bokeh' or 'svelte')

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).backend('svelte').show()
        """
        self._plot._set_backend(backend)
        return self

    def get_backend(self) -> tPlottingBackend:
        return self._plot._backend

    def mode(self, mode: tDisplayMode) -> LazyPlot:
        """Override display mode for this plot only.

        Args:
            mode: Display mode ('notebook', 'browser', or 'desktop')

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).mode('browser').show()
        """
        self._plot._set_mode(mode)
        return self

    def get_mode(self) -> tDisplayMode:
        return self._plot._mode

    def show(self) -> Server | RenderedResult:
        """Explicitly render and display the plot.

        Use this in browser/desktop mode or when you want explicit control.
        In notebooks, auto-rendering happens via _repr_mimebundle_.

        Returns:
            The rendered plot output
        """
        renderer = self._plot._renderer
        server = renderer.server
        # server is already running, return it
        # happens when in notebook envs, somehow _repr_mimebundle_ and _repr_html_ are called multiple times automatically
        # e.g. plt.ohlc(df).mode('browser')
        if server is not None:
            return server
        return self._plot._render()

    def servable(self, title: str | None = None) -> Component:
        """Mark the plot as servable for use with `panel serve` CLI.

        Use this when running with: panel serve myfile.py --show --autoreload

        Args:
            title: Optional title for the browser tab

        Returns:
            The servable component

        Example:
            fig = plt.ohlc(df).backend('bokeh')
            fig.servable()
        """
        return self.component.servable(title=title)

    def _repr_mimebundle_(self, include=None, exclude=None) -> dict[str, Any]:
        """Auto-render in Jupyter/IPython notebooks.

        This magic method is called when the object is the last expression
        in a notebook cell, enabling auto-display without explicit render().
        """
        result = self.show()
        if hasattr(result, "_repr_mimebundle_"):
            return result._repr_mimebundle_(include, exclude)
        return {}

    def _repr_html_(self) -> str | None:
        """Fallback HTML representation for notebooks."""
        result = self.show()
        if hasattr(result, "_repr_html_"):
            return result._repr_html_()
        return None
