'''
This module is using hvplot with bokeh backend to plot candlestick chart, instead of using bokeh directly.
'''
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import Frame

from bokeh.models import HoverTool, CrosshairTool
    

__all__ = ['plot', 'style']
PLOT_OPTIONS = ['title', 'xlabel', 'ylabel', 'height']


def style(
    title: str = 'Candlestick Chart',
    xlabel: str = 'time',
    ylabel: str = 'price',
    up_color: str = 'green',
    down_color: str = 'red',
    bg_color: str = 'white',
    height: int | None = None,
    width: int | None = None,
    grid: bool = True,
    show_volume: bool = True,
):
    return locals()


def control(
    num_data: int = 100,
    slider_step: int = 100,
):
    return locals()
    

def _create_hover_tool(df: Frame) -> HoverTool:
    from pfund_plot.utils.utils import is_daily_data
    date_format = '%Y-%m-%d' if is_daily_data(df) else '%Y-%m-%d %H:%M:%S'
    return HoverTool(
        tooltips=[
            ('date', f'@date{{{date_format}}}'),
            ('open', '@open'),
            ('high', '@high'),
            ('low', '@low'),
            ('close', '@close'),
            ('volume', '@volume'),
        ],
        formatters={'@date': 'datetime'},
        mode='vline',
    )
    
    
# Define the DynamicMap with the pipe (plot structure created once)
def plot(df: Frame, style: dict):
    from pfund_plot.plots.candlestick import Candlestick
    REQUIRED_COLS = Candlestick.REQUIRED_COLS[:]
    plot_options = {k: v for k, v in style.items() if k in PLOT_OPTIONS}
    return (
        df
        .to_native()
        .hvplot
        .ohlc(
            REQUIRED_COLS[0], REQUIRED_COLS[1:-1],
            hover_cols=REQUIRED_COLS,
            tools=[
                _create_hover_tool(df), 
                CrosshairTool(dimensions='height', line_color='gray', line_alpha=0.3)
            ],
            grid=style['grid'],
            pos_color=style['up_color'],
            neg_color=style['down_color'],
            responsive=True,
            bgcolor=style['bg_color'],
        )
        .opts(**plot_options)
    )