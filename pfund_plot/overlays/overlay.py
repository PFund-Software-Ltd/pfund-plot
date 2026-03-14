# pyright: reportAttributeAccessIssue=false
from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar, Any

if TYPE_CHECKING:
    from pfund_plot.overlays.lazy import LazyOverlay
    from pfund_plot.typing import Plot

import importlib

import narwhals as nw

from pfund_plot.plots.plot import BasePlot
from pfund_plot.enums import PlottingBackend


class BaseOverlay(BasePlot):
    """A visual layer that composites onto a host plot's coordinate space.

    Extends BasePlot but overrides __new__ to return LazyOverlay (no standalone display),
    and overrides _plot_func to load from pfund_plot.overlays.* instead of pfund_plot.plots.*.

    Overlays don't own axes or widgets — they piggyback on the host plot's
    coordinate space. Examples: markers, trend lines, horizontal lines, bands.
    """
    SUPPORTED_BACKENDS: ClassVar[list[PlottingBackend]] = []

    def __new__(cls, *args: Any, **kwargs: Any) -> LazyOverlay:
        from pfund_plot.overlays.lazy import LazyOverlay

        instance: BaseOverlay = object.__new__(cls)
        instance.__init__(*args, **kwargs)
        return LazyOverlay(instance)

    def _create_component(self) -> None:
        pass

    @property
    def _plot_func(self):
        module_path = f"pfund_plot.overlays.{self.name}.{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")

    def _build_plot(self, df: nw.DataFrame[Any] | None = None) -> Plot:
        return self._plot_func(
            df=df,
            x=self._x,
            y=self._y,
            style=self._style,
            control=self._control,
        )
