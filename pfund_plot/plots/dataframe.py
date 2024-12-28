from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pfeed.types.core import tDataFrame
    from pfeed.feeds.base_feed import BaseFeed
    from pfund_plot.types.literals import tDISPLAY_MODE, tDATAFRAME_BACKEND
    from pfund_plot.types.core import tOutput
    from panel.widgets import Widget

import panel as pn
from bokeh.models.widgets.tables import DateFormatter

from pfeed.etl import convert_to_pandas_df
from pfund_plot.const.enums import DisplayMode, DataType, DataFrameBackend, NotebookType
from pfund_plot.utils.validate import validate_data_type
from pfund_plot.utils.utils import get_notebook_type
from pfund_plot.renderer import render


# EXTEND: maybe add some common functionalities here, e.g. search, sort, filter etc. not sure what users want for now.
def dataframe_plot(
    data: tDataFrame | BaseFeed,
    streaming: bool = False,
    display_mode: tDISPLAY_MODE = "notebook",
    num_points: int = 20,
    streaming_freq: int = 1000,  # in milliseconds
    dataframe_backend: tDATAFRAME_BACKEND = "tabulator",
    hide_cols: list[str] | None = None,
    header_filters: bool = False,
    watch: bool = True,
    **panel_kwargs
) -> tOutput:
    '''
    Args:
        num_points: number of data points to display.
            In this context, it's the number of rows to display, which is the page_size of the Tabulator.
        col_widths: column widths to apply to the Tabulator. unit in pixels.
            e.g. {'column1': 123, 'column2': 456}
            if not provided, use DEFAULT_STYLE['col_widths']
        dataframe_backend: backend to use for the dataframe plot.
            e.g. 'tabulator' or 'perspective'
            use Perspective if data size is large or more complicated data manipulation is needed.
        header_filters: whether to enable header filters in the Tabulator.
        watch: whether to watch the streaming data.
            if true, you will be able to see the table update and scroll along with the new data.
        panel_kwargs: kwargs for pn.widgets.Tabulator, e.g. theme, page_size, etc.

    For all the supported panel_kwargs, and more customization examples,
    please refer to https://panel.holoviz.org/reference/widgets/Tabulator.html
    '''

    display_mode, dataframe_backend = DisplayMode[display_mode.lower()], DataFrameBackend[dataframe_backend.lower()]
    data_type: DataType = validate_data_type(data, streaming, import_hvplot=False)
    notebook_type: NotebookType = get_notebook_type()
    if data_type == DataType.datafeed:
        # TODO: get streaming data in the format of dataframe, and then call _validate_df
        # df = data.get_realtime_data(...)
        pass
    else:
        df = data
    
    if dataframe_backend == DataFrameBackend.tabulator:
        df = convert_to_pandas_df(df)
        table: Widget = pn.widgets.Tabulator(
            df, 
            hidden_columns=hide_cols or [],
            page_size=num_points, 
            header_filters=header_filters,
            disabled=True,  # not allow user to edit the table
            # HACK: jupyter notebook is running in a server, use remote pagination to work around the update error when streaming=True
            # the error is: "ValueError: Must have equal len keys and value when setting with an iterable"
            pagination='local' if notebook_type == NotebookType.vscode else 'remote',
            formatters={
                # NOTE: %f somehow doesn't work for microseconds, and %N (nanoseconds) only preserves up to milliseconds precision
                # so just use %3N to display milliseconds precision
                'ts': DateFormatter(format='%Y-%m-%d %H:%M:%S.%3N')
            },
            **panel_kwargs
        )
    elif dataframe_backend == DataFrameBackend.perspective:
        # TODO
        pass
    
    if streaming:
        n = 0
        def _update_table():
            nonlocal df, n
            # TEMP: fake streaming data
            new_data = df.tail(1)
            new_data['symbol'] = f'AAPL_{n}'
            n += 1

            table.stream(new_data, follow=watch)
        periodic_callback = pn.state.add_periodic_callback(_update_table, period=streaming_freq, start=False)
    else:
        periodic_callback = None
        
    return render(table, display_mode, periodic_callback=periodic_callback)
