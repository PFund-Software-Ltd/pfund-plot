# ruff: noqa

# /// script
# dependencies = [
#     "marimo",
#     "pfund-plot==0.0.5",
#     "bokeh-sampledata==2025.0",
#     "plotly==6.8.0",
# ]
# requires-python = ">=3.11"
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
async def _():
    # Pyodide bundles outdated pinned wheels (bokeh 3.6.0, typing-extensions
    # 4.11.0) that the header pin can't override, blocking pfund-plot's newer
    # requirements (bokeh>=3.7 via panel>=1.9.3; typing-extensions>=4.14). On
    # WASM, drop those bundled wheels so micropip pulls satisfying versions from
    # PyPI BEFORE pfund_plot is imported/installed. If more bundled-version
    # conflicts surface, add the package + version here. No-op off WASM.
    import sys

    if sys.platform == "emscripten":
        import micropip

        overrides = {"bokeh": "3.8.0", "typing-extensions": "4.14.0"}
        for _pkg in overrides:
            try:
                micropip.uninstall(_pkg)
            except Exception:
                pass
        # bokeh.sampledata imports bokeh_sampledata internally, so marimo's
        # import scanner never sees it and the header entry isn't pulled on
        # WASM — install it explicitly here too.
        reqs = [f"{p}=={v}" for p, v in overrides.items()]
        reqs.append("bokeh-sampledata==2025.0")
        await micropip.install(reqs)
    pfund_plot_ready = True
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import pfund_plot as plt
    import plotly.express as px
    from bokeh.sampledata import stocks

    return mo, pd, plt, px, stocks


@app.cell(hide_code=True)
def _(mo):
    mo.callout(
        mo.md(
            "**Demo mode.** This is `pfund-plot` running in WASM — some features "
            "are not fully supported. (e.g. streaming plots won't work) "
            "For full functionality, install locally:\n\n"
            "```\npip install pfund-plot\n```\n"
            "Click **▶ Run all** (bottom right) to start. First run takes ~20s while Pyodide and dependencies load."
        ),
        kind="info",
    )
    return


@app.cell(hide_code=True)
def _(pd, stocks):
    # Get some sample data:
    df = pd.DataFrame(stocks.AAPL)
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Quick Plot
    """)
    return


@app.cell
def _(df, plt):
    plt.ohlc(df)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Intuitive API (changing the title, disabling the slider widget)
    """)
    return


@app.cell
def _(df, plt):
    plt.ohlc(df).style(title="Apple Stock Price").control(widgets=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Switch Backend
    """)
    return


@app.cell
def _(df, plt):
    candlestick = plt.ohlc(df, name="tradingview").backend("svelte").style(width=1000)
    candlestick
    return (candlestick,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Simple Overlay
    """)
    return


@app.cell(hide_code=True)
def _(df):
    markers = df.assign(
        signal=df["close"] / df["open"].shift(1) - 1,
    ).query("signal > 0.1")
    return (markers,)


@app.cell
def _(df, markers, plt):
    line = plt.line(df, x="date", y="close") * plt.marker(
        markers, x="date", y="close", signal="signal"
    )
    line
    return (line,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Reactive Plots (multiple products)
    """)
    return


@app.cell
def _(df, pd, plt, stocks):
    ohlc = plt.ohlc(
        df,
        callback=lambda product: pd.DataFrame(getattr(stocks, product)),
        product=["AAPL", "GOOG"],
    ).control(widgets=False)
    ohlc
    return (ohlc,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Integration with Other Plotting Libs (e.g. `plotly`)
    """)
    return


@app.cell
def _(df, plt, px):
    plotly_mix = plt.ohlc(df) + plt.plotly(
        px.area(df, x="date", y="volume", title="Apple Trading Volume")
    ).style(width=600)
    plotly_mix
    return (plotly_mix,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tabs
    """)
    return


@app.cell
def _(candlestick, line, ohlc, plotly_mix, plt):
    plt.tabs(
        candlestick,
        line,
        ohlc,
        plt.panel(plotly_mix, name="Plotly Mix"),
    )
    return


if __name__ == "__main__":
    app.run()
