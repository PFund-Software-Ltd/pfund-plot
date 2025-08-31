from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable
    from narwhals.typing import Frame
    from param.parameterized import Event

import panel as pn


class CandlestickWidgets:
    def __init__(self, df: Frame, control: dict, update_plot: Callable):
        self._df: Frame = df
        self._control = control
        self._max_data = pn.rx(df.shape[0])
        self._update_plot = update_plot
        self._data_slider = pn.widgets.IntSlider(
            name='Number of Most Recent Data Points',
            value=min(control['num_data'], self._max_data.rx.value),
            start=control['num_data'],
            end=self._max_data,
            step=control['slider_step']
        )
        self._data_slider.param.watch(self._update_data_slider, 'value')
        self._show_all_button = pn.widgets.Button(name='Show All', button_type='primary')
        self._show_all_button.on_click(self._max_out_data_slider)
    
    @property
    def max_data(self) -> pn.rx:
        return self._max_data
    
    @property
    def data_slider(self) -> pn.widgets.IntSlider:
        return self._data_slider
    
    @property
    def show_all_button(self) -> pn.widgets.Button:
        return self._show_all_button
    
    def _max_out_data_slider(self, event: Event):
        self._data_slider.value = self._max_data.rx.value
    
    def _update_data_slider(self, event: Event):
        self._update_plot(self._df.tail(self._data_slider.value))