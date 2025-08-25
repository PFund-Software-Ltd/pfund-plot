from __future__ import annotations
from typing import Callable, TYPE_CHECKING, ClassVar
if TYPE_CHECKING:
    from pfeed._typing import GenericFrame

import importlib
from abc import ABC, abstractmethod

from pfeed.feeds.market_feed import MarketFeed
from pfeed.utils.dataframe import is_dataframe
from pfund_plot._typing import tPlottingBackend, tDisplayMode
from pfund_plot.enums import PlottingBackend, DisplayMode


class Plot(ABC):
    PLOT_TYPE: ClassVar[str]  # e.g. 'candlestick'
    
    def __init__(self):
        from pfund_plot.state import state
        self._backend = PlottingBackend.bokeh
        self._mode = DisplayMode.notebook
        self._state = state
        self._streaming = False
        self._streaming_freq = 1000  # in milliseconds

    @property
    def style(self):
        from pfund_plot.plots.style import Style
        return Style(self._backend, self.PLOT_TYPE)
    
    @property
    def control(self):
        from pfund_plot.plots.control import Control
        return Control(self._backend, self.PLOT_TYPE)
    
    @property
    def _plot(self) -> Callable:
        module_path = f"pfund_plot.plots.{self.PLOT_TYPE}._{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, 'plot')
    
    def set_backend(self, backend: tPlottingBackend):
        self._backend = PlottingBackend[backend.lower()]
        
    def set_mode(self, mode: tDisplayMode) -> None:
        self._mode = DisplayMode[mode.lower()]
    
    def set_streaming(self, streaming_feed: MarketFeed | None, streaming_freq: int=1000) -> None:
        self._streaming = bool(streaming_feed)
        self._streaming_freq = streaming_freq  # in milliseconds
        if streaming_feed is not None:
            assert isinstance(streaming_feed, MarketFeed), "streaming_feed must be a MarketFeed instance"
            assert streaming_feed._use_ray is False, "Ray is not supported for plotting"
    
    def is_streaming(self) -> bool:
        # if in layout, override streaming setting
        return self._streaming or self._state.layout.streaming
        
    def _setup_plotting(self, df: GenericFrame | None, style: dict | None, control: dict | None, streaming_feed: MarketFeed | None) -> tuple[dict, dict]:
        style = style or self.style()
        control = control or self.control()
        assert df is not None or streaming_feed is not None, "Either df or streaming_feed must be provided"
        # TODO: only for bokeh backend?
        if df is not None:
            self._import_hvplot(df)
        return style, control
    
    def _setup_streaming(self, streaming_feed: MarketFeed | None, streaming_freq: int) -> None:
        self.set_streaming(streaming_feed, streaming_freq=streaming_freq)
        # TODO: only for bokeh backend?
        if streaming_feed is not None:
            self._import_hvplot(streaming_feed)
    
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
                raise ValueError(f"Unsupported dataframe type: {type(data)}, make sure you have installed the required libraries")
        elif isinstance(data, MarketFeed):
            data_tool= data._data_tool
            if data_tool not in ['pandas', 'polars', 'dask']:
                raise ValueError(f"Unsupported data tool: {data_tool}, must be one of ['pandas', 'polars', 'dask']")
            # dynamically import the corresponding hvplot module
            importlib.import_module(f"hvplot.{data._data_tool}")
        else:
            raise ValueError("Input data must be a dataframe or pfeed's feed object")
        