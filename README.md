# pfund-plot

A high-level out-of-the-box, domain-specific plotting library for **financial data visualization designed for traders**.


> This library is not ready, please wait for version 0.0.1 release.


## Why pfund-plot?
This library is designed for traders who just want to get their data visualized and displayed in the simplest way possible, 
there is almost no learning curve.


## Core Features
- [x] Multi-Display Mode: support displaying plots in a *Jupyter notebook*, *Marimo notebook*, *browser* and *desktop window*
- [x] Streaming Data: support streaming data in real-time by just setting `streaming=True`
- [x] DataFrame Agnostic: support pandas, polars, and dask
- [x] Financial Plots: e.g. candlestick, orderbook, trades etc.



## Installation
```bash
pip install pfund-plot
```


## Usage
```python
import pfund_plot as plt

# TODO: get some sample data using pfeed
data = ...
fig = plt.ohlc(data)
```
