from __future__ import annotations
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from narwhals.typing import Frame
    from holoviews.core.overlay import Overlay
    from panel.layout import Panel
    from pfeed._typing import GenericFrame
    from pfeed.feeds.market_feed import MarketFeed
    from anywidget import AnyWidget
    from panel.pane import Pane
    from pfund_plot._typing import Output, tDisplayMode

import panel as pn
from pfund_plot.plots.plot import Plot
from pfund_plot.plots.candlestick.widgets import CandlestickWidgets
from pfund_plot.enums import NotebookType
from pfund_plot.utils.utils import get_sizing_mode


__all__ = ['candlestick']


class Candlestick(Plot):
    PLOT_TYPE = 'candlestick'
    REQUIRED_COLS = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    def __call__(
        self, 
        df: GenericFrame | None = None,
        style: dict | None = None,
        control: dict | None = None,
        streaming_feed: MarketFeed | None = None,
        streaming_freq: int = 1000,  # in milliseconds
        raw_figure: bool = False,
        mode: tDisplayMode | None = None,
    ) -> Output:
        '''
        Args:
            streaming_freq: the update frequency of the streaming data in milliseconds
            mode: where to display the plot, either "notebook", "browser", or "desktop".
                if None, default to an auto-detected mode
            raw_figure: if True, returns the raw figure object (e.g. bokeh.plotting.figure or plotly.graph_objects.Figure)
                if False, returns the holoviews.core.overlay.Overlay object
        '''
        style, control = self._setup_plotting(df, style, control, streaming_feed, mode)
        self._setup_streaming(streaming_feed, streaming_freq)
        if df is not None:
            df = self._standardize_df(df) 
        if raw_figure:
            fig: AnyWidget | Overlay = self._plot(df, style)
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
    
    # TODO: add ticker selector: ticker = pn.widgets.Select(options=['AAPL', 'IBM', 'GOOG', 'MSFT'], name='Ticker')
    # TODO: use tick data to update the current candlestick
    def plot(self, df: Frame, style: dict, control: dict, streaming_feed: MarketFeed | None=None) -> Output:
        from pfund_plot.renderer import render
        # TODO: add volume plot when show_volume is True
        # show_volume = style['show_volume']
        component: AnyWidget | Pane = self._create_plot(df, style, control)
        widgets = CandlestickWidgets(df, control, self._update_plot)
        # TODO: to be removed, max_data not in use?
        max_data = widgets.max_data
        datetime_range_input, datetime_range_slider = widgets.datetime_range_input, widgets.datetime_range_slider

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

                old_max = max_data.rx.value
                
                # this will also update the slider's end value since it's a reactive object
                max_data.rx.value = df.shape[0]
                
                # if slider was at max, auto-increment to include new data; otherwise, new points aren't visible until manual adjustment
                if data_slider.value == old_max:
                    data_slider.value = max_data.rx.value
                
                new_df = df.tail(data_slider.value)
                pipe.send(new_df)

            periodic_callback = pn.state.add_periodic_callback(_update_plot, period=self._streaming_freq, start=False)  # period in milliseconds
        else:
            periodic_callback = None

        toolbox = pn.FlexBox(datetime_range_input, datetime_range_slider, align_items="center", justify_content="center")
        if self._notebook_type == NotebookType.marimo:
            import marimo as mo
            return mo.vstack([component, toolbox])
        else:
            height = style.get('height', None)
            width = style.get('width', None)
            fig: Panel = pn.Column(
                component,
                toolbox,
                name='Candlestick Chart',
                sizing_mode=get_sizing_mode(height, width),
                # TODO: separate component height and overall figure height
                # height=height + 150,
                height=height,
                width=width,
            )
            return render(fig, mode=self._mode, periodic_callbacks=[periodic_callback])

candlestick = Candlestick()