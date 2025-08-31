from __future__ import annotations
from typing import Callable, TYPE_CHECKING, ClassVar
if TYPE_CHECKING:
    from narwhals.typing import Frame
    from pfeed._typing import GenericFrame
    from pfund_plot._typing import tPlottingBackend, tDisplayMode

import importlib
from abc import ABC

import panel as pn
from holoviews.streams import Pipe

from pfeed.feeds.market_feed import MarketFeed
from pfeed.utils.dataframe import is_dataframe
from pfund_plot.utils.utils import get_notebook_type
from pfund_plot.enums import PlottingBackend, DisplayMode, NotebookType


class Plot(ABC):
    PLOT_TYPE: ClassVar[str]  # e.g. 'candlestick'
    
    def __init__(self):
        from pfund_plot.state import state
        self._backend = PlottingBackend.bokeh
        self._mode = DisplayMode.notebook
        self._state = state
        self._streaming_pipe: Pipe | None = None
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
    
    def _update_plot(self, df: Frame):
        if self._backend == 'bokeh':
            self._streaming_pipe.send(df)
        elif self._backend == 'svelte':
            pass
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")
    
    def _create_plot(self, df: Frame, style: dict, control: dict) -> pn.pane.Pane:
        if self._backend == PlottingBackend.bokeh:
            from holoviews import DynamicMap
            self._streaming_pipe = Pipe(data=df.tail(min(control['num_data'], df.shape[0])))
            dmap = DynamicMap(lambda data: self._plot(data, style), streams=[self._streaming_pipe])
            pane = pn.pane.HoloViews(dmap)
        elif self._backend == PlottingBackend.svelte:
            pass
            # def session_created(session_context):
            #     widget = self._plot(df, style)
            #     print(f'Created a session running at the {session_context.request.uri} endpoint')
            # pn.state.on_session_created(session_created)
            # TODO
            # widget = self._plot(df.tail(data_slider.value), style)
            # height = 400
            # pane = pn.pane.IPyWidget(widget)
            # # Update function: send new tail of data via pipe on slider change
            # def _update_data(event):
            #     new_df = df.tail(data_slider.value)
            #     widget.update_data(new_df)
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")
        return pane
    
    def set_backend(self, backend: tPlottingBackend):
        self._backend = PlottingBackend[backend.lower()]
        
    def set_mode(self, mode: tDisplayMode | None) -> None:
        if mode is None:
            notebook_type: NotebookType | None = get_notebook_type()
            mode = DisplayMode.notebook if notebook_type is not None else DisplayMode.browser
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
        
    def _setup_plotting(self, df: GenericFrame | None, style: dict | None, control: dict | None, streaming_feed: MarketFeed | None, mode: tDisplayMode | None) -> tuple[dict, dict]:
        style = style or self.style()
        control = control or self.control()
        self.set_mode(mode)
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
        