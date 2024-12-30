from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfeed.types.core import tDataFrame
    from pfeed.feeds.base_feed import BaseFeed
    from pfund_plot.types.literals import tDISPLAY_MODE, tDATAFRAME_BACKEND
    from pfund_plot.types.core import tOutput
    from panel.widgets import Widget
    from panel.pane import Pane

import panel as pn
from bokeh.models.widgets.tables import DateFormatter

from pfund import print_warning
from pfeed.etl import convert_to_pandas_df
from pfund_plot.const.enums import DisplayMode, DataType, DataFrameBackend, NotebookType
from pfund_plot.utils.validate import validate_data_type
from pfund_plot.utils.utils import get_notebook_type
from pfund_plot.renderer import render


__all__ = ['dataframe_plot']


SUGGESTED_MAX_DATA_SIZE_FOR_PERSPECTIVE = 10000
SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR = 11
DEFAULT_IFRAME_STYLE = {
    'tabulator': "width: 100vw; height: {height}px;",
    'perspective': "width: calc(100vw - 50px); height: {height}px;",
}


# EXTEND: maybe add some common functionalities here, e.g. search, sort, filter etc. not sure what users want for now.
def dataframe_plot(
    data: tDataFrame | BaseFeed,
    display_mode: tDISPLAY_MODE = "notebook",
    dataframe_backend: tDATAFRAME_BACKEND = "tabulator",
    streaming: bool = False,
    streaming_freq: int = 1000,  # in milliseconds
    max_streaming_data: int | None = None,
    watch: bool = True,
    page_size: int = 20,
    header_filters: bool = False,
    height: int = 600,
    **kwargs
) -> tOutput:
    '''
    Args:
        data: the data to plot, either a dataframe or pfeed's feed object
        display_mode: where to display the plot, either "notebook", "browser", or "desktop"
        streaming: if True, the plot will be updated in real-time as new data is received
        streaming_freq: the update frequency of the streaming data in milliseconds
        max_streaming_data: maximum number of data points used when streaming.
            If None, data will continue to grow unbounded.
        dataframe_backend: backend to use for the dataframe plot.
            e.g. 'tabulator' or 'perspective'
            use Perspective if data size is large or more complicated data manipulation is needed.
        page_size: number of data points to display on each page when using Tabulator backend.
        header_filters: whether to enable header filters when using Tabulator backend.
        watch: whether to watch the streaming data when using Tabulator backend.
            if true, you will be able to see the table update and scroll along with the new data.
        height: height of the dataframe plot in pixels.
            Only applicable when display_mode is 'notebook' and when iframe is used.
        kwargs: kwargs for pn.widgets.Tabulator or pn.pane.Perspective

    For all the supported kwargs, and more customization examples,
    please refer to https://panel.holoviz.org/reference/widgets/Tabulator.html for Tabulator backend,
    and https://panel.holoviz.org/reference/panes/Perspective.html for Perspective backend.
    '''

    display_mode, dataframe_backend = DisplayMode[display_mode.lower()], DataFrameBackend[dataframe_backend.lower()]
    data_type: DataType = validate_data_type(data, streaming, import_hvplot=False)
    if data_type == DataType.datafeed:
        # TODO: get streaming data in the format of dataframe, and then call _validate_df
        # df = data.get_realtime_data(...)
        pass
    else:
        df = data
    df = convert_to_pandas_df(df)
    use_iframe_in_notebook = streaming or (dataframe_backend == DataFrameBackend.perspective)
    iframe_style = None
    
    if dataframe_backend == DataFrameBackend.tabulator:
        if max_streaming_data is not None and max_streaming_data < SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR:
            # FIXME: this is a workaround for a bug in panel Tabulator, see if panel will fix it, or create a github issue
            print_warning(
                f"max_streaming_data < {SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR} will lead to buggy behaviors (possibly a bug in panel Tabulator's rollover). "
                f"Setting max_streaming_data to {SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR}."
            )
            max_streaming_data = SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR
        notebook_type: NotebookType = get_notebook_type()
        if 'sizing_mode' not in kwargs and display_mode == DisplayMode.notebook:
            kwargs['sizing_mode'] = 'stretch_both'
        if use_iframe_in_notebook:
            iframe_style = DEFAULT_IFRAME_STYLE['tabulator'].format(height=height)
        table: Widget = pn.widgets.Tabulator(
            df,
            page_size=page_size if not max_streaming_data else max(page_size, max_streaming_data), 
            header_filters=header_filters,
            disabled=True,  # not allow user to edit the table
            # HACK: jupyter notebook is running in a server, use remote pagination to work around the update error when streaming=True
            # the error is: "ValueError: Must have equal len keys and value when setting with an iterable"
            # FIXME: this is a workaround for a bug in panel Tabulator, see if panel will fix it, or create a github issue
            pagination='local' if notebook_type == NotebookType.vscode else 'remote',
            formatters={
                # NOTE: %f somehow doesn't work for microseconds, and %N (nanoseconds) only preserves up to milliseconds precision
                # so just use %3N to display milliseconds precision
                'ts': DateFormatter(format='%Y-%m-%d %H:%M:%S.%3N')
            },
            **kwargs
        )
    elif dataframe_backend == DataFrameBackend.perspective:
        data_size = df.shape[0]
        if data_size > SUGGESTED_MAX_DATA_SIZE_FOR_PERSPECTIVE:
            print_warning(f"Data size is large (data_size={data_size}), consider using Tabulator backend, which supports for better performance.")
        if use_iframe_in_notebook:
            iframe_style = DEFAULT_IFRAME_STYLE['perspective'].format(height=height)
        table: Pane = pn.pane.Perspective(
            df, 
            sizing_mode='stretch_both', 
            columns_config={
                'ts': {
                    # FIXME: this doesn't work (only 'datetime_color_mode' works), see if panel will fix it, or create a github issue
                    'timeZone': 'Asia/Hong_Kong',  # can't even set timezone to UTC...
                    'dateStyle': 'full',
                    'timeStyle': 'full',
                    # "datetime_color_mode": "background",
                }
            },
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported dataframe backend: {dataframe_backend}")
    
    if not streaming:
        periodic_callback = None
    else:
        n = 0
        def _update_table():
            nonlocal df, n
            # TEMP: fake streaming data
            # NOTE: must be pandas dataframe, pandas series, or dict
            new_data = df.tail(1)
            new_data['symbol'] = f'AAPL_{n}'
            n += 1

            if dataframe_backend == DataFrameBackend.tabulator:
                table.stream(new_data, follow=watch, rollover=max_streaming_data)
            elif dataframe_backend == DataFrameBackend.perspective:
                table.stream(new_data, rollover=max_streaming_data)
        periodic_callback = pn.state.add_periodic_callback(_update_table, period=streaming_freq, start=False)
        
    return render(
        table, 
        display_mode, 
        periodic_callback=periodic_callback, 
        use_iframe_in_notebook=use_iframe_in_notebook,
        iframe_style=iframe_style,
    )
