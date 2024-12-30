# PFund-Plot

[![Twitter Follow](https://img.shields.io/twitter/follow/pfund_ai?style=social)](https://x.com/pfund_ai)
![GitHub stars](https://img.shields.io/github/stars/PFund-Software-Ltd/pfund-plot?style=social)
[![Jupyter Notebook](https://img.shields.io/badge/jupyter-notebook-orange?logo=jupyter)](https://jupyter.org)
[![Marimo](https://marimo.io/shield.svg)](https://marimo.io)
![PyPI downloads](https://img.shields.io/pypi/dm/pfund-plot?label=downloads)
[![PyPI](https://img.shields.io/pypi/v/pfund-plot.svg)](https://pypi.org/project/pfund-plot)
![PyPI - Support Python Versions](https://img.shields.io/pypi/pyversions/pfund-plot)

## Problem
Traders often need to quickly visualize their data without investing time in learning new tools.
For example, plotting an orderbook should be as simple as writing a single line of code.

## Solution
We created a high-level plotting library that combines the best features from existing plotting and dashboarding libraries into an easy-to-use interface.

---
<img src="docs/assets/candlestick.gif" alt="pfund-plot candlestick streaming example" width="450">

<!-- <div style="display: flex; justify-content: space-around; align-items: center;">
    <img src="docs/assets/candlestick.gif" alt="pfund-plot streaming example" width="450">
    <img src="docs/assets/orderbook.gif" alt="pfund-plot streaming example" width="450">
</div> -->

---

PFund-Plot is a super high-level, out-of-the-box, domain-specific plotting library designed for traders that supports **financial data visualization**, **dashboard creation**, and **template sharing**.

> This library is not ready, please wait for version 0.0.1 release.

## Core Features
- [x] Multi-Display Mode: support displaying plots in a *Jupyter notebook*, *Marimo notebook*, *browser* and *desktop window*
- [x] Streaming Data: support streaming data in real-time by just setting `streaming=True`
- [x] DataFrame Agnostic: support pandas, polars, and dask
- [x] Big Data Plotting: support plotting large datasets
- [x] Financial Plots: plot financial data by just one function call, e.g. candlestick, orderbook, trades etc.
- [x] Combine multiple plots into a dashboard quickly for visualization


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
