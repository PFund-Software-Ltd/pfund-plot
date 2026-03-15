# pyright: reportUnknownMemberType=false, reportAttributeAccessIssue=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from panel.pane import Pane
    from panel.viewable import Viewable
    from panel.io.server import Server
    from narwhals.typing import IntoFrame
    from pfeed.feeds.market_feed import MarketFeed
    from pfund_plot.widgets.base import BaseWidget
    from pfund_plot.typing import (
        RenderedResult,
        Component,
        Plot,
        Figure,
    )
    from pfund_plot.enums import PlottingBackend, DisplayMode
    from pfund_plot.plots.plot import BasePlot

import panel as pn


class LazyRow(pn.Row):
    """A pn.Row subclass that supports + and | operators for chaining."""

    def __add__(self, other: LazyPlot | Viewable) -> LazyRow:
        right = other.component if isinstance(other, LazyPlot) else other
        return LazyRow(*self.objects, right)

    def __or__(self, other: LazyPlot | Viewable) -> LazyColumn:
        right = other.component if isinstance(other, LazyPlot) else other
        return LazyColumn(self, right)


class LazyColumn(pn.Column):
    """A pn.Column subclass that supports + and | operators for chaining."""

    def __add__(self, other: LazyPlot | Viewable) -> LazyRow:
        right = other.component if isinstance(other, LazyPlot) else other
        return LazyRow(self, right)

    def __or__(self, other: LazyPlot | Viewable) -> LazyColumn:
        right = other.component if isinstance(other, LazyPlot) else other
        return LazyColumn(*self.objects, right)


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
    
    def opts(self, *args: Any, **kwargs: Any) -> LazyPlot:
        """Pass holoviews opts to the underlying plot.

        Example:
            candlestick.opts(multi_y=True)
            (candlestick * volume).opts(multi_y=True)
        """
        self._plot._add_opts(args, kwargs)
        return self
    
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
    def component(self) -> Component | None:
        self._plot._create()  # create pane+widgets+component
        return self._plot._component
    
    @property
    def df(self) -> IntoFrame | None:
        if self._plot._df is None:
            return None
        return self._plot._df.to_native()
    
    @property
    def feed(self) -> MarketFeed | None:
        return self._plot._feed
    
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

    def backend(self, backend: PlottingBackend | str) -> LazyPlot:
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

    def get_backend(self) -> PlottingBackend:
        return self._plot._backend

    def mode(self, mode: DisplayMode | Literal['notebook', 'browser', 'desktop']) -> LazyPlot:
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

    def get_mode(self) -> DisplayMode:
        return self._plot._mode
    
    @property
    def reactive_widgets(self) -> dict[str, Any]:
        """Access the auto-created Panel widgets for customization.

        Returns:
            dict mapping parameter names to Panel widget instances.
            Empty dict if reactive params weren't provided or component not yet created.
        """
        return self._plot._reactive_widgets

    def remove_widgets(self, *WidgetClasses: type[BaseWidget]) -> LazyPlot:
        """Remove widgets from the plot.

        Args:
            *WidgetClasses: The widget classes to remove.

        Returns:
            Self for method chaining
        """
        self._plot._remove_widgets(*WidgetClasses)
        return self
    
    def _get_existing_server(self) -> Server | None:
        renderer = self._plot._renderer
        server = renderer.server
        # server is already running, return it
        # happens when in notebook envs, somehow _repr_mimebundle_ and _repr_html_ are called multiple times automatically
        # e.g. plt.ohlc(df).mode('browser')
        if server is not None:
            return server
        return None

    def show(self) -> Server | RenderedResult:
        """Explicitly render and display the plot.

        Returns:
            The rendered plot output
        """
        if self._plot._feed is not None and self._plot._notebook_type is not None:
            raise RuntimeError("Cannot render streaming plot in synchronous mode, use show_async() instead.")
        if server := self._get_existing_server():
            return server
        return self._plot._render_sync()

    async def show_async(self) -> Server | RenderedResult:
        if server := self._get_existing_server():
            return server
        return await self._plot._render_async()

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

    def __add__(self, other: LazyPlot | Viewable) -> LazyRow:
        """Combine plots horizontally using + operator.

        Args:
            other: Another LazyPlot, Panel component, or any Panel-compatible object

        Returns:
            LazyRow containing the combined components

        Example:
            plot1 + plot2  # Side by side
            plot1 + plot2 + plot3  # Three plots in a row
            plot1 + some_widget  # LazyPlot with a widget
        """
        left = self.component
        right = other.component if isinstance(other, LazyPlot) else other
        return LazyRow(left, right)

    def __radd__(self, other: Viewable) -> LazyRow:
        """Support reverse addition (when left operand doesn't support +)."""
        return LazyRow(other, self.component)

    def __mul__(self, other: LazyPlot) -> LazyPlot:
        """Overlay another plot or overlay layer onto this plot using * operator.

        Returns a new LazyPlot with the overlay appended, leaving the original unchanged.
        This allows reuse: plot * marker1 and plot * marker2 are independent.

        Args:
            other: A LazyPlot to composite onto this plot

        Returns:
            A new LazyPlot with the overlay added

        Example:
            candlestick * markers      # overlay markers on candlestick
            candlestick * volume_bars  # overlay volume on candlestick
        """
        from copy import deepcopy
        if not isinstance(other, LazyPlot):
            raise TypeError(f"Cannot overlay {type(other).__name__} onto a plot.")

        other_plot = other._plot
        current_plot = self._plot
        if other_plot.is_streaming() != current_plot.is_streaming():
            raise RuntimeError("Cannot overlay a streaming plot with a non-streaming plot.")
        if other_plot._backend != current_plot._backend:
            raise RuntimeError("Cannot overlay plots with different backends.")
        if other_plot._mode != current_plot._mode:
            raise RuntimeError("Cannot overlay plots with different modes.")
        # NOTE: deepcopy both plots so the originals are not mutated —
        # conceptually the result is a new plot instance that carries its own _overlays list.
        # The overlay must also be cloned so that _parent_plot doesn't get shared
        # when the same overlay is reused across multiple compositions.
        cloned_plot = deepcopy(self._plot)
        cloned_plot._add_overlay(deepcopy(other._plot))
        return LazyPlot(cloned_plot)

    def __or__(self, other: LazyPlot | Viewable) -> LazyColumn:
        """Stack plots vertically using | operator.

        Args:
            other: Another LazyPlot, Panel component, or any Panel-compatible object

        Returns:
            LazyColumn containing the stacked components

        Example:
            plot1 | plot2  # Vertically stacked
            plot1 | plot2 | plot3  # Three plots stacked
            plot1 | "Some text label"  # LazyPlot with text below
        """
        top = self.component
        bottom = other.component if isinstance(other, LazyPlot) else other
        return LazyColumn(top, bottom)

    def __ror__(self, other: Viewable) -> LazyColumn:
        """Support reverse or (when left operand doesn't support |)."""
        return LazyColumn(other, self.component)
