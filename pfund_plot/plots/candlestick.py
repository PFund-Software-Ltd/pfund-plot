from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import IntoFrame, Frame
    from pfeed.typing import GenericFrame
    from pfeed.feeds.base_feed import BaseFeed
    from pfund_plot.types.literals import tDISPLAY_MODE
    from pfund_plot.types.core import tOutput
    from holoviews.core.overlay import Overlay
    from panel.layout import Panel
    
import panel as pn
import narwhals as nw
from bokeh.models import HoverTool, CrosshairTool

from pfund_plot.const.enums import DisplayMode, DataType
from pfund_plot.utils.validate import validate_data_type
from pfund_plot.utils.utils import get_sizing_mode
from pfund_plot.renderer import render
from pfund_plot.state import state


__all__ = ['candlestick_plot']


REQUIRED_COLS = ['ts', 'open', 'high', 'low', 'close', 'volume']
DEFAULT_STYLE = {
    'title': 'Candlestick Chart',
    'ylabel': 'price',
    'xlabel': 'time',
}
# needs a default value for "responsive"=True to work properly in notebook environment
DEFAULT_HEIGHT_FOR_NOTEBOOK = 280


def _validate_df(df: IntoFrame) -> Frame:
    import datetime
    df: Frame = nw.from_native(df)
    if isinstance(df, nw.LazyFrame):
        df = df.collect()
    # convert all columns to lowercase
    df = df.rename({col: col.lower() for col in df.columns})
    # rename 'date' to 'ts'
    if 'date' in df.columns and 'ts' not in df.columns:
        df = df.rename({'date': 'ts'})
    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    ts_value = df.select('ts').row(0)[0]
    # convert ts to datetime if not already
    if not isinstance(ts_value, datetime.datetime):
        # REVIEW: this might mess up the datetime format
        df = df.with_columns(
            nw.col('ts').str.to_datetime(format=None),
        )
    return df


def _get_style(df: Frame, raw_figure: bool, height: int | None = None, width: int | None = None) -> dict:
    style = DEFAULT_STYLE.copy()
    # set height and width if raw_figure is True since pn.Column won't be used
    if raw_figure:
        if height is not None:
            style['height'] = height
        if width is not None:
            style['width'] = width
    product_or_symbol = None
    if 'symbol' in df.columns:
        product_or_symbol = df.select('symbol').row(0)[0]
    elif 'product' in df.columns:
        product_or_symbol = df.select('product').row(0)[0]
    if product_or_symbol:
        style['title'] = f"{product_or_symbol} {style['title']}"
    return style


def _create_hover_tool(df: Frame) -> HoverTool:
    from pfund_plot.utils.utils import is_daily_data
    ts_format = '%Y-%m-%d' if is_daily_data(df) else '%Y-%m-%d %H:%M:%S'
    return HoverTool(
        tooltips=[
            ('ts', f'@ts{{{ts_format}}}'),
            ('open', '@open'),
            ('high', '@high'),
            ('low', '@low'),
            ('close', '@close'),
            ('volume', '@volume'),
        ],
        formatters={'@ts': 'datetime'},
        mode='vline',
    )


def candlestick_plot(
    data: GenericFrame | BaseFeed, 
    streaming: bool = False, 
    display_mode: tDISPLAY_MODE = "notebook", 
    num_data: int = 100,
    raw_figure: bool = False,
    slider_step: int = 100,
    show_volume: bool = True,
    streaming_freq: int = 1000,  # in milliseconds
    # styling
    up_color: str = 'green',
    down_color: str = 'red',
    bg_color: str = 'white',
    height: int | None = None,
    width: int | None = None,
    grid: bool = True,
) -> tOutput:
    '''
    Args:
        data: the data to plot, either a dataframe or pfeed's feed object
        streaming: if True, the plot will be updated in real-time as new data is received
        display_mode: where to display the plot, either "notebook", "browser", or "desktop"
        streaming_freq: the update frequency of the streaming data in milliseconds
        raw_figure: if True, returns the raw figure object (e.g. bokeh.plotting.figure or plotly.graph_objects.Figure)
            if False, returns the holoviews.core.overlay.Overlay object
        num_data: the initial number of data points to display.
            This can be changed by a slider in the plot.
        up_color: the color of the up candle, hex code is supported
        down_color: the color of the down candle, hex code is supported
        bg_color: the background color of the plot, hex code is supported
        height: the height of the plot
        width: the width of the plot
    '''
    # TODO: add volume plot when show_volume is True
    # TODO: add range selector
    # TODO: date input
    # TODO: using tick data to update the current candlestick
    
    
    display_mode = DisplayMode[display_mode.lower()]
    if state.layout.in_layout:
        streaming = streaming or state.layout.streaming
    data_type: DataType = validate_data_type(data, streaming, import_hvplot=True)
    if data_type == DataType.datafeed:
        # TODO: get streaming data in the format of dataframe, and then call _validate_df
        # df = data.get_realtime_data(...)
        pass
    else:
        df = data
    df: Frame = _validate_df(df)
    if display_mode == DisplayMode.notebook:
        height = height or DEFAULT_HEIGHT_FOR_NOTEBOOK
        
    
    # Main Component: candlestick plot
    def _create_plot(_df: Frame, _num_data: int):
        plot_df: GenericFrame = _df.tail(_num_data).to_native()
        return (
            plot_df
            .hvplot
            .ohlc(
                'ts', ['open', 'low', 'high', 'close'],
                hover_cols=REQUIRED_COLS,
                tools=[
                    _create_hover_tool(_df), 
                    CrosshairTool(dimensions='height', line_color='gray', line_alpha=0.3)
                ],
                grid=grid,
                pos_color=up_color,
                neg_color=down_color,
                responsive=True,
                bgcolor=bg_color,
            )
            .opts(**_get_style(_df, raw_figure, height, width))
        )
        
    if raw_figure:
        fig: Overlay = _create_plot(df, _num_data=num_data)
        return fig
    else:
        # Define reactive values    
        max_num_data = pn.rx(df.shape[0])
        
        # Side Components 1: data points slider
        points_slider = pn.widgets.IntSlider(
            name='Number of Most Recent Data Points', 
            value=min(num_data, max_num_data.rx.value),
            start=num_data,
            end=max_num_data,
            step=slider_step,
        )
        
        # Side Components 2: show all data button
        show_all_data_button = pn.widgets.Button(
            name='Show All',
            button_type='primary',
        )
        def max_out_slider(event):
            points_slider.value = max_num_data.rx.value
        show_all_data_button.on_click(max_out_slider)
        

        if not streaming:
            periodic_callback = None
            plot_pane = pn.pane.HoloViews(
                pn.bind(_create_plot, _df=df, _num_data=points_slider)
            )
        else:
            # NOTE: do NOT bind the plot to the slider, otherwise the change of slider value and the periodic callback 
            # will BOTH trigger the plot update, causing an error, probably a race condition
            plot_pane = pn.pane.HoloViews(_create_plot(df, points_slider.value))
            
            def _update_plot():
                # FIXME
                # TEMP: fake streaming data
                import pandas as pd
                nonlocal df
                pandas_df = df.to_native()
                last_ts = pandas_df['ts'].iloc[-1]
                new_ts = last_ts + pd.Timedelta(days=1)
                new_row = pd.DataFrame({
                    'date': [new_ts.date()],
                    'ts': [new_ts],
                    'symbol': ['AAPL'],
                    'product': ['AAPL_USD_STK'],
                    'open': [pandas_df['open'].iloc[-1] * 1.01],  # 1% higher than last price
                    'high': [pandas_df['high'].iloc[-1] * 1.02],
                    'low': [pandas_df['low'].iloc[-1] * 0.99],
                    'close': [pandas_df['close'].iloc[-1] * 1.015],
                    'volume': [int(pandas_df['volume'].iloc[-1] * 0.8)]
                })
                df2 = pd.concat([pandas_df, new_row], ignore_index=True)
                df = nw.from_native(df2)

                # this will also update the slider's end value since it's a reactive object
                max_num_data.rx.value = df.shape[0]
                
                plot_pane.object = _create_plot(df, points_slider.value)

            periodic_callback = pn.state.add_periodic_callback(_update_plot, period=streaming_freq, start=False)  # period in milliseconds
        fig: Panel = pn.Column(
            plot_pane,
            pn.Row(points_slider, show_all_data_button, align='center'),
            name=DEFAULT_STYLE['title'],
            sizing_mode=get_sizing_mode(height, width),
            height=height,
            width=width,
        )
        return render(fig, display_mode, periodic_callbacks=[periodic_callback])
