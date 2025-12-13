from __future__ import annotations
from typing import Callable, TYPE_CHECKING, ClassVar, Any

if TYPE_CHECKING:
    from narwhals.typing import Frame
    from pfeed._typing import GenericFrame
    from panel.pane import Pane
    from anywidget import AnyWidget
    from pfund_plot._typing import Output, tPlottingBackend, tDisplayMode

import importlib
from abc import ABC, abstractmethod

import panel as pn
from holoviews.streams import Pipe

from pfeed.feeds.market_feed import MarketFeed
from pfeed.utils.dataframe import is_dataframe
from pfund_plot.utils.utils import get_notebook_type
from pfund_plot.enums import PlottingBackend, DisplayMode, NotebookType


class Plot(ABC):
    REQUIRED_COLS: ClassVar[list[str]]
    STREAMING_FREQ: ClassVar[int] = 1000  # in milliseconds
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = []
    style: ClassVar[Any]  # Wrapper class like CandlestickStyle, used to access the style() function based on backend
    control: ClassVar[Any]  # Wrapper class like CandlestickControl, used to access the control() function based on backend
    _style: ClassVar[dict | None] = None  # actual style dictionary
    _control: ClassVar[dict | None] = None  # actual control dictionary
    _backend: ClassVar[PlottingBackend] = PlottingBackend.bokeh
    _mode: ClassVar[DisplayMode] = DisplayMode.notebook

    def __new__(cls, *args, **kwargs):
        from pfund_plot.plots.lazy import LazyPlot
        instance: Plot = super().__new__(cls)
        # manually call __init__ to initialize the instance
        instance.__init__(*args, **kwargs)  

        # do some sanity checks for the class variables
        assert hasattr(cls, "style"), "class variable 'style' is not defined"
        assert hasattr(cls, "control"), "class variable 'control' is not defined"
        assert cls.SUPPORTED_BACKENDS, "SUPPORTED_BACKENDS is empty"
        assert cls.STREAMING_FREQ > 0, "STREAMING_FREQ must be greater than 0"
        return LazyPlot(instance)

    def __init__(
        self,
        df: GenericFrame | None = None,
        streaming_feed: MarketFeed | None = None,
        streaming_freq: int = STREAMING_FREQ,
    ):
        import pfund_plot as plt
        from pfund_plot.state import state
        self._setup(df, streaming_feed)

        self._df: Frame | None = self._standardize_df(df) if df is not None else None
        self._streaming_feed: MarketFeed | None = streaming_feed
        self._streaming_freq = streaming_freq

        self._streaming_pipe: Pipe | None = None
        self._anywidget: AnyWidget | None = None

        self._notebook_type: NotebookType | None = get_notebook_type()
        self._state = state

        cls = self.__class__
        cls.set_backend(plt.config.backend)
        cls.set_mode(DisplayMode.notebook if self._notebook_type else DisplayMode.browser)

        # Initialize instance variables
        self._backend: PlottingBackend
        self._mode: DisplayMode
        self._style: dict
        self._control: dict
        self._set_backend(cls._backend)
        self._set_mode(cls._mode)
    
    @abstractmethod
    def _standardize_df(self, df: GenericFrame) -> Frame:
        pass
    
    @abstractmethod
    def _render(self) -> Output:
        pass
    
    @classmethod
    def set_style(cls, style: dict | None = None):
        '''Set the class-level style for the plot.'''
        cls._style = cls._get_style_dict(style, cls._backend, cls.style)
    
    @staticmethod
    def _get_style_dict(style: dict | None, backend: PlottingBackend, style_wrapper) -> dict:
        if style is None:
            style = getattr(style_wrapper, backend.value)()
        if not isinstance(style, dict):
            raise ValueError("style must be a dictionary")
        return style
    
    def _set_style(self, style: dict | None = None):
        '''Set the instance-level style for the plot.'''
        self._style = self._get_style_dict(style, self._backend, self.style)
    
    @classmethod
    def set_control(cls, control: dict | None = None):
        '''Set the class-level control for the plot.'''
        cls._control = cls._get_control_dict(control, cls._backend, cls.control)
    
    @staticmethod
    def _get_control_dict(control: dict | None, backend: PlottingBackend, control_wrapper) -> dict:
        if control is None:
            control = getattr(control_wrapper, backend.value)()
        if not isinstance(control, dict):
            raise ValueError("control must be a dictionary")
        return control
    
    def _set_control(self, control: dict | None = None):
        '''Set the instance-level control for the plot.'''
        self._control = self._get_control_dict(control, self._backend, self.control)
    
    @classmethod
    def set_backend(cls, backend: tPlottingBackend):
        assert backend in cls.SUPPORTED_BACKENDS, f"Backend {backend} is not in supported backends: {cls.SUPPORTED_BACKENDS}"
        original_backend = cls._backend
        cls._backend = PlottingBackend[backend.lower()]
        is_backend_changed = original_backend != cls._backend
        # reset style and control if backend is changed
        if is_backend_changed or cls._style is None:
            cls.set_style()
        if is_backend_changed or cls._control is None:
            cls.set_control()
            
    def _set_backend(self, backend: tPlottingBackend):
        '''Set the instance-level backend for the plot.'''
        assert backend in self.SUPPORTED_BACKENDS, f"Backend {backend} is not in supported backends: {self.SUPPORTED_BACKENDS}"
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
        assert mode in DisplayMode, f"Mode {mode} is not in supported modes: {DisplayMode}"
        cls._mode = DisplayMode[mode.lower()]
    
    def _set_mode(self, mode: tDisplayMode):
        '''Set the instance-level mode for the plot.'''
        assert mode in DisplayMode, f"Mode {mode} is not in supported modes: {DisplayMode}"
        self._mode = DisplayMode[mode.lower()]

    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    @property
    def _plot(self) -> Callable:
        module_path = f"pfund_plot.plots.{self.name}._{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")
    
    @property
    def figure(self):
        """Return the raw figure object (e.g. bokeh.plotting.figure or plotly.graph_objects.Figure)."""
        return self._plot(self._df, self._style, self._control)
    
    def _setup(self, df: GenericFrame | None, streaming_feed: MarketFeed | None) -> None:
        assert df is not None or streaming_feed is not None, (
            "Either df or streaming_feed must be provided"
        )
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
    
    def _create_plot(self) -> AnyWidget | Pane:
        if self._backend == PlottingBackend.bokeh:
            from holoviews import DynamicMap

            self._streaming_pipe = Pipe(
                data=self._df.tail(min(self._control["num_data"], self._df.shape[0]))
            )
            dmap = DynamicMap(
                lambda data: self._plot(data, self._style), streams=[self._streaming_pipe]
            )
            component = pn.pane.HoloViews(dmap)
        elif self._backend == PlottingBackend.svelte:
            self._anywidget: AnyWidget = self._plot(self._df.tail(self._control["num_data"]), self._style)
            if self._notebook_type == NotebookType.marimo:
                component = self._anywidget
            else:
                component = pn.pane.IPyWidget(self._anywidget)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")
        return component

    def _update_plot(self, df: Frame):
        if self._backend == "bokeh":
            self._streaming_pipe.send(df)
        elif self._backend == "svelte":
            assert self._anywidget is not None, "anywidget is not set"
            self._anywidget.update_data(df)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")

    @staticmethod
    def _import_hvplot(data: GenericFrame | MarketFeed) -> None:
        if is_dataframe(data):
            import pandas as pd
            import polars as pl
            from pfeed._typing import dd

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
