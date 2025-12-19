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
        tPlottingBackend,
        tDisplayMode,
        Component,
        Plot,
    )

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
        assert cls.style is not None, (
            f"class variable 'style' is not defined for class {class_name}"
        )
        assert cls.control is not None, (
            f"class variable 'control' is not defined for class {class_name}"
        )
        for backend in cls.SUPPORTED_BACKENDS:
            assert hasattr(cls.style, backend.value), (
                f"style for {backend} is not defined for class {class_name}"
            )
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
    def _plot(self) -> Callable:
        """Runs the plot function for the current backend."""
        module_path = f"pfund_plot.plots.{self.name}.{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")

    @property
    def plot(self) -> Plot:
        """Runs the plot function for the current backend"""
        return self._plot(self._df, self._style, self._control)

    def _setup(
        self, df: GenericFrame | None, streaming_feed: MarketFeed | None
    ) -> None:
        from pfeed.feeds.market_feed import MarketFeed

        # TODO: only for bokeh backend?
        if df is not None:
            self._import_hvplot(df)
        if streaming_feed is not None:
            assert isinstance(streaming_feed, MarketFeed), (
                "streaming_feed must be a MarketFeed instance"
            )
            assert streaming_feed._use_ray is False, "Ray is not supported for plotting"
        if streaming_feed is not None:
            self._import_hvplot(streaming_feed)

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

    def _create_pane(self):
        from pfund_plot import print_warning
        from pfund_plot.utils import load_panel_extensions

        # NOTE: data update in anywidget (backend=svelte) may have issues (especially in marimo) after loading panel extensions
        if self._backend != PlottingBackend.svelte:
            # TODO: do not load unnecessary extensions
            load_panel_extensions()
        elif pn.extension._loaded_extensions:
            print_warning(
                "Svelte backend may not work correctly with existing panel extensions. Restart kernel to fix if issues arise."
            )

        if self._backend == PlottingBackend.panel:
            # no pane needed for panel backend (e.g. GridStack, use it directly as a component)
            pass
        elif self._backend == PlottingBackend.bokeh:
            from holoviews.streams import Pipe
            from holoviews import DynamicMap

            self._streaming_pipe = Pipe(
                data=self._df.tail(min(self._control["num_data"], self._df.shape[0]))
            )
            dmap = DynamicMap(
                lambda data: self._plot(data, self._style, self._control),
                streams=[self._streaming_pipe],
            )
            self._pane = pn.pane.HoloViews(dmap, linked_axes=self._control.get("linked_axes", True))
        elif self._backend == PlottingBackend.svelte:
            self._anywidget: AnyWidget = self._plot(
                self._df.tail(self._control["num_data"]), self._style, self._control
            )
            self._pane = pn.pane.IPyWidget(self._anywidget)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")

    def _update_pane(self, df: Frame):
        if self._backend == PlottingBackend.bokeh:
            self._streaming_pipe.send(df)
        elif self._backend == PlottingBackend.svelte:
            assert self._anywidget is not None, "anywidget is not set"
            self._anywidget.update_data(df)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")

    # TODO: move to utils
    @staticmethod
    def _import_hvplot(data: GenericFrame | MarketFeed) -> None:
        from pfeed.utils.dataframe import is_dataframe
        
        if is_dataframe(data):
            import pandas as pd
            import polars as pl
            from pfeed.typing import dd

            if isinstance(data, pd.DataFrame):
                import hvplot.pandas
            elif pl and isinstance(data, (pl.DataFrame, pl.LazyFrame)):
                import hvplot.polars
            elif dd and isinstance(data, dd.DataFrame):
                import hvplot.dask
            else:
                raise ValueError(
                    f"Unsupported dataframe type: {type(data)}, make sure you have installed the required libraries"
                )
        elif isinstance(data, MarketFeed):
            data_tool = data._data_tool
            if data_tool not in ["pandas", "polars", "dask"]:
                raise ValueError(
                    f"Unsupported data tool: {data_tool}, must be one of ['pandas', 'polars', 'dask']"
                )
            # dynamically import the corresponding hvplot module
            importlib.import_module(f"hvplot.{data._data_tool}")
        else:
            raise ValueError("Input data must be a dataframe or pfeed's feed object")
