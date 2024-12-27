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
def orderbook_plot(data: tDataFrame) -> tOutput:
    dataframe_plot(..., dataframe_backend='perspective')