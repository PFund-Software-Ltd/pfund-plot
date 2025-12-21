from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import Frame
    from pfeed.typing import GenericFrame
    from pfeed.feeds.market_feed import MarketFeed
    from bokeh.plotting._figure import figure as BokehFigure
    from plotly.graph_objects import Figure as PlotlyFigure
    from altair import Chart as AltairChart
    from matplotlib.figure import Figure as MatplotlibFigure
    from pfund_plot.plots.lazy import LazyPlot

import os
import datetime
from pathlib import Path

from pfund_plot.enums.notebook_type import NotebookType


def load_js(path: str) -> str:
    js_code = Path(path).read_text()
    return f"<script>{js_code}</script>"


def is_daily_data(df: Frame) -> bool:
    '''Checks if the 'resolution' column is '1d' and the "ts" column by comparing the first two rows to see if the data is daily data.'''
    if df.is_empty():
        return False
    if 'resolution' in df.columns and df.select('resolution').row(0)[0] == '1d':
        return True
    assert 'date' in df.columns, "DataFrame must have a 'date' column"
    assert isinstance(df.select('date').row(0)[0], datetime.datetime), '"date" column must be of type datetime'
    date1 = df.select('date').row(0)[0]
    if df.shape[0] >= 2:
        date2 = df.select('date').row(1)[0]
        delta = date2 - date1
        return delta == datetime.timedelta(days=1)
    else:
        # if only has one data point, check if the time is '00:00:00'
        return str(date1.time()) == '00:00:00'


def get_notebook_type() -> NotebookType | None:
    import importlib.util
    
    marimo_spec = importlib.util.find_spec("marimo")
    if marimo_spec is not None:
        import marimo as mo
        if mo.running_in_notebook():
            return NotebookType.marimo
        
    if any(key.startswith(('JUPYTER_', 'JPY_')) for key in os.environ):
        return NotebookType.jupyter
    
    # if 'VSCODE_PID' in os.environ:
    #     return NotebookType.vscode
    
    # None means not in a notebook environment
    return None


def load_panel_extensions(extensions: list[str] = None):
    import panel as pn

    extensions = extensions or []
    for extension in extensions:
        if extension not in pn.extension._loaded_extensions:
            pn.extension(extension)
            print(f'loaded Panel extension: {extension}')


def import_hvplot_df_module(data: GenericFrame | MarketFeed) -> None:
    import importlib
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


def convert_to_lazy_plot(obj: PlotlyFigure | AltairChart | MatplotlibFigure | BokehFigure) -> LazyPlot:
    """Convert plotting library figures to LazyPlot instances."""
    import pfund_plot as plt

    # Plotly
    try:
        import plotly.graph_objects as go
        if isinstance(obj, go.Figure):
            return plt.plotly(obj)
    except ImportError:
        pass

    # TODO: plt.altair(), plt.matplotlib(), plt.bokeh() are not implemented yet
    # # Altair
    # try:
    #     import altair as alt
    #     if isinstance(obj, (alt.Chart, alt.LayerChart, alt.HConcatChart, alt.VConcatChart)):
    #         return plt.altair(obj)
    # except ImportError:
    #     pass

    # # Matplotlib
    # try:
    #     from matplotlib.figure import Figure as MplFigure
    #     if isinstance(obj, MplFigure):
    #         return plt.matplotlib(obj)
    # except ImportError:
    #     pass

    # # Bokeh
    # try:
    #     from bokeh.model import Model as BokehModel
    #     if isinstance(obj, BokehModel):
    #         return plt.bokeh(obj)
    # except ImportError:
    #     pass

    return obj
