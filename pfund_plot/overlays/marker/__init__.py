# pyright: reportArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame

from pfund_plot.overlays.overlay import BaseOverlay
from pfund_plot.enums import PlottingBackend


__all__ = ["Marker"]


class MarkerStyle:
    from pfund_plot.overlays.marker.bokeh import style as bokeh_style

    bokeh = bokeh_style


class MarkerControl:
    from pfund_plot.overlays.marker.bokeh import control as bokeh_control

    bokeh = bokeh_control


class Marker(BaseOverlay):
    """Generic marker overlay for annotating plots with points/flags.

    Renders scatter points on a host plot's coordinate space. Supports
    per-point styling via DataFrame columns or uniform styling via kwargs.

    Args:
        data: DataFrame with marker positions
        x: Column name for x-axis position
        y: Column name for y-axis position

    Example:
        markers = plt.marker(buy_df, x='date', y='price')
        chart = plt.ohlc(ohlc_df) * markers
    """
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = [PlottingBackend.bokeh]
    style = MarkerStyle
    control = MarkerControl

    def __init__(self, data: IntoFrame, x: str, y: str):
        super().__init__(data=data, x=x, y=y)
