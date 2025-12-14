from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pfund_plot._typing import (
        Output,
        tPlottingBackend,
        tDisplayMode,
        Component,
        WrappedPlot,
        WrappedFigure,
        RawFigure,
    )

from pfund_plot.plots.plot import Plot
from pfund_plot.enums import PlottingBackend


class LazyPlot:
    """Lazy plot builder that defers rendering until display.

    Enables method chaining for configuring plots:
        plt.ohlc(df).style(height=600, width=800).control(num_data=100)

    Auto-renders when displayed in notebooks or at end of scripts.
    """

    def __init__(self, plot_instance: Plot):
        self._plot_instance = plot_instance
    
    @property
    def name(self) -> str:
        return self._plot_instance.name
    
    @property
    def raw_figure(self) -> RawFigure:
        import hvplot
        from holoviews.core.overlay import Overlay
        from anywidget import AnyWidget
        
        fig = self.figure
        backend = self._plot_instance._backend
        if isinstance(fig, Overlay):
            raw_fig = hvplot.render(fig, backend=backend)
            if backend != PlottingBackend.plotly:
                return raw_fig
            else:
                import plotly.graph_objects as go
                return go.Figure(raw_fig)
        elif isinstance(fig, AnyWidget):
            return fig
        else:
            raise ValueError(f"Unsupported figure type: {type(fig)}")

    @property
    def figure(self) -> WrappedFigure:
        return self._plot_instance.figure
    
    @property
    def plot(self) -> WrappedPlot:
        if self._plot_instance._plot is None:
            self._plot_instance._create_plot()
        return self._plot_instance._plot

    @property
    def component(self) -> Component:
        if self._plot_instance._component is None:
            self._plot_instance._create_component()
        return self._plot_instance._component
    
    def style(self, **kwargs) -> LazyPlot:
        """Configure style options.

        Args:
            **kwargs: Style parameters (e.g., height, width, colors, etc.)

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).style(height=600, width=800)
        """
        self._plot_instance._set_style(kwargs)
        return self

    def control(self, **kwargs) -> LazyPlot:
        """Configure control options.

        Args:
            **kwargs: Control parameters (e.g., num_data, etc.)

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).control(num_data=100)
        """
        self._plot_instance._set_control(kwargs)
        return self

    def backend(self, backend: tPlottingBackend) -> LazyPlot:
        """Override backend for this plot only.

        Args:
            backend: Backend to use ('bokeh' or 'svelte')

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).backend('svelte').show()
        """
        self._plot_instance._set_backend(backend)
        return self

    def mode(self, mode: tDisplayMode) -> LazyPlot:
        """Override display mode for this plot only.

        Args:
            mode: Display mode ('notebook', 'browser', or 'desktop')

        Returns:
            Self for method chaining

        Example:
            plt.ohlc(df).mode('browser').show()
        """
        self._plot_instance._set_mode(mode)
        return self

    def show(self) -> Output:
        """Explicitly render and display the plot.

        Use this in browser/desktop mode or when you want explicit control.
        In notebooks, auto-rendering happens via _repr_mimebundle_.

        Returns:
            The rendered plot output
        """
        return self._plot_instance._render()

    def _repr_mimebundle_(self, include=None, exclude=None) -> dict[str, Any] | None:
        """Auto-render in Jupyter/IPython notebooks.

        This magic method is called when the object is the last expression
        in a notebook cell, enabling auto-display without explicit render().
        """
        result = self.show()
        if hasattr(result, "_repr_mimebundle_"):
            return result._repr_mimebundle_(include, exclude)
        return None

    def _repr_html_(self) -> str | None:
        """Fallback HTML representation for notebooks."""
        result = self.show()
        if hasattr(result, "_repr_html_"):
            return result._repr_html_()
        return None
