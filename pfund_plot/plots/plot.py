# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, ClassVar, Any

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame, IntoSeries
    from holoviews.streams import Pipe
    from anywidget import AnyWidget
    from panel.pane import Pane
    from pfeed.streaming.streaming_message import StreamingMessage
    from pfeed.feeds.market_feed import MarketFeed
    from pfund_plot.renderers.base import BaseRenderer
    from pfund_plot.plots.lazy import LazyPlot
    from pfund_plot.typing import (
        RenderedResult,
        Figure,
        Component,
        Plot,
        RawFigure,
        Style,
        Control,
    )

import asyncio
import time
import warnings
import importlib
from threading import Thread
from abc import ABC, abstractmethod

import narwhals as nw
import panel as pn

from pfund_kit.style import cprint, RichColor, TextStyle
from pfund_plot.enums import PlottingBackend, DisplayMode, NotebookType


class BasePlot(ABC):
    REQUIRED_COLS: ClassVar[list[str] | None] = None
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend] | None] = None
    SUPPORT_STREAMING: ClassVar[bool] = False
    backends = SUPPORTED_BACKENDS  # alias for SUPPORTED_BACKENDS
    # Wrapper class like CandlestickStyle, used to access the style() function based on backend
    style: ClassVar[Any | None] = None
    # Wrapper class like CandlestickControl, used to access the control() function based on backend
    control: ClassVar[Any | None] = None
    _style: ClassVar[Style | None] = None  # actual style dictionary
    _control: ClassVar[Control | None] = None  # actual control dictionary
    _backend: ClassVar[PlottingBackend | None] = None
    _mode: ClassVar[DisplayMode | None] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> LazyPlot:
        from pfund_plot.plots.lazy import LazyPlot

        instance: BasePlot = super().__new__(cls)
        # manually call __init__ to initialize the instance
        instance.__init__(*args, **kwargs)
        return LazyPlot(instance)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        class_name = cls.__name__
        assert cls.SUPPORTED_BACKENDS is not None, (
            f"SUPPORTED_BACKENDS is not defined for class {class_name}"
        )
        for backend in cls.SUPPORTED_BACKENDS:
            if cls.style is not None:
                assert hasattr(cls.style, backend.value), (
                    f"style for {backend} is not defined for class {class_name}"
                )
            if cls.control is not None:
                assert hasattr(cls.control, backend.value), (
                    f"control for {backend} is not defined for class {class_name}"
                )

    def __init__(self, data: IntoFrame | IntoSeries | None = None, streaming_feed: MarketFeed | None = None):
        '''
        Args:
            data: The data to plot, either a dataframe or a series
            streaming_feed: pfeed's feed object that supports streaming
        '''
        from pfund_kit.utils import get_notebook_type

        self._setup(data, streaming_feed)
        self._data: nw.DataFrame[Any] | nw.Series[Any] | None = self._standardize_data(data) if data is not None else None
        self._streaming_feed: MarketFeed | None = streaming_feed
        self._streaming_pipe: Pipe | None = None
        self._streaming_thread: Thread | None = None
        self._anywidget: AnyWidget | None = None
        self._plot: Plot | None = None
        self._pane: Pane | None = None
        self._widgets: Any | None = None  # a set of widgets, e.g. CandlestickWidgets
        self._component: Component | None = None

        self._notebook_type: NotebookType | None = get_notebook_type()

        cls = self.__class__
        if cls._backend is None:
            cls.set_backend(cls.SUPPORTED_BACKENDS[0])
        if cls._mode is None:
            cls.set_mode(
                DisplayMode.notebook if self._notebook_type else DisplayMode.browser
            )

        # Initialize instance variables
        self._backend: PlottingBackend | None = None
        self._mode: DisplayMode | None = None
        self._renderer: BaseRenderer | None = None
        self._style: Style | None = None
        self._control: Control | None = None
        self._set_backend(cls._backend)
        self._set_mode(cls._mode)

    @abstractmethod
    def _standardize_data(self, data: IntoFrame | IntoSeries) -> nw.DataFrame[Any] | nw.Series[Any]:
        pass

    @abstractmethod
    def _create_widgets(self) -> None:
        pass
    
    @abstractmethod
    def _update_widgets(self, data: nw.DataFrame[Any] | nw.Series[Any]) -> None:
        pass

    def _update_data(self, data: nw.DataFrame[Any] | nw.Series[Any]):
        self._data = data

    @abstractmethod
    def _create_component(self) -> None:
        pass

    def _setup(self, data: IntoFrame | IntoSeries | None, streaming_feed: MarketFeed | None):
        from pfund_plot.utils import import_hvplot_df_module, match_df_with_data_tool
        from pfeed import get_config
        from pfeed.feeds.streaming_feed_mixin import StreamingFeedMixin

        # TODO: only for bokeh backend?
        if data is not None:
            import_hvplot_df_module(match_df_with_data_tool(data))

        if streaming_feed is not None:
            assert self.SUPPORT_STREAMING, f"{self.__class__.__name__} does not support streaming"
            if not isinstance(streaming_feed, StreamingFeedMixin):
                raise ValueError("feed must be a pfeed's Feed object that supports streaming")
            # set pipeline mode to True for streaming to standardize the run method to be feed.run()
            assert streaming_feed.is_pipeline(), f"{streaming_feed} must be in pipeline mode"
            assert streaming_feed._num_workers is None, f"Ray is not supported in streaming plot, {streaming_feed.__class__.__name__} 'num_workers' must be None"
            pfeed_config = get_config()
            data_tool = pfeed_config.data_tool
            import_hvplot_df_module(data_tool)

    def _create(self):
        if self._pane is None:
            self._create_pane()
        if self._widgets is None:
            self._create_widgets()
        if self._component is None:
            self._create_component()

    def _add_periodic_callback(self, callback: Callable[..., Any]):
        '''Add a periodic callback to the renderer.
        Args:
            periodic_callback: The periodic callback to add.
                it is created by `panel.state.add_periodic_callback`.
        '''
        periodic_callback = pn.state.add_periodic_callback(
            callback, 
            period=self._control['update_interval'],  # in ms
            start=False,
        )
        self._renderer.add_periodic_callback(periodic_callback)
    
    def _on_streaming_callback(self, msg: StreamingMessage) -> StreamingMessage:
        raise NotImplementedError(f"{self.__class__.__name__} does not support streaming")
    
    def _is_streaming_ready(self) -> bool:
        raise NotImplementedError(f"{self.__class__.__name__} does not support streaming")
        
    def _start_streaming(self):
        assert self._streaming_feed is not None, "streaming_feed is not set"
        self._add_periodic_callback(self._refresh_streaming_ui)

        # add on_callback to the first of the custom_transformations list
        for request in self._streaming_feed._requests:
            transformations = self._streaming_feed._custom_transformations[request]
            self._streaming_feed._custom_transformations[request] = (
                self._on_streaming_callback,
                *transformations,
            )
        if self._notebook_type is None:
            self._streaming_thread = Thread(
                target=self._streaming_feed.run,
                daemon=True,
            )
            self._streaming_thread.start()
        else:
            asyncio.get_running_loop().create_task(self._streaming_feed.run_async())
    
    def _refresh_streaming_ui(self):
        '''during streaming, update pane and widgets accordingly using the newly updated data (updated in _on_streaming_callback)'''
        if self._data is not None and self._is_streaming_ready():
            self._update_pane(self._data)
            self._update_widgets(self._data)
    
    def _wait_for_streaming_ready(self):
        if self._streaming_feed is not None and self._data is None:
            while not self._is_streaming_ready():
                cprint("Not enough data to plot, waiting for streaming data...", style=TextStyle.BOLD + RichColor.YELLOW)
                time.sleep(1)
                
    async def _wait_for_streaming_ready_async(self):
        if self._streaming_feed is not None and self._data is None:
            while not self._is_streaming_ready():
                cprint("Not enough data to plot, waiting for streaming data...", style=TextStyle.BOLD + RichColor.YELLOW)
                await asyncio.sleep(1)
    
    def _render(self) -> RenderedResult:
        self._create()
        return self._renderer.render(self._component)
    
    def _render_sync(self) -> RenderedResult:
        if self._streaming_feed is not None:
            self._start_streaming()
            # NOTE: when streaming, need to wait for enough data before creating plot/pane etc.
            # otherwise the e.g. x-axis might be wrong and cannot be fixed once it's served
            self._wait_for_streaming_ready()
        return self._render()

    async def _render_async(self) -> RenderedResult:
        if self._streaming_feed is not None:
            self._start_streaming()
            await self._wait_for_streaming_ready_async()
        return self._render()

    @classmethod
    def set_style(cls, style: dict | None = None):
        """Set the class-level style for the plot."""
        cls._style = cls._create_style(style, cls._backend, cls.style)

    @staticmethod
    def _create_style(
        style: dict | None, backend: PlottingBackend, style_wrapper
    ) -> dict:
        if style_wrapper is None:
            return None

        default_style = getattr(style_wrapper, backend.value)()

        if style is None:
            return default_style

        if not isinstance(style, dict):
            raise ValueError("style must be a dictionary")

        return {**default_style, **style}

    def _set_style(self, style: dict | None = None):
        """Set the instance-level style for the plot."""
        self._style = self._create_style(style, self._backend, self.style)

    @classmethod
    def set_control(cls, control: dict | None = None):
        """Set the class-level control for the plot."""
        cls._control = cls._create_control(control, cls._backend, cls.control)

    @staticmethod
    def _create_control(
        control: dict | None, backend: PlottingBackend, control_wrapper
    ) -> dict:
        if control_wrapper is None:
            return None

        default_control = getattr(control_wrapper, backend.value)()

        if control is None:
            return default_control

        if not isinstance(control, dict):
            raise ValueError("control must be a dictionary")

        return {**default_control, **control}

    def _set_control(self, control: dict | None = None):
        """Set the instance-level control for the plot."""
        self._control = self._create_control(control, self._backend, self.control)

    @classmethod
    def set_backend(cls, backend: PlottingBackend | str):
        assert backend in cls.SUPPORTED_BACKENDS, (
            f"Backend {backend} is not in supported backends: {cls.SUPPORTED_BACKENDS}"
        )
        original_backend = cls._backend
        cls._backend = PlottingBackend[backend.lower()]
        is_backend_changed = original_backend != cls._backend
        # reset style and control if backend is changed
        if is_backend_changed or cls._style is None:
            cls.set_style()
        if is_backend_changed or cls._control is None:
            cls.set_control()

    def _set_backend(self, backend: PlottingBackend | str):
        """Set the instance-level backend for the plot."""
        assert backend in self.SUPPORTED_BACKENDS, (
            f"Backend {backend} is not in supported backends: {self.SUPPORTED_BACKENDS}"
        )
        original_backend = self._backend
        self._backend = PlottingBackend[backend.lower()]
        is_backend_changed = original_backend != self._backend
        # reset style and control if backend is changed
        if is_backend_changed or self._style is None:
            self._set_style()
        if is_backend_changed or self._control is None:
            self._set_control()

    @classmethod
    def set_mode(cls, mode: DisplayMode | str):
        assert mode in DisplayMode.__members__, (
            f"Mode {mode} is not in supported modes: {DisplayMode}"
        )
        cls._mode = DisplayMode[mode.lower()]

    def _set_mode(self, mode: DisplayMode | str):
        """Set the instance-level mode for the plot."""
        assert mode in DisplayMode.__members__, (
            f"Mode {mode} is not in supported modes: {DisplayMode}"
        )
        self._mode = DisplayMode[mode.lower()]
        self._set_renderer()

    def _set_renderer(self):
        if self._mode == DisplayMode.notebook:
            from pfund_plot.renderers.notebook import NotebookRenderer

            self._renderer = NotebookRenderer()
        elif self._mode == DisplayMode.browser:
            from pfund_plot.renderers.browser import BrowserRenderer

            self._renderer = BrowserRenderer()
        elif self._mode == DisplayMode.desktop:
            from pfund_plot.renderers.desktop import DesktopRenderer

            self._renderer = DesktopRenderer()

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def _plot_func(self) -> Callable[[nw.DataFrame[Any] | nw.Series[Any], Style, Control], Plot]:
        """Runs the plot function for the current backend."""
        module_path = f"pfund_plot.plots.{self.name}.{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")

    @property
    def figure(self) -> Figure:
        import hvplot

        if self._plot is None:
            self._create_plot()

        plot: Plot = self._plot
        backend = self._backend

        if backend == PlottingBackend.panel:
            raise ValueError("Panel backend does not support figure property")
        elif backend in [PlottingBackend.bokeh, PlottingBackend.plotly, PlottingBackend.matplotlib]:
            if self._is_plotted_by_hvplot():
                # use hvplot to convert holoviews Overlay to the underlying plotting library's figure
                fig = hvplot.render(plot, backend=backend)
                if backend == PlottingBackend.plotly:
                    import plotly.graph_objects as go
                    # hvplot.render() returns a dict, convert it to a plotly Figure
                    fig: dict
                    fig = go.Figure(fig)
            else:  # plot is from plt.bokeh(), plt.plotly() or plt.matplotlib()
                plot: RawFigure
                fig = plot
        # TODO
        # elif self._backend == PlottingBackend.altair:
        #     pass
        else:
            raise ValueError(f"Unsupported backend: {backend}")
        return fig

    def _is_using_marimo_svelte_combo(self):
        return (
            self._backend == PlottingBackend.svelte
            and self._mode == DisplayMode.notebook
            and self._notebook_type == NotebookType.marimo
        )

    @staticmethod
    def _get_sizing_mode(height: int | None, width: int | None) -> str | None:
        if height is None and width is None:
            return "stretch_both"
        elif height is None:
            return "stretch_height"
        elif width is None:
            return "stretch_width"
        else:
            return None
    
    def _is_plotted_by_hvplot(self) -> bool:
        from holoviews.core.overlay import Overlay
        return isinstance(self._plot, Overlay)
    
    def _create_plot(self):
        """Runs the plot function for the current backend"""
        self._plot = self._plot_func(self._data, self._style, self._control)

    def _create_pane(self):
        if self._control and "num_data" in self._control:
            data = self._data.tail(self._control["num_data"])
        else:
            data = self._data

        if self._plot is None:
            self._create_plot()

        backend = self._backend

        if backend == PlottingBackend.panel:
            # no pane needed for panel backend (e.g. GridStack, use it directly as a component)
            pass
        elif backend in [PlottingBackend.bokeh, PlottingBackend.plotly, PlottingBackend.matplotlib]:
            if self._is_plotted_by_hvplot():
                from holoviews.streams import Pipe
                from holoviews import DynamicMap

                self._streaming_pipe = Pipe(data=data)
                plot = self._plot_func
                dmap = DynamicMap(
                    lambda data: plot(data, self._style, self._control),
                    streams=[self._streaming_pipe],
                )
                self._pane = pn.pane.HoloViews(
                    dmap, linked_axes=self._control.get("linked_axes", True)
                )
            else:  # from plt.bokeh(), plt.plotly() or plt.matplotlib()
                if backend == PlottingBackend.bokeh:
                    self._pane = pn.pane.Bokeh(self._plot)
                elif backend == PlottingBackend.plotly:
                    self._pane = pn.pane.Plotly(self._plot)
                elif backend == PlottingBackend.matplotlib:
                    self._pane = pn.pane.Matplotlib(self._plot)
        elif backend == PlottingBackend.svelte:
            if pn.extension._loaded_extensions:
                warnings.warn(
                    "Svelte backend may not work correctly with existing panel extensions. Restart kernel to fix if issues arise.",
                    stacklevel=1,
                )
            self._anywidget: AnyWidget = self._plot_func(data, self._style, self._control)
            self._pane = pn.pane.IPyWidget(self._anywidget)
        # TODO
        # elif backend == PlottingBackend.altair:
        #     self._pane = pn.pane.Vega(self._plot)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def _update_pane(self, data: nw.DataFrame[Any] | nw.Series[Any]):
        if self._pane is None:
            self._create_pane()
        if self._backend == PlottingBackend.bokeh:
            self._streaming_pipe.send(data)
        elif self._backend == PlottingBackend.svelte:
            assert self._anywidget is not None, "anywidget is not set"
            self._anywidget.update_data(data)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")
