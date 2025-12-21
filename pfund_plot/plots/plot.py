from __future__ import annotations
from typing import Callable, TYPE_CHECKING, ClassVar, Any

if TYPE_CHECKING:
    from narwhals.typing import Frame
    from holoviews.streams import Pipe
    from pfeed.typing import GenericFrame
    from anywidget import AnyWidget
    from panel.io.callbacks import PeriodicCallback
    from panel.pane import Pane
    from pfeed.feeds.market_feed import MarketFeed
    from pfund_plot.renderers.base import BaseRenderer
    from pfund_plot.typing import (
        RenderedResult,
        Figure,
        tPlottingBackend,
        tDisplayMode,
        Component,
        Plot,
        RawFigure,
    )

import warnings
import importlib
from abc import ABC, abstractmethod

import panel as pn

from pfund_plot.enums import PlottingBackend, DisplayMode, NotebookType


class BasePlot(ABC):
    REQUIRED_COLS: ClassVar[list[str] | None] = None
    STREAMING_FREQ: ClassVar[int] = 1000  # in milliseconds
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend] | None] = None
    backends = SUPPORTED_BACKENDS  # alias for SUPPORTED_BACKENDS
    # Wrapper class like CandlestickStyle, used to access the style() function based on backend
    style: ClassVar[Any | None] = None
    # Wrapper class like CandlestickControl, used to access the control() function based on backend
    control: ClassVar[Any | None] = None
    _style: ClassVar[dict | None] = None  # actual style dictionary
    _control: ClassVar[dict | None] = None  # actual control dictionary
    _backend: ClassVar[PlottingBackend | None] = None
    _mode: ClassVar[DisplayMode | None] = None

    def __new__(cls, *args, **kwargs):
        from pfund_plot.plots.lazy import LazyPlot

        instance: BasePlot = super().__new__(cls)
        # manually call __init__ to initialize the instance
        instance.__init__(*args, **kwargs)
        return LazyPlot(instance)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        class_name = cls.__name__
        assert cls.SUPPORTED_BACKENDS is not None, (
            f"SUPPORTED_BACKENDS is not defined for class {class_name}"
        )
        assert cls.STREAMING_FREQ > 0, (
            f"STREAMING_FREQ must be greater than 0 for class {class_name}"
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

    def __init__(
        self,
        df: GenericFrame | None = None,
        streaming_feed: MarketFeed | None = None,
        streaming_freq: int = STREAMING_FREQ,
    ):
        from pfund_plot.utils import get_notebook_type

        self._setup(df, streaming_feed)

        self._df: Frame | None = self._standardize_df(df) if df is not None else None
        self._streaming_feed: MarketFeed | None = streaming_feed
        self._streaming_freq = streaming_freq

        self._streaming_pipe: Pipe | None = None
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
        self._style: dict | None = None
        self._control: dict | None = None
        self._set_backend(cls._backend)
        self._set_mode(cls._mode)

    @abstractmethod
    def _standardize_df(self, df: GenericFrame) -> Frame:
        pass

    @abstractmethod
    def _create_widgets(self) -> None:
        pass

    @abstractmethod
    def _create_component(self) -> None:
        pass

    def _create(self):
        if self._pane is None:
            self._create_pane()
        if self._widgets is None:
            self._create_widgets()
        if self._component is None:
            self._create_component()

    def _add_periodic_callback(self, periodic_callback: PeriodicCallback):
        self._renderer.add_periodic_callback(periodic_callback)

    def _render(self) -> RenderedResult:
        self._create()
        return self._renderer.render(self._component)

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
    def set_backend(cls, backend: tPlottingBackend):
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

    def _set_backend(self, backend: tPlottingBackend):
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
    def set_mode(cls, mode: tDisplayMode):
        assert mode in DisplayMode.__members__, (
            f"Mode {mode} is not in supported modes: {DisplayMode}"
        )
        cls._mode = DisplayMode[mode.lower()]

    def _set_mode(self, mode: tDisplayMode):
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
    def _plot_func(self) -> Callable:
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

    def _setup(
        self, df: GenericFrame | None, streaming_feed: MarketFeed | None
    ) -> None:
        from pfund_plot.utils import import_hvplot_df_module
        from pfeed.feeds.market_feed import MarketFeed

        # TODO: only for bokeh backend?
        if df is not None:
            import_hvplot_df_module(df)
        if streaming_feed is not None:
            assert isinstance(streaming_feed, MarketFeed), (
                "streaming_feed must be a MarketFeed instance"
            )
            assert streaming_feed._use_ray is False, "Ray is not supported for plotting"
        if streaming_feed is not None:
            import_hvplot_df_module(streaming_feed)

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
        self._plot = self._plot_func(self._df, self._style, self._control)

    def _create_pane(self):
        if self._control and "num_data" in self._control:
            df = self._df.tail(self._control["num_data"])
        else:
            df = self._df
        
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

                self._streaming_pipe = Pipe(data=df)
                dmap = DynamicMap(
                    lambda data: self._plot_func(data, self._style, self._control),
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
            self._anywidget: AnyWidget = self._plot_func(df, self._style, self._control)
            self._pane = pn.pane.IPyWidget(self._anywidget)
        # TODO
        # elif backend == PlottingBackend.altair:
        #     self._pane = pn.pane.Vega(self._plot)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def _update_pane(self, df: Frame):
        if self._backend == PlottingBackend.bokeh:
            self._streaming_pipe.send(df)
        elif self._backend == PlottingBackend.svelte:
            assert self._anywidget is not None, "anywidget is not set"
            self._anywidget.update_data(df)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")
