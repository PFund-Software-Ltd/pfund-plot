try:
    import polars as pl
except ImportError:
    pl = None

try:
    import dask.dataframe as dd
except ImportError:
    dd = None
import pandas as pd

from pfeed.const.enums import DataTool
from pfeed.types.core import tDataFrame, is_dataframe
from pfeed.feeds.base_feed import BaseFeed

from pfund_plot.const.enums import DataType
from pfund_plot import get_config


config = get_config()


def _get_dataframe_type(df: tDataFrame) -> DataTool:
    if isinstance(df, pd.DataFrame):
        return DataTool.pandas
    elif pl and isinstance(df, (pl.DataFrame, pl.LazyFrame)):
        return DataTool.polars
    elif dd and isinstance(df, dd.DataFrame):
        return DataTool.dask
    else:
        raise ValueError(f"Unsupported dataframe type: {type(df)}, make sure you have installed the required libraries")


def validate_input_data(data: tDataFrame | BaseFeed) -> DataType:
    if is_dataframe(data):
        df_type: DataTool = _get_dataframe_type(data)
        data_tool: DataTool = DataTool[config.data_tool.lower()]
        if data_tool != df_type:
            raise ValueError(f"data_tool is set to '{data_tool}', but the input data is of type '{df_type}'")
        return DataType.dataframe
    elif isinstance(data, BaseFeed):
        return DataType.datafeed
    else:
        raise ValueError("Input data must be a dataframe or pfeed's feed object")
    