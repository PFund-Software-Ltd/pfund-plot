from __future__ import annotations

from pfund_plot.plots.lazy import LazyPlot

_STANDALONE_ERROR = (
    "Overlays cannot be displayed standalone. "
    "Compose onto a plot: plt.ohlc(df) * plt.marker(df)"
)


class LazyOverlay(LazyPlot):
    """Lazy overlay builder that defers rendering until composed with a plot.

    Extends LazyPlot but disables standalone display — must be
    composed onto a LazyPlot via the * operator.

    Example:
        markers = plt.marker(df, x='date', y='price', color='green')
        chart = plt.ohlc(ohlc_df) * markers
    """

    def show(self):
        raise TypeError(_STANDALONE_ERROR)

    async def show_async(self):
        raise TypeError(_STANDALONE_ERROR)

    def servable(self, title=None):
        raise TypeError(_STANDALONE_ERROR)

    def _repr_mimebundle_(self, include=None, exclude=None):
        raise TypeError(_STANDALONE_ERROR)

    def _repr_html_(self):
        raise TypeError(_STANDALONE_ERROR)
