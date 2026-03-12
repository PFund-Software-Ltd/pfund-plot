# pyright: reportUnknownMemberType=false, reportGeneralTypeIssues=false, reportUnusedParameter=false, reportUnknownVariableType=false, reportArgumentType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any
if TYPE_CHECKING:
    from narwhals.typing import Frame
    from param.parameterized import Event

import datetime

import narwhals as nw
import panel as pn

from pfund_plot.utils import convert_to_datetime
from pfund_plot.widgets.base import BaseWidget


def round_date(dt: datetime.datetime, to: str = 'floor') -> datetime.datetime:
    """Round a datetime to the nearest second boundary.

    When a user drags the DatetimeRangeSlider, Bokeh snaps BOTH slider handles
    to the nearest step boundary (e.g. every 5000ms). This snapping truncates
    sub-second precision, producing a value like 04:55:19.000 even if the original
    datetime was 04:55:19.732. When that snapped value is synced back to the
    DatetimeRangeInput, Panel validates it against the input's start/end bounds.
    If the bound still has the original sub-second precision (04:55:19.732),
    the snapped value (04:55:19.000) falls outside the bound and validation fails.

    To prevent this, we round the bounds: floor the start date and ceil the end date,
    so the bounds are always wider than any value the slider step quantization can produce.

    Args:
        dt: the datetime to round
        to: 'floor' to round down (strip microseconds), 'ceil' to round up (next whole second)
    """
    if to == 'floor':
        return dt.replace(microsecond=0)
    elif to == 'ceil':
        return dt.replace(microsecond=0) + datetime.timedelta(seconds=1)
    else:
        raise ValueError(f"Invalid rounding direction: {to}, must be 'floor' or 'ceil'")


class DatetimeRangeWidget(BaseWidget):
    def __init__(self, df: nw.DataFrame[Any], control: dict[str, Any], update_callback: Callable[[nw.DataFrame[Any]], None]):
        self._df = df
        self._control: dict[str, Any] = control
        self._update_callback = update_callback
        date_col = self._df['date']
        num_data_shown = date_col.len()
        if 'num_data' in control and control['num_data'] is not None:
            num_data_shown = min(control['num_data'], num_data_shown)
        start_date, end_date = convert_to_datetime(date_col[0]), convert_to_datetime(date_col[-1])
        start_date = round_date(start_date, to='floor')
        end_date = round_date(end_date, to='ceil')
        data_shown_start_date = round_date(convert_to_datetime(date_col[-num_data_shown]), to='floor')
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
            step=control['slider_step'] or self._derive_slider_step()
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

    def get_panel_objects(self) -> list[pn.widgets.Widget]:
        return [self._datetime_range_input, self._datetime_range_slider]

    def _filter_df(self, start_date: datetime.datetime, end_date: datetime.datetime) -> Frame:
        return self._df.filter(
            (nw.col("date") >= start_date) & (nw.col("date") <= end_date)
        )

    def _derive_slider_step(self) -> int:
        date_col = self._df['date']
        # infer resolution from data
        resolution_ms = (date_col[1] - date_col[0]).total_seconds() * 1000
        # use 5x resolution as step, so user can move meaningfully but not too coarsely
        slider_step = int(resolution_ms * 5)
        return slider_step

    def _update_datetime_range_input(self, event: Event):
        start_date, end_date = self._datetime_range_input.value
        # silently update the _datetime_range_slider as well, temporarily remove the watcher
        self._datetime_range_slider.param.unwatch(self._slider_watcher)
        try:
            _ = self._datetime_range_slider.param.update(value=(start_date, end_date))
        finally:
            self._slider_watcher = self._datetime_range_slider.param.watch(self._update_datetime_range_slider, 'value')
        df_filtered = self._filter_df(start_date, end_date)
        self._update_callback(df_filtered)

    def _update_datetime_range_slider(self, event: Event):
        start_date, end_date = self._datetime_range_slider.value
        # silently update the _datetime_range_input as well, temporarily remove the watcher
        self._datetime_range_input.param.unwatch(self._input_watcher)
        try:
            _ = self._datetime_range_input.param.update(value=(start_date, end_date))
        finally:
            self._input_watcher = self._datetime_range_input.param.watch(self._update_datetime_range_input, 'value')
        df_filtered = self._filter_df(start_date, end_date)
        self._update_callback(df_filtered)

    def update_df(self, df: nw.DataFrame[Any]):
        """Update widget bounds and df reference for new df (currently only used when receiving streaming data)."""
        self._df = df
        if self._df.shape[0] < 2:
            raise ValueError("df must have at least 2 rows")
        date_col = df['date']
        new_end = round_date(convert_to_datetime(date_col[-1]), to='ceil')

        self._datetime_range_input.param.unwatch(self._input_watcher)
        self._datetime_range_slider.param.unwatch(self._slider_watcher)
        try:
            # check if slider was at the end before updating
            # NOTE: strip tzinfo before comparing because Panel/Bokeh may return
            # tz-aware datetimes from .value after user interaction
            slider_start, slider_end = self._datetime_range_slider.value

            was_at_end = convert_to_datetime(slider_end) >= convert_to_datetime(self._datetime_range_slider.end)

            # expand bounds
            self._datetime_range_slider.end = new_end
            self._datetime_range_input.end = new_end

            # auto-extend value to include new data if slider was at the end
            if was_at_end:
                _ = self._datetime_range_slider.param.update(value=(slider_start, new_end))
                _ = self._datetime_range_input.param.update(value=(slider_start, new_end))
        finally:
            self._input_watcher = self._datetime_range_input.param.watch(self._update_datetime_range_input, 'value')
            self._slider_watcher = self._datetime_range_slider.param.watch(self._update_datetime_range_slider, 'value')

    # @property
    # def data_slider(self) -> pn.widgets.IntSlider:
    #     return self._data_slider

    # @property
    # def show_all_button(self) -> pn.widgets.Button:
    #     return self._show_all_button

    # def _update_data_slider(self, event: Event):
    #     self._update_callback(self._df.tail(self._data_slider.value))

    # def _max_out_data_slider(self, event: Event):
    #     self._data_slider.value = self._max_data.rx.value
