# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalSubscript=false, reportCallIssue=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal, Callable

if TYPE_CHECKING:
    from narwhals.typing import IntoFrame
    from pfund_plot.typing import Style, Control, Plot

import narwhals as nw

from pfund_plot.plots.scatter import Scatter


__all__ = ["Marker"]


class Marker(Scatter):
    """Marker plot that colors points by signal direction.

    Positive signal values (>= 0) get one color/marker, negative values get another.

    Args:
        data: DataFrame with marker positions
        x: Column name for x-axis position
        y: Column name for y-axis position (e.g. 'close' price)
        signal: Column whose sign determines positive/negative styling.
            If None, defaults to the y column.
        pos_color: Color for positive values (default: 'green')
        neg_color: Color for negative values (default: 'red')
        pos_marker: Marker shape for positive values (default: 'triangle_up')
        neg_marker: Marker shape for negative values (default: 'triangle_down')

    Example:
        plt.marker(df, x='date', y='pnl')
        plt.ohlc(df) * plt.marker(df, x='date', y='close', signal='trade')
    """

    def __init__(
        self,
        data: IntoFrame,
        x: str,
        y: str,
        signal: str | None = None,
        pos_color: str='green',
        neg_color: str='red',
        pos_marker: Literal['circle', 'square', 'triangle_up', 'triangle_down', 'diamond', 'cross', 'x', 'star']='triangle_up',
        neg_marker: Literal['circle', 'square', 'triangle_up', 'triangle_down', 'diamond', 'cross', 'x', 'star']='triangle_down',
    ):
        self._signal = signal
        self._pos_color = pos_color
        self._neg_color = neg_color
        self._pos_marker = pos_marker
        self._neg_marker = neg_marker
        super().__init__(data=data, x=x, y=y)
    
    @property
    def _plot_func(self) -> Callable[[nw.DataFrame[Any], Style, Control], Plot]:
        """Runs the plot function for the current backend."""
        import importlib
        module_path = f"pfund_plot.plots.scatter.{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")

    def _standardize_df(self, df: IntoFrame) -> nw.DataFrame[Any]:
        df: nw.DataFrame[Any] = super()._standardize_df(df)
        signal_col = self._signal if self._signal else self._y
        is_positive = nw.col(signal_col) >= 0
        df = df.with_columns(
            nw.when(is_positive)
            .then(nw.lit(self._pos_color))
            .otherwise(nw.lit(self._neg_color))
            .alias('_color'),
            nw.when(is_positive)
            .then(nw.lit(self._pos_marker))
            .otherwise(nw.lit(self._neg_marker))
            .alias('_marker'),
        )
        return df

    def _set_style(self, style: dict[str, Any] | None = None):
        super()._set_style(style)
        if self._style is not None:
            self._style['color'] = '_color'
            self._style['marker'] = '_marker'
