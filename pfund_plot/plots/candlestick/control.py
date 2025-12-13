class CandlestickControl:
    @property
    def bokeh(self):
        from pfund_plot.plots.candlestick._bokeh import control
        return control

    @property
    def svelte(self):
        from pfund_plot.plots.candlestick._svelte import control
        return control