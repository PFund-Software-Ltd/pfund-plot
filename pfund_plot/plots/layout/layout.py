from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pfund_plot.typing import RawFigure

from pfund_kit.style import cprint, RichColor, TextStyle
from pfund_plot.plots.lazy import LazyPlot
from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class BaseLayout(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.panel]
    SUPPORT_STREAMING: ClassVar[bool] = True
    REQUIRED_DATA: ClassVar[bool] = False

    def __new__(cls, *plots: LazyPlot | RawFigure):
        from pfund_plot.utils import convert_to_lazy_plot

        # Convert any plotting library figures to LazyPlot instances
        lazy_plots = tuple(
            convert_to_lazy_plot(plot) if not isinstance(plot, LazyPlot) else plot  # pyright: ignore[reportArgumentType]
            for plot in plots
        )
        # super().__new__ will call __init__ with converted_plots
        return super().__new__(cls, *lazy_plots)

    def __init__(self, *plots: LazyPlot):  # pyright: ignore[reportInconsistentConstructor]
        self._plots: tuple[LazyPlot, ...] = plots
        super().__init__(data=None)
    
    def _add_plots_periodic_callbacks(self):
        """Transfer child plots' periodic callbacks to Layout's renderer.

        Child plots inside Layout are never rendered directly — only Layout's
        renderer gets render() called. Without this, child streaming plots'
        periodic callbacks (e.g. _refresh_streaming_ui) would never start.
        """
        assert self._renderer is not None, "renderer is not set"
        for lazyplot in self._plots:
            plot = lazyplot._plot
            assert plot._renderer is not None, f"{plot.name} renderer is not set"
            for cb in plot._renderer._periodic_callbacks:
                self._renderer.add_periodic_callback(cb)
    
    def is_streaming(self):
        return any(lazyplot.is_streaming for lazyplot in self._plots)
    
    def _start_streaming(self):
        for lazyplot in self._plots:
            plot = lazyplot._plot
            if plot.is_streaming():
                plot._start_streaming()
                
    def _wait_for_streaming_ready(self):
        for lazyplot in self._plots:
            plot = lazyplot._plot
            if plot.is_streaming():
                plot._wait_for_streaming_ready()

    def _apply_linked_axes(self):
        """Apply layout-level linked_axes control to all child plots."""
        if self._control is None:
            return
        linked_axes = self._control.get("linked_axes", True)
        for lazyplot in self._plots:
            plot = lazyplot._plot
            if plot._control is not None:
                plot._control["linked_axes"] = linked_axes
            for overlay in plot._overlays:
                if overlay._control is not None:
                    overlay._control["linked_axes"] = linked_axes
    
    def _warn_if_linked_axes_with_streaming(self):
        """Warn if linked_axes is enabled when streaming and non-streaming plots coexist.

        Streaming plots continuously update their x-axis range, which will drag
        linked non-streaming plots to the same range — making their data invisible.
        """
        if self._control is None or not self._control.get("linked_axes", True):
            return
        has_streaming = any(lazyplot.is_streaming for lazyplot in self._plots)
        has_non_streaming = any(not lazyplot.is_streaming for lazyplot in self._plots)
        if has_streaming and has_non_streaming:
            cprint(
                "Streaming and non-streaming plots detected with linked_axes=True. "
                + "Non-streaming plots may show empty data as their axes follow the streaming range. "
                + "Use .control(linked_axes=False) to fix this.",
                style=TextStyle.BOLD + RichColor.YELLOW,
            )

    def _create(self):
        super()._create()
        self._warn_if_linked_axes_with_streaming()
    
    # no plot needed
    def _create_plot(self):
        pass
    
    # no pane needed
    def _create_pane(self):
        pass

    def _create_component(self):
        self._apply_linked_axes()
        self._component = self._plot_func(
            *self._plots, style=self._style, control=self._control  # pyright: ignore[reportCallIssue]
        )
        self._add_plots_periodic_callbacks()
