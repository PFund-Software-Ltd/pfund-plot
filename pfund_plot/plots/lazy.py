from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from panel.pane import Pane
    from panel.io.server import Server
    from pfund_plot._typing import (
        RenderedResult,
        tPlottingBackend,
        tDisplayMode,
        Component,
        Plot,
        Figure,
    )

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class LazyPlot:
    """Lazy plot builder that defers rendering until display.

    Enables method chaining for configuring plots:
        plt.ohlc(df).style(height=600, width=800).control(num_data=100)

    Auto-renders when displayed in notebooks or at end of scripts.
    """

    def __init__(self, plot_instance: BasePlot):
        self._plot = plot_instance
    
    @property
    def name(self) -> str:
        return self._plot.name
    
    @property
    def figure(self) -> Figure:
        import hvplot
        from holoviews.core.overlay import Overlay
        from anywidget import AnyWidget
        
        plot = self.plot
        backend = self._plot._backend
        if isinstance(plot, Overlay):
            fig = hvplot.render(plot, backend=backend)
            if backend != PlottingBackend.plotly:
                return fig
            else:
                import plotly.graph_objects as go
                return go.Figure(fig)
        elif isinstance(plot, AnyWidget):
            return plot
        else:
            raise ValueError(f"Unsupported plot type: {type(plot)}")

    @property
    def plot(self) -> Plot:
        return self._plot.plot
    
    @property
    def pane(self) -> Pane:
        if self._plot._pane is None:
            self._plot._create_plot()
        return self._plot._pane

    @property
    def component(self) -> Component:
        if self._plot._component is None:
            self._plot._create_component()
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
