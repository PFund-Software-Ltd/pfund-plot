from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from narwhals.typing import IntoFrame, Frame
    from pfeed._typing import GenericFrame
    from pfeed.feeds.base_feed import BaseFeed
    from pfund_plot._typing import tDisplayMode, tDataframeBackend
    from pfund_plot._typing import Output
    from holoviews.core.overlay import Overlay
    from panel.layout import Panel

import panel as pn

from pfund_plot.plots.dataframe import dataframe_plot
from pfund_plot.enums import DisplayMode, DataType, DataFrameBackend
from pfund_plot.utils.validate import validate_data_type
from pfund_plot.renderer import render


# TODO: use perspective to plot orderbook
def orderbook_plot(
    data: GenericFrame | BaseFeed,
    mode: tDisplayMode = 'notebook',
    streaming: bool = False,
    streaming_freq: int = 1000,  # in milliseconds
    height: int = 600,
    **kwargs
) -> Output:
    '''
    Args:
        height: height of the orderbook plot in pixels.
            Only applicable when mode is 'notebook'.
        kwargs: kwargs for pn.pane.Perspective

    For all the supported kwargs, and more customization examples,
    please refer to https://panel.holoviz.org/reference/panes/Perspective.html.
    '''
    return dataframe_plot(
        data, 
        mode=mode,
        streaming=streaming,
        streaming_freq=streaming_freq,
        backend='perspective', 
        max_streaming_data=1,
        height=height,
        **kwargs
    )
