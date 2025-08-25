from typing import TYPE_CHECKING, Callable

import importlib

from pfund_plot.enums import PlottingBackend


class Control:
    def __init__(self, backend: PlottingBackend, plot_type: str):
        self._backend = backend
        self._plot_type = plot_type
    
    def _get_control_function(self) -> Callable[..., dict]:
        """Dynamically import the control function for the current backend and plot type."""
        module_path = f"pfund_plot.plots.{self._plot_type}._{self._backend}"
        module = importlib.import_module(module_path)
        return getattr(module, 'control')
    
    @property
    def bokeh(self):
        if TYPE_CHECKING:
            # For type hints, import the specific svelte style function
            from pfund_plot.plots.candlestick import Candlestick
            if self._plot_type == Candlestick.PLOT_TYPE:
                from pfund_plot.plots.candlestick._bokeh import control
                return control
        assert self._backend == PlottingBackend.bokeh, "Backend is not bokeh"
        return self._get_control_function()
    
    @property
    def svelte(self):
        if TYPE_CHECKING:
            # For type hints, import the specific svelte style function
            from pfund_plot.plots.candlestick import Candlestick
            if self._plot_type == Candlestick.PLOT_TYPE:
                from pfund_plot.plots.candlestick._svelte import control
                return control
        assert self._backend == PlottingBackend.svelte, "Backend is not svelte"
        return self._get_control_function()
    
    def __call__(self):
        if self._backend == PlottingBackend.bokeh:
            return self.bokeh()
        elif self._backend == PlottingBackend.svelte:
            return self.svelte()
        else:
            raise ValueError(f"Unsupported backend: {self._backend}")