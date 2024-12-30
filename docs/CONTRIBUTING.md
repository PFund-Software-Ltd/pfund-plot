[hvplot]: https://hvplot.holoviz.org/
[holoviews]: https://holoviews.org/
[panel]: https://panel.holoviz.org/
[plotly]: https://plotly.com/
[altair]: https://altair-viz.github.io/
[narwhals]: https://github.com/narwhals-dev/narwhals


# CONTRIBUTING

Thank you for your interest in contributing to PFund-Plot! This guide will help you get started.


## Development Setup
```bash
git clone https://github.com/PFund-Software-Ltd/pfund-plot.git
cd pfund-plot
poetry install --with dev,test --all-extras
```


## Adding a new plot
1. if the plot is supported by [hvplot], use hvplot to implement the plot
2. if the plot is not supported by hvplot, use [holoviews] to implement the plot
3. if holoviews doesn't support the plot, use [panel] to implement the plot

> Panel can be used as the standardized interface for different plotting libraries.

e.g. if you want to use `plotly`
```python
import panel as pn
import plotly.graph_objects as go
from pfund_plot.renderer import render

# your plotly figure
fig = go.Figure(...)

# convert plotly figure to panel
panel_fig = pn.pane.Plotly(fig)

# pass the panel figure to the render function
render(panel_fig)
```

e.g. if you want to use `altair`
```python
import panel as pn
import altair as alt
from pfund_plot.renderer import render

# your altair figure
fig = alt.Chart(...)

# convert altair figure to panel
panel_fig = pn.pane.Vega(fig)

# pass the panel figure to the render function
render(panel_fig)
```

The same logic can be applied to other plotting libraries as long as `panel` supports them.
e.g. there are also `pn.pane.Bokeh`, `pn.pane.Matplotlib`, `pn.pane.ECharts`, `pn.pane.HoloViews`, etc.


## Dataframe Manipulation
`pfund-plot` supports `pandas`, `polars` and `dask` dataframes. If you need to manipulate the input dataframe, please use the [narwhals] library.


## Example
Your function will look something like this:
```python
# tDataFrame is just a type alias for pandas, polars and dask dataframes
from pfeed.types.core import tDataFrame
from typing import Literal
from pfund_plot.renderer import render


def your_plot(
    data: tDataFrame,
    streaming: bool = False,
    display_mode: Literal['notebook', 'browser', 'desktop'] = "notebook",
    raw_figure: bool = False,  # add this if your function uses hvplot
):
    # your plotting logic
    ...
    return render(panel_fig)
```

For a full example, see the function `candlestick_plot()` in `pfund_plot/plots/candlestick.py`.
It is a standard way to make a plot using hvplot, and pn.state.add_periodic_callback() to make the plot streaming.
