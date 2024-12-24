from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import IntoFrameT, FrameT
    from pfeed.types.core import tDataFrame
    from pfund_plot.types.core import tFigure
    from pfund_plot.types.literals import tDISPLAY_MODE
    from holoviews.core.overlay import Overlay
    from panel.layout import Panel

import datetime

import panel as pn
import narwhals as nw
from bokeh.models import HoverTool

from pfeed.feeds.base_feed import BaseFeed
from pfund_plot.const.enums import DisplayMode, PlottingBackend, DataType
from pfund_plot.config_handler import get_config
from pfund_plot.utils.validate import validate_input_data
from pfund_plot.utils.utils import is_daily_data
from pfund_plot.renderer import render


config = get_config()
__all__ = ['candlestick_plot']


REQUIRED_COLS = ['ts', 'open', 'high', 'low', 'close', 'volume']
DEFAULT_STYLE = {
    'title': 'Candlestick Chart',
    'ylabel': 'price',
    'xlabel': 'time',
}
# needs a default value for "responsive"=True to work properly in notebook environment
DEFAULT_HEIGHT_FOR_NOTEBOOK = 280


def _validate_df(df: IntoFrameT) -> FrameT:
    df: FrameT = nw.from_native(df)
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
    assert isinstance(df.select('ts').row(0)[0], datetime.datetime), '"ts" column must be of type datetime'
    return df


def _get_style(df: FrameT, display_mode: DisplayMode, height: int | None, width: int | None) -> dict:
    style = DEFAULT_STYLE.copy()
    if height is not None:
        style['height'] = height
    else:
        if display_mode == DisplayMode.notebook:
            style['height'] = DEFAULT_HEIGHT_FOR_NOTEBOOK
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


def _create_hover_tool(df: FrameT) -> HoverTool:
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


# REVIEW: this function only supports bokeh (so no "plotting_backend" in the kwargs), hvplot.ohlc won't work with plotly, probably a bug
def candlestick_plot(
    data: tDataFrame | BaseFeed, 
    streaming: bool = False, 
    display_mode: tDISPLAY_MODE = "notebook", 
    raw_figure: bool = False,
    num_points: int = 100,
    slider_step: int = 100,
    show_volume: bool = True,
    # styling
    up_color: str = 'green',
    down_color: str = 'red',
    bg_color: str = 'white',
    height: int | None = None,
    width: int | None = None,
    grid: bool = True,
) -> tFigure:
    '''
    Args:
        data: the data to plot, either a dataframe or pfeed's feed object
        streaming: if True, the plot will be updated in real-time as new data is received
        display_mode: where to display the plot, either "notebook", "browser", or "desktop"
        raw_figure: if True, returns the raw figure object (e.g. bokeh.plotting.figure or plotly.graph_objects.Figure)
            if False, returns the holoviews.core.overlay.Overlay object
        num_points: the initial number of data points to display.
            This can be changed by a slider in the plot.
        up_color: the color of the up candle, hex code is supported
        down_color: the color of the down candle, hex code is supported
        bg_color: the background color of the plot, hex code is supported
        height: the height of the plot
        width: the width of the plot
    '''
    display_mode, plotting_backend = DisplayMode[display_mode.lower()], PlottingBackend.bokeh
    data_type: DataType = validate_input_data(data)
    
    if not streaming:
        if data_type == DataType.dataframe:
            df: FrameT = _validate_df(data)
            max_num_points = df.shape[0]
            def create_plot(_num_points):
                plot_df: tDataFrame = df.tail(_num_points).to_native()
                return (
                    plot_df
                    .hvplot
                    .ohlc(
                        'ts', ['open', 'low', 'high', 'close'],
                        hover_cols=REQUIRED_COLS,
                        tools=[_create_hover_tool(df)],
                        grid=grid,
                        pos_color=up_color,
                        neg_color=down_color,
                        responsive=True,
                        bgcolor=bg_color,
                    )
                    .opts(
                        **_get_style(df, display_mode, height, width),
                    )
                )
        else:
            # TODO
            feed = data
    else:
        # TODO
        pass
    
    # TODO: add volume plot when show_volume is True
    # TODO: add range selector
    # TODO: date input
     
    if not raw_figure:
        points_slider = pn.widgets.IntSlider(
            name='Number of Most Recent Data Points', 
            value=min(num_points, max_num_points),
            start=num_points,
            end=max_num_points,
            step=slider_step,
        )
        show_all_data_button = pn.widgets.Button(
            name='Show All',
            button_type='primary',
        )
        def update_slider(event):
            points_slider.value = max_num_points
        show_all_data_button.on_click(update_slider)
        fig: Panel = pn.Column(
            pn.bind(create_plot, points_slider.param.value),
            pn.Row(points_slider, show_all_data_button, align='center'),
            sizing_mode='stretch_both',
            name=DEFAULT_STYLE['title'],
        )
    else:
        fig: Overlay = create_plot(max_num_points)
    return render(fig, display_mode, plotting_backend, raw_figure)
