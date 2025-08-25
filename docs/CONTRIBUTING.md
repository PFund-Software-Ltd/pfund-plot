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


## Svelte + AnyWidget Integration

For advanced UI components not available in the Python ecosystem, we use **Svelte components with AnyWidget** integration:

### Architecture Overview
```
pfund-plot/
├── ui/                           # Frontend components
│   ├── src/
│   │   ├── components/           # Pure Svelte components
│   │   │   └── tradingview/
│   │   │       └── Candlestick.svelte
│   │   └── widgets/              # AnyWidget wrappers
│   │       └── tradingview/
│   │           └── candlestick/
│   │               ├── index.ts          # AnyWidget export
│   │               └── CandlestickWrapper.svelte
├── vite.config.ts               # SvelteKit web app & dashboards
└── vite.widget.config.ts        # AnyWidget builds for notebooks
```

### Component Development Workflow

1. **Pure Svelte Components** (`ui/src/components/`)
   - Build reusable UI components independent of AnyWidget
   - Can be used in web apps via `pnpm dev`
   - Example: `Candlestick.svelte` takes `data` prop

2. **AnyWidget Wrappers** (`ui/src/widgets/`)
   - Thin wrappers that handle AnyWidget bindings
   - Each widget folder contains:
     - `index.ts` - exports `defineWidget()`
     - `*Wrapper.svelte` - handles `bindings` prop from Python

3. **Build Process**
   - `pnpm build:widget` - builds widgets for Jupyter/Marimo
   - Auto-discovers all `src/widgets/**/index.ts` files
   - Outputs standalone ES modules in `dist/`


### When to Use Svelte Components
- Complex interactive visualizations (TradingView charts, custom controls)
- JavaScript libraries not available in Python ecosystem
- Need for high-performance frontend interactions
- Custom UI components that benefit from reactive frameworks

### Development Commands
```bash
cd ui/
pnpm dev                    # Develop components in web app
pnpm build:widget:watch     # Build widgets with hot reload
pnpm build:widget           # Production widget builds
```


## Dataframe Manipulation
`pfund-plot` supports `pandas`, `polars` and `dask` dataframes. If you need to manipulate the input dataframe, please use the [narwhals] library.


## Example
Your function will look something like this:
```python
# GenericFrame is just a type alias for pandas, polars and dask dataframes
from pfeed.typing import GenericFrame
from typing import Literal
from pfund_plot.renderer import render


def your_plot(
    data: GenericFrame,
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
