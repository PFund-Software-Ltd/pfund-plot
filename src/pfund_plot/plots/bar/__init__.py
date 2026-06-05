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

__all__ = ["Bar"]


class BarStyle:
    from pfund_plot.plots.bar.bokeh import style as bokeh_style

    bokeh = bokeh_style


class BarControl:
    from pfund_plot.plots.bar.bokeh import control as bokeh_control

    bokeh = bokeh_control


class Bar(BasePlot):
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = [PlottingBackend.bokeh]
    SUPPORT_STREAMING: ClassVar[bool] = True
    SUPPORTED_WIDGETS: ClassVar[list[type[BaseWidget]]] = [DatetimeRangeWidget]
    SUPPORTED_STREAMING_WIDGETS: ClassVar[list[type[BaseStreamingWidget]]] = [
        TickerSelectWidget
    ]
    style = BarStyle
    control = BarControl

    def __init__(
        self,
        data: IntoFrame | MarketFeed | None = None,
        x: str | None = None,
        y: str | list[str] | None = None,
        by: str | list[str] | None = None,
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
            y: Column name for the y-position.
            by: A single column or list of columns to group by. All the subgroups are visualized.
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
        if by is not None:
            self._plot_kwargs["by"] = by
