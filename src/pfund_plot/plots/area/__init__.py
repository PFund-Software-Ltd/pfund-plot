# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame
    from pfeed.feeds.market_feed import MarketFeed

    from pfund_plot.widgets.base import BaseStreamingWidget, BaseWidget

from pfund_plot.enums import PlottingBackend
from pfund_plot.plots.plot import BasePlot
from pfund_plot.widgets.datetime_widget import DatetimeRangeWidget
from pfund_plot.widgets.ticker_widget import TickerSelectWidget

__all__ = ["Area"]


class AreaStyle:
    from pfund_plot.plots.area.bokeh import style as bokeh_style

    bokeh = bokeh_style


class AreaControl:
    from pfund_plot.plots.area.bokeh import control as bokeh_control

    bokeh = bokeh_control


class Area(BasePlot):
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = [PlottingBackend.bokeh]
    SUPPORT_STREAMING: ClassVar[bool] = True
    SUPPORTED_WIDGETS: ClassVar[list[type[BaseWidget]]] = [DatetimeRangeWidget]
    SUPPORTED_STREAMING_WIDGETS: ClassVar[list[type[BaseStreamingWidget]]] = [
        TickerSelectWidget
    ]
    style = AreaStyle
    control = AreaControl

    def __init__(
        self,
        data: IntoFrame | MarketFeed | None = None,
        x: str | None = None,
        y: str | list[str] | None = None,
        y2: str | None = None,
        callback: Callable[..., Any] | None = None,
        name: str | None = None,
        plot_kwargs: dict[str, Any] | None = None,
        **reactive_params: Any,
    ):
        """
        Args:
            data: The dataframe for static plot or pfeed's feed object for streaming plot
            x: Column name for x-positions. If not specified, the index is used.
                Can refer to continuous and categorical data.
            y: Column name for the first y-position (lower bound of the area)
            # REVIEW: y2 is only supported by hvplot
            y2: Column name for the second y-position (upper bound of the area).
                If not specified, the area is drawn from 0 to y.
            callback: A reactive callback function. When provided with **reactive_params,
                auto-creates widgets that re-fetch data on change.
            name: Display name for this plot (used as label when widgets are shown alongside overlays).
                Defaults to the class name lowercased.
            plot_kwargs: keyword arguments for the plot function.
                e.g. if the plot function is hvplot.line, plot_kwargs will be passed to hvplot.line(**plot_kwargs)
            **reactive_params: name=value pairs for reactive widgets (e.g. ticker=["BTC", "ETH"]).
                Requires callback to be set.
        """
        super().__init__(
            data=data,
            x=x,
            y=y,
            callback=callback,
            name=name,
            plot_kwargs=plot_kwargs,
            **reactive_params,
        )
        if y2 is not None:
            self._plot_kwargs["y2"] = y2
