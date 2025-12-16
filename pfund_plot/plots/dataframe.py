from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfeed._typing import GenericFrame
    from pfeed.feeds.base_feed import BaseFeed
    from pfund_plot._typing import tDisplayMode, tDataframeBackend
    from pfund_plot._typing import RenderedResult
    from panel.widgets import Widget
    from panel.pane import Pane

import panel as pn
from bokeh.models.widgets.tables import DateFormatter

from pfeed._etl.base import convert_to_pandas_df
from pfund_plot.enums import DisplayMode, DataFrameBackend, NotebookType
from pfund_plot.utils.utils import get_notebook_type
from pfund_plot.state import state


__all__ = ['dataframe_plot']


SUGGESTED_MAX_DATA_SIZE_FOR_PERSPECTIVE = 10000
SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR = 11
DEFAULT_IFRAME_STYLE = {
    # 'tabulator': "width: 100vw; height: {height}px;",
    'perspective': "display: block; width: {width}; height: {height}; border: none;",
}
DEFAULT_HEIGHT_FOR_NOTEBOOK = 650


# EXTEND: maybe add some common functionalities here, e.g. search, sort, filter etc. not sure what users want for now.
def dataframe_plot(
    data: GenericFrame | BaseFeed,
    mode: tDisplayMode = "notebook",
    backend: tDataframeBackend = "tabulator",
    streaming: bool = False,
    streaming_freq: int = 1000,  # in milliseconds
    max_streaming_data: int | None = None,
    watch: bool = True,
    page_size: int = 20,
    header_filters: bool = False,
    height: int | None = None,
    width: int | None = None,
    **kwargs
) -> RenderedResult:
    '''
    Args:
        data: the data to plot, either a dataframe or pfeed's feed object
        mode: where to display the plot, either "notebook", "browser", or "desktop"
        streaming: if True, the plot will be updated in real-time as new data is received
        streaming_freq: the update frequency of the streaming data in milliseconds
        max_streaming_data: maximum number of data points used when streaming.
            If None, data will continue to grow unbounded.
        backend: backend to use for the dataframe plot.
            e.g. 'tabulator' or 'perspective'
            use Perspective if data size is large or more complicated data manipulation is needed.
        page_size: number of data points to display on each page when using Tabulator backend.
        header_filters: whether to enable header filters when using Tabulator backend.
        watch: whether to watch the streaming data when using Tabulator backend.
            if true, you will be able to see the table update and scroll along with the new data.
        height: the height of the dataframe plot in pixels.
        width: the width of the dataframe plot in pixels.
        kwargs: kwargs for pn.widgets.Tabulator or pn.pane.Perspective

    For all the supported kwargs, and more customization examples,
    please refer to https://panel.holoviz.org/reference/widgets/Tabulator.html for Tabulator backend,
    and https://panel.holoviz.org/reference/panes/Perspective.html for Perspective backend.
    '''
    from pfund_plot import print_warning


    mode, backend = DisplayMode[mode.lower()], DataFrameBackend[backend.lower()]
    if state.layout.in_layout:
        streaming = streaming or state.layout.streaming
    data_type: DataType = validate_data_type(data, streaming, import_hvplot=False)
    if data_type == DataType.datafeed:
        # TODO: get streaming data in the format of dataframe, and then call _validate_df
        # df = data.get_realtime_data(...)
        pass
    else:
        df = data
    df = convert_to_pandas_df(df)

    use_iframe_in_notebook, iframe_style = False, None
    if mode == DisplayMode.notebook:
        use_iframe_in_notebook = (backend == DataFrameBackend.perspective)
        height = height or DEFAULT_HEIGHT_FOR_NOTEBOOK
    if 'sizing_mode' not in kwargs:
        kwargs['sizing_mode'] = get_sizing_mode(height, width)


    if backend == DataFrameBackend.tabulator:
        if max_streaming_data is not None and max_streaming_data < SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR:
            # FIXME: this is a workaround for a bug in panel Tabulator, see if panel will fix it, or create a github issue
            print_warning(
                f"max_streaming_data < {SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR} will lead to buggy behaviors (possibly a bug in panel Tabulator's rollover). "
                f"Setting max_streaming_data to {SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR}."
            )
            max_streaming_data = SUGGESTED_MIN_STREAMING_DATA_FOR_TABULATOR
        notebook_type: NotebookType = get_notebook_type()
        # FIXME: this is a workaround for a bug in panel Tabulator, see if panel will fix it, or create a github issue
        if mode == DisplayMode.notebook and notebook_type in [NotebookType.jupyter, NotebookType.marimo]:
            pagination = 'remote'
        else:
            pagination = 'local'
        table: Widget = pn.widgets.Tabulator(
            df,
            page_size=page_size if not max_streaming_data else max(page_size, max_streaming_data), 
            header_filters=header_filters,
            disabled=True,  # not allow user to edit the table
            pagination=pagination,
            formatters={
                # NOTE: %f somehow doesn't work for microseconds, and %N (nanoseconds) only preserves up to milliseconds precision
                # so just use %3N to display milliseconds precision
                'date': DateFormatter(format='%Y-%m-%d %H:%M:%S.%3N')
            },
            height=height,
            width=width, 
            **kwargs
        )
    elif backend == DataFrameBackend.perspective:
        data_size = df.shape[0]
        if data_size > SUGGESTED_MAX_DATA_SIZE_FOR_PERSPECTIVE:
            print_warning(f"Data size is large (data_size={data_size}), consider using Tabulator backend, which supports for better performance.")
        if use_iframe_in_notebook:
            iframe_height = height + 10  # add 10px to avoid scrollbar from appearing
            iframe_style = DEFAULT_IFRAME_STYLE['perspective'].format(height=f'{iframe_height}px', width='100%' if width is None else f'{width}px')
        table: Pane = pn.pane.Perspective(
            df, 
            columns_config={
                'date': {
                    # FIXME: this doesn't work (only 'datetime_color_mode' works), see if panel will fix it, or create a github issue
                    'timeZone': 'Asia/Hong_Kong',  # can't even set timezone to UTC...
                    'dateStyle': 'full',
                    'timeStyle': 'full',
                    # "datetime_color_mode": "background",
                }
            },
            height=height,
            width=width,
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported dataframe backend: {backend}")
    
    if not streaming:
        periodic_callback = None
    else:
        n = 0
        def _update_table():
            nonlocal df, n
            # TEMP: fake streaming data
            # NOTE: must be pandas dataframe, pandas series, or dict
            new_data = df.tail(1)
            if 'symbol' in new_data.columns:
                new_data['symbol'] = f'AAPL_{n}'
            n += 1

            if backend == DataFrameBackend.tabulator:
                table.stream(new_data, follow=watch, rollover=max_streaming_data)
            elif backend == DataFrameBackend.perspective:
                table.stream(new_data, rollover=max_streaming_data)
        periodic_callback = pn.state.add_periodic_callback(_update_table, period=streaming_freq, start=False)
        
    return render(
        table, 
        mode, 
        periodic_callbacks=[periodic_callback], 
        use_iframe_in_notebook=use_iframe_in_notebook,
        iframe_style=iframe_style,
    )
