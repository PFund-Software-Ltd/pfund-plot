from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from narwhals.typing import Frame
    from holoviews.core.overlay import Overlay
    from panel.layout import Panel
    from pfeed._typing import GenericFrame
    from pfeed.feeds.market_feed import MarketFeed
    from pfund_plot._typing import tOutput

from pfund_plot.plots.plot import Plot


__all__ = ['candlestick']


class Candlestick(Plot):
    PLOT_TYPE = 'candlestick'
    REQUIRED_COLS = ['date', 'open', 'high', 'low', 'close', 'volume']
    # needs a default value for bokeh's "responsive=True" to work properly in notebook environment
    DEFAULT_HEIGHT_FOR_NOTEBOOK = 280
    
    def __call__(
        self, 
        df: GenericFrame | None = None,
        style: dict | None = None,
        control: dict | None = None,
        streaming_feed: MarketFeed | None = None,
        streaming_freq: int = 1000,  # in milliseconds
        raw_figure: bool = False,
    ) -> tOutput:
        style, control = self._setup_plotting(df, style, control, streaming_feed)
        self._setup_streaming(streaming_feed, streaming_freq)
        style, control = self._adjust_style(style).copy(), control.copy()
        if df is not None:
            df = self._standardize_df(df) 
        if raw_figure:  # FIXME: only handles bokeh
            fig: Overlay = self._plot(df, style)
            return fig
        else:
            return self.plot(df, style, control, streaming_feed=streaming_feed)

    def set_backend(self, backend: Literal['bokeh', 'svelte']):
        return super().set_backend(backend)
        
    def _standardize_df(self, df: GenericFrame) -> Frame:
        import datetime
        import narwhals as nw
        df: Frame = nw.from_native(df)
        if isinstance(df, nw.LazyFrame):
            df = df.collect()
        # convert all columns to lowercase
        df = df.rename({col: col.lower() for col in df.columns})
        # rename 'datetime' to 'date'
        if 'datetime' in df.columns and 'date' not in df.columns:
            df = df.rename({'datetime': 'date'})
        missing_cols = [col for col in self.REQUIRED_COLS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        date_value = df.select('date').row(0)[0]
        # convert date to datetime if not already
        if not isinstance(date_value, datetime.datetime):
            # REVIEW: this might mess up the datetime format
            df = df.with_columns(
                nw.col('date').str.to_datetime(format=None),
            )
        return df
    
    def _adjust_style(self, style: dict) -> dict:
        from pfund_plot.enums import DisplayMode
        if self._mode == DisplayMode.notebook:
            style['height'] = style['height'] or self.DEFAULT_HEIGHT_FOR_NOTEBOOK
        return style
        
    def plot(self, df: Frame, style: dict, control: dict, streaming_feed: MarketFeed | None=None) -> tOutput:
        '''
        Args:
            data: the data to plot, either a dataframe or pfeed's feed object
            streaming: if True, the plot will be updated in real-time as new data is received
            mode: where to display the plot, either "notebook", "browser", or "desktop"
            streaming_freq: the update frequency of the streaming data in milliseconds
            raw_figure: if True, returns the raw figure object (e.g. bokeh.plotting.figure or plotly.graph_objects.Figure)
                if False, returns the holoviews.core.overlay.Overlay object
            num_data: the initial number of data points to display.
                This can be changed by a slider in the plot.
            up_color: the color of the up candle, hex code is supported
            down_color: the color of the down candle, hex code is supported
            bg_color: the background color of the plot, hex code is supported
            height: the height of the plot
            width: the width of the plot
        '''
        # TODO: add volume plot when show_volume is True
        # TODO: add range selector
        # TODO: date input
        # TODO: using tick data to update the current candlestick
        import panel as pn
        from holoviews import DynamicMap
        from holoviews.streams import Pipe

        from pfund_plot.utils.utils import get_sizing_mode
        from pfund_plot.renderer import render
        
        periodic_callback = None
        show_volume = style['show_volume']  # TODO
        height, width = style['height'], style['width']
        
        # Define reactive values
        max_num_data = pn.rx(df.shape[0])
        
        # Side Components 1: data points slider
        # TODO: specific to panel or bokeh?
        num_data, slider_step = control['num_data'], control['slider_step']
        points_slider = pn.widgets.IntSlider(
            name='Number of Most Recent Data Points', 
            value=min(num_data, max_num_data.rx.value),
            start=num_data,
            end=max_num_data,
            step=slider_step,
        )
        
        # Side Components 2: show all data button
        show_all_data_button = pn.widgets.Button(
            name='Show All',
            button_type='primary',
        )
        
        # Create a Pipe stream for data updates
        pipe = Pipe(data=df.tail(min(num_data, df.shape[0])))

        # Update function: send new tail of data via pipe on slider change
        def _update_data(event):
            new_data = df.tail(points_slider.value)
            pipe.send(new_data)
        points_slider.param.watch(_update_data, 'value')

        # Also update for show_all_data_button
        def _max_out_slider(event):
            points_slider.value = max_num_data.rx.value
            _update_data(None)  # Trigger update
        show_all_data_button.on_click(_max_out_slider)
            
        dmap = DynamicMap(lambda data: self._plot(data, style), streams=[pipe])
        pane = pn.pane.HoloViews(dmap)

        if self.is_streaming():
            def _update_plot():
                # data.stream()? in a thread? passed into render()?
                # FIXME
                # TEMP: fake streaming data
                import pandas as pd
                nonlocal df
                pandas_df = df.to_native()
                last_date = pandas_df['date'].iloc[-1]
                new_date = last_date + pd.Timedelta(days=1)
                new_row = pd.DataFrame({
                    'date': [new_date],
                    # 'symbol': ['AAPL'],
                    # 'product': ['AAPL_USD_STK'],
                    'open': [pandas_df['open'].iloc[-1] * 1.01],  # 1% higher than last price
                    'high': [pandas_df['high'].iloc[-1] * 1.02],
                    'low': [pandas_df['low'].iloc[-1] * 0.99],
                    'close': [pandas_df['close'].iloc[-1] * 1.015],
                    'volume': [int(pandas_df['volume'].iloc[-1] * 0.8)]
                })
                df2 = pd.concat([pandas_df, new_row], ignore_index=True)
                df = nw.from_native(df2)

                old_max = max_num_data.rx.value
                
                # this will also update the slider's end value since it's a reactive object
                max_num_data.rx.value = df.shape[0]
                
                # if slider was at max, auto-increment to include new data; otherwise, new points aren't visible until manual adjustment
                if points_slider.value == old_max:
                    points_slider.value = max_num_data.rx.value
                
                new_data = df.tail(points_slider.value)
                pipe.send(new_data)

            periodic_callback = pn.state.add_periodic_callback(_update_plot, period=self._streaming_freq, start=False)  # period in milliseconds

        fig: Panel = pn.Column(
            pane,
            pn.Row(points_slider, show_all_data_button, align='center'),
            name='Candlestick Chart',
            sizing_mode=get_sizing_mode(height, width),
            height=height,
            width=width,
        )
        return render(fig, self._mode, periodic_callbacks=[periodic_callback])

candlestick = Candlestick()