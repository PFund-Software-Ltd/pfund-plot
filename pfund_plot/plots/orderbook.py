from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import IntoFrameT, FrameT
    from pfeed.types.core import tDataFrame
    from pfeed.feeds.base_feed import BaseFeed
    from pfund_plot.types.literals import tDISPLAY_MODE, tDATAFRAME_BACKEND
    from pfund_plot.types.core import tOutput
    from holoviews.core.overlay import Overlay
    from panel.layout import Panel

import panel as pn

from pfund_plot.plots.dataframe import dataframe_plot
from pfund_plot.const.enums import DisplayMode, DataType, DataFrameBackend
from pfund_plot.utils.validate import validate_data_type
from pfund_plot.renderer import render


# TODO: use perspective to plot orderbook
def orderbook_plot(
    data: tDataFrame | BaseFeed,
    display_mode: tDISPLAY_MODE = 'notebook',
    streaming: bool = False,
    streaming_freq: int = 1000,  # in milliseconds
    height: int = 600,
    **kwargs
) -> tOutput:
    '''
    Args:
        height: height of the orderbook plot in pixels.
            Only applicable when display_mode is 'notebook'.
        kwargs: kwargs for pn.pane.Perspective

    For all the supported kwargs, and more customization examples,
    please refer to https://panel.holoviz.org/reference/panes/Perspective.html.
    '''
    return dataframe_plot(
        data, 
        display_mode=display_mode,
        streaming=streaming,
        streaming_freq=streaming_freq,
        dataframe_backend='perspective', 
        max_streaming_data=1,
        height=height,
        **kwargs
    )
