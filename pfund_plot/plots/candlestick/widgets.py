from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable
    from narwhals.typing import Frame
    from param.parameterized import Event

import datetime

import narwhals as nw
import panel as pn


class CandlestickWidgets:
    def __init__(self, df: Frame, control: dict, update_plot: Callable):
        self._df: Frame = df
        self._control = control
        self._update_plot = update_plot
        num_data_shown = control['num_data']
        date_col = self._df.select('date')
        start_date, end_date = date_col.row(0)[0].to_pydatetime(), date_col.row(-1)[0].to_pydatetime()
        data_shown_start_date = date_col.row(-num_data_shown)[0].to_pydatetime()
        self._datetime_range_input = pn.widgets.DatetimeRangeInput(
            name='Datetime Range Input',
            start=start_date, end=end_date,
            value=(data_shown_start_date, end_date),
            width=150
        )
        self._input_watcher = self._datetime_range_input.param.watch(self._update_datetime_range_input, 'value')
        self._datetime_range_slider = pn.widgets.DatetimeRangeSlider(
            name='Period',
            start=start_date, end=end_date,
            value=(data_shown_start_date, end_date),
            step=control['slider_step']
        )
        self._slider_watcher = self._datetime_range_slider.param.watch(self._update_datetime_range_slider, 'value')
        # self._max_data = pn.rx(df.shape[0])
        # self._data_slider = pn.widgets.IntSlider(
        #     name='Number of Most Recent Data Points',
        #     value=num_data_shown,
        #     start=control['num_data'],
        #     end=self._max_data,
        #     step=control['slider_step']
        # )
        # self._data_slider.param.watch(self._update_data_slider, 'value')
        # self._show_all_button = pn.widgets.Button(name='Show All', button_type='primary')
        # self._show_all_button.on_click(self._max_out_data_slider)
    
    @property
    def datetime_range_input(self) -> pn.widgets.DatetimeRangeInput:
        return self._datetime_range_input
    
    @property
    def datetime_range_slider(self) -> pn.widgets.DatetimeRangeSlider:
        return self._datetime_range_slider
    
    def _filter_df(self, start_date: datetime.datetime, end_date: datetime.datetime) -> Frame:
        return self._df.filter(
            (nw.col("date") >= start_date) & (nw.col("date") <= end_date)
        )
    
    def _update_datetime_range_input(self, event: Event):
        start_date, end_date = self._datetime_range_input.value
        
        # silently update the _datetime_range_slider as well, temporarily remove the watcher
        self._datetime_range_slider.param.unwatch(self._slider_watcher)
        self._datetime_range_slider.param.update(value=(start_date, end_date))
        self._datetime_range_slider.param.watch(self._update_datetime_range_slider, 'value')
        
        df_filtered = self._filter_df(start_date, end_date)
        self._update_plot(df_filtered)

    def _update_datetime_range_slider(self, event: Event):
        start_date, end_date = self._datetime_range_slider.value
        
        # silently update the _datetime_range_input as well, temporarily remove the watcher
        self._datetime_range_input.param.unwatch(self._input_watcher)
        self._datetime_range_input.param.update(value=(start_date, end_date))
        self._datetime_range_input.param.watch(self._update_datetime_range_input, 'value')
        
        df_filtered = self._filter_df(start_date, end_date)
        self._update_plot(df_filtered)
        
    # @property
    # def data_slider(self) -> pn.widgets.IntSlider:
    #     return self._data_slider
    
    # @property
    # def show_all_button(self) -> pn.widgets.Button:
    #     return self._show_all_button
    
    # def _update_data_slider(self, event: Event):
    #     self._update_plot(self._df.tail(self._data_slider.value))
        
    # def _max_out_data_slider(self, event: Event):
    #     self._data_slider.value = self._max_data.rx.value
    