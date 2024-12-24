'''
class StreamingCandlestickFigure(go.Figure):
    def __init__(self, feed: DataFeed, *args, **kwargs):
        self.feed = feed
        initial_data = feed.data
        super().__init__(data=[go.Candlestick(
            x=initial_data.index,
            open=initial_data['open'],
            high=initial_data['high'],
            low=initial_data['low'],
            close=initial_data['close']
        )], *args, **kwargs)
    
    def update(self):
        """Fetch and add new data from the feed."""
        pane = pn.pane.HoloViews(plot)
    
        new_data = feed.get_latest()
        pane.object = new_data.hvplot.line(
            streaming=True,
            window=max_points,
            sliding=True
        )
    
    def stream(self, interval_ms=1000):
        """Start streaming updates with Panel."""
        def update():
            new_data = self.feed.data
            self.add_trace(go.Candlestick(
                x=new_data.index,
                open=new_data['open'],
                high=new_data['high'],
                low=new_data['low'],
                close=new_data['close']
            ))
            return self
            
        self.pane.param.watch(update, 'object')
        return self.pane.servable()
'''

class StreamingPlot:
    def __init__(self, data: tDataFrame | BaseFeed, max_data: int = 5000):
        self.data = data
        self.max_data = max_data
        self.plot = None

    def plot(self):
        pass