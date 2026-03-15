# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame
    from pfund_plot.widgets.base import BaseWidget

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend
from pfund_plot.widgets.datetime_widget import DatetimeRangeWidget


__all__ = ["Scatter"]


class ScatterStyle:
    from pfund_plot.plots.scatter.bokeh import style as bokeh_style

    bokeh = bokeh_style


class ScatterControl:
    from pfund_plot.plots.scatter.bokeh import control as bokeh_control

    bokeh = bokeh_control


class Scatter(BasePlot):
    """Generic scatter plot — renders points on a 2D plane.

    Supports per-point styling via DataFrame columns or uniform styling via kwargs.
    Works standalone or composed onto another plot via the * operator.

    Args:
        data: DataFrame with point positions
        x: Column name for x-axis position
        y: Column name for y-axis position

    Example:
        plt.scatter(df, x='x', y='y')
        plt.ohlc(ohlc_df) * plt.scatter(df, x='date', y='price')
    """
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = [PlottingBackend.bokeh]
    # TODO: support other streaming feeds like EngineFeed etc.
    # SUPPORT_STREAMING: ClassVar[bool] = True
    SUPPORTED_WIDGETS: ClassVar[list[type[BaseWidget]]] = [DatetimeRangeWidget]
    style = ScatterStyle
    control = ScatterControl

    # TODO: add "by" parameter to group by, see https://hvplot.holoviz.org/en/docs/latest/ref/api/manual/hvplot.hvPlot.scatter.html
    def __init__(self, data: IntoFrame, x: str, y: str):
        super().__init__(data=data, x=x, y=y)
