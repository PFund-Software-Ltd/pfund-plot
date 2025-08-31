'''
This module is using hvplot with bokeh backend to plot candlestick chart, instead of using bokeh directly.
'''
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import Frame

from bokeh.models import HoverTool, CrosshairTool


__all__ = ['plot', 'style', 'control']
PLOT_OPTIONS = ['title', 'xlabel', 'ylabel', 'height']  # specified options supported in .opts()


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
    '''
    Args:
        title: the title of the plot
        xlabel: the label of the x-axis
        ylabel: the label of the y-axis
        up_color: the color of the up candle, hex code is supported
        down_color: the color of the down candle, hex code is supported
        bg_color: the background color of the plot, hex code is supported
        height: the height of the plot
        width: the width of the plot
    '''
    from pfund_plot.enums import NotebookType
    from pfund_plot.utils.utils import get_notebook_type, get_sizing_mode
    style_dict = locals()
    # needs a default value for bokeh's "responsive=True" to work properly in notebook environment
    DEFAULT_HEIGHT_FOR_NOTEBOOK = 280
    notebook_type: NotebookType | None = get_notebook_type()
    if notebook_type is not None and height is None:
        height = DEFAULT_HEIGHT_FOR_NOTEBOOK
        style_dict['height'] = height
    style_dict['sizing_mode'] = get_sizing_mode(height, width)
    return style_dict


def control(
    num_data: int = 100,
    slider_step: int = 100,
):
    '''
    Args:
        num_data: the initial number of data points to display.
            This can be changed by a slider in the plot.
        slider_step: the step size of the slider.
    '''
    return locals()
    

def _create_hover_tool(date_format: str) -> HoverTool:
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
    

def _create_crosshair_tool():
    return CrosshairTool(dimensions='height', line_color='gray', line_alpha=0.3)
    

def plot(df: Frame, style: dict):
    from pfund_plot.plots.candlestick import Candlestick
    from pfund_plot.utils.utils import is_daily_data
    date_format = '%Y-%m-%d' if is_daily_data(df) else '%Y-%m-%d %H:%M:%S'
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
                _create_hover_tool(date_format), 
                _create_crosshair_tool(),
            ],
            grid=style['grid'],
            pos_color=style['up_color'],
            neg_color=style['down_color'],
            responsive=True,
            bgcolor=style['bg_color'],
        )
        .opts(**plot_options)
    )