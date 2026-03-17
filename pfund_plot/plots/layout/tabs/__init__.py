from __future__ import annotations
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from panel import Tabs as PanelTabs

import importlib

from pfund_plot.plots.layout.layout import BaseLayout


class TabsStyle:
    from pfund_plot.plots.layout.tabs.panel import style as panel_style

    panel = panel_style


class TabsControl:
    from pfund_plot.plots.layout.tabs.panel import control as panel_control

    panel = panel_control


class Tabs(BaseLayout):
    style = TabsStyle
    control = TabsControl

    # tabs is not at the top level of plots, it's inside layout/tabs, so we need to override the _plot property
    @property
    def _plot_func(self) -> Callable[..., PanelTabs]:
        """Runs the plot function for the current backend."""
        module_path: str = f"pfund_plot.plots.layout.{self._class_name}.{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, "plot")
