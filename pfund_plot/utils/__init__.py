from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    import pandas as pd
    from narwhals.typing import IntoFrame
    from bokeh.plotting._figure import figure as BokehFigure
    from plotly.graph_objects import Figure as PlotlyFigure
    from altair import Chart as AltairChart
    from matplotlib.figure import Figure as MatplotlibFigure
    from pfund_plot.plots.lazy import LazyPlot

import datetime
from pathlib import Path

import narwhals as nw
from pfeed.enums import DataTool


def load_js(path: str) -> str:
    js_code = Path(path).read_text()
    return f"<script>{js_code}</script>"


def convert_to_datetime(date: str | datetime.datetime | pd.Timestamp) -> datetime.datetime:
    """Convert various date types to a naive UTC datetime.

    Always returns tz-naive datetime (in UTC) because Panel/Bokeh widgets
    don't handle tz-aware datetimes consistently in their internal validation.
    """
    if isinstance(date, str):
        dt = datetime.datetime.fromisoformat(date)
    elif isinstance(date, datetime.datetime):
        dt = date
    elif isinstance(date, datetime.date):
        dt = datetime.datetime(date.year, date.month, date.day)
    elif isinstance(date, pd.Timestamp):
        dt = date.to_pydatetime()
    else:
        raise ValueError(f"Invalid date type: {type(date)}")
    # convert to UTC then strip tzinfo — Panel widgets don't handle tz-aware datetimes consistently
    if dt.tzinfo is not None:
        dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return dt

    
def is_daily_data(df: nw.DataFrame[Any]) -> bool:
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


def load_panel_extensions(extensions: list[str] = None):
    import panel as pn

    extensions = extensions or []
    for extension in extensions:
        if extension not in pn.extension._loaded_extensions:
            pn.extension(extension)
            print(f'loaded Panel extension: {extension}')


def match_df_with_data_tool(df: IntoFrame) -> DataTool:
    import pandas as pd
    import polars as pl
    from pfeed.utils.dataframe import dd
    
    if isinstance(df, pd.DataFrame):
        return DataTool.pandas
    elif pl and isinstance(df, (pl.DataFrame, pl.LazyFrame)):
        return DataTool.polars
    elif dd and isinstance(df, dd.DataFrame):
        return DataTool.dask
    else:
        raise ValueError(f"Unsupported dataframe type: {type(df)}, make sure you have installed the required libraries")


def import_hvplot_df_module(data_tool: DataTool | str) -> None:

    data_tool = DataTool[data_tool.lower()]
    if data_tool == DataTool.pandas:
        import hvplot.pandas
    elif data_tool == DataTool.polars:
        import hvplot.polars
    elif data_tool == DataTool.dask:
        import hvplot.dask
    else:
        raise ValueError(f"Unsupported data tool: {data_tool}, must be one of ['pandas', 'polars', 'dask']")


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
