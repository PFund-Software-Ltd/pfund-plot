# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
    from pfund_plot.widgets.base import BaseWidget, BaseStreamingWidget

from pfund_plot.enums import PlottingBackend
from pfund_plot.plots.plot import BasePlot
from pfund_plot.widgets.datetime_widget import DatetimeRangeWidget
from pfund_plot.widgets.ticker_widget import TickerSelectWidget


__all__ = ["Line"]


class LineStyle:
    from pfund_plot.plots.line.bokeh import style as bokeh_style

    bokeh = bokeh_style

    
class LineControl:
    from pfund_plot.plots.line.bokeh import control as bokeh_control
    
    bokeh = bokeh_control


class Line(BasePlot):
    SUPPORTED_BACKENDS = [PlottingBackend.bokeh]
    SUPPORT_STREAMING: ClassVar[bool] = True
    SUPPORTED_WIDGETS: ClassVar[list[type[BaseWidget]]] = [DatetimeRangeWidget]
    SUPPORTED_STREAMING_WIDGETS: ClassVar[list[type[BaseStreamingWidget]]] = [TickerSelectWidget]
    style = LineStyle
    control = LineControl
