import importlib

try:
    import polars as pl
except ImportError:
    pl = None

try:
    import dask.dataframe as dd
except ImportError:
    dd = None
import pandas as pd

from pfeed.types.core import tDataFrame, is_dataframe
from pfeed.feeds.base_feed import BaseFeed

from pfund_plot.const.enums import DataType


def _import_hvplot(data: tDataFrame | BaseFeed) -> None:
    if is_dataframe(data):
        if isinstance(data, pd.DataFrame):
            import hvplot.pandas
        elif pl and isinstance(data, (pl.DataFrame, pl.LazyFrame)):
            import hvplot.polars
        elif dd and isinstance(data, dd.DataFrame):
            import hvplot.dask
        else:
            raise ValueError(f"Unsupported dataframe type: {type(data)}, make sure you have installed the required libraries")
    elif isinstance(data, BaseFeed):
        importlib.import_module(f"hvplot.{data.data_tool.name.value.lower()}")
    else:
        raise ValueError("Input data must be a dataframe or pfeed's feed object")


def validate_data_type(data: tDataFrame | BaseFeed, streaming: bool, import_hvplot: bool = True) -> DataType:
    if is_dataframe(data):
        data_type = DataType.dataframe
    elif isinstance(data, BaseFeed):
        data_type = DataType.datafeed
    else:
        raise ValueError("Input data must be a dataframe or pfeed's feed object")
   
    # FIXME: add it back when pfeed's streaming is ready
    # if streaming:
    #     assert data_type == DataType.datafeed, "streaming is only supported for pfeed's feed object, not dataframe"

    if import_hvplot:
        _import_hvplot(data)
    return data_type
