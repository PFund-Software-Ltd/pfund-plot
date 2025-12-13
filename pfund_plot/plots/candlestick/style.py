class CandlestickStyle:
    @property
    def bokeh(self):
        from pfund_plot.plots.candlestick._bokeh import style
        return style

    @property
    def svelte(self):
        from pfund_plot.plots.candlestick._svelte import style
        return style
    