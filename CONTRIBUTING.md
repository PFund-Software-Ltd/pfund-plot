## Features:
### 1. Plotting:
> A prepackaged solution for different types of plots based on various types of financial data
#### Requirements
- can be rendered in notebooks, web browser and desktop window
- supports interactivity and real-time data streaming
    - for data streaming, only supports plotly and bokeh (hvplot), rendered using panel

#### Libraries:
- hvplot is the default plotting library (bokeh backend)
    - jupyter-bokeh is for using bokeh (hvplot) in jupyter notebook
    - datashader is for plotting big data
- if hvplot doesn't support a plot type, use plotly directly
- if performance is an issue, use perspective-python for streaming big data

---
### 2. Dashboard generation = Curated plots in a dashboard
> use panel to render the plots
```
run_dashboard(
    line_plot(custom_data),
    bar_plot(
        pfeed.get_historical_data(...)
    ),
    scatter_plot(
        pfolio.analyze_portfolio(...)
    ),
    ...,
    some_layout_settings,
)
```

---
## 3. Templating (notebooks/dashboards/spreadsheets)
- parametrized by data feeds (feed objects from pfeed)
- e.g. `python custom_notebook.py --feed bybit okx`
> backtest result is considered as a data feed as well. (using pfeed's BacktestEngineFeed)
- should find a way to lock pfeed's version and the framework's version (e.g. streamlit)
- how to handle other dependencies? find a way to install them
- need to handle security issues, since users will be running someone's code
- a template can support multiple data feeds as long as they are compatible.
but the switching will be handled in the template, e.g.
```
if data_feed == bybit:
    feed = BybitFeed()
elif data_feed == binance:
    feed = BinanceFeed()
```
- in the end, if for production use, need to think about auth etc.
