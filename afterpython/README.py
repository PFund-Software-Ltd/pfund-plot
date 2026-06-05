# ruff: noqa

# /// script
# dependencies = [
#     "marimo",
#     "pfund-plot==0.0.5",
#     "bokeh-sampledata==2025.0",
#     "altair==6.0.0",
# ]
# requires-python = ">=3.11"
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
async def _():
    import sys

    if sys.platform == "emscripten":
        import micropip

        # Drop the outdated bundled wheels.
        try:
            micropip.uninstall("bokeh")
        except Exception:
            pass
        try:
            micropip.uninstall("typing-extensions")
        except Exception:
            pass
        try:
            micropip.uninstall("altair")
        except Exception:
            pass

        # Reinstall satisfying versions from PyPI.
        await micropip.install("bokeh==3.9.0")
        await micropip.install("typing-extensions==4.14.0")
        await micropip.install("altair==6.0.0")

        # bokeh.sampledata imports bokeh_sampledata internally, so marimo's
        # import scanner never sees it and the header entry isn't pulled on
        # WASM — install it explicitly too.
        await micropip.install("bokeh-sampledata==2025.0")

        await micropip.install("pfund-plot==0.0.5")
        await micropip.install("pyarrow==18.1.0")
        await micropip.install("polars==1.24.0")
        await micropip.install("traitlets==5.14.3")
        await micropip.install("anywidget==0.10.0")
    pfund_plot_ready = True
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import pfund_plot as plt
    from bokeh.sampledata import stocks

    return mo, pd, alt, plt, stocks


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
    ## Integration with Other Plotting Libs (e.g. `altair`)
    """)
    return


@app.cell
def _(alt, df, plt):
    altair_mix = plt.ohlc(df) + plt.altair(
        alt.Chart(df)
        .mark_area()
        .encode(x="date:T", y="volume:Q")
        .properties(title="Apple Trading Volume")
    )
    altair_mix
    return (altair_mix,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tabs
    """)
    return


@app.cell
def _(altair_mix, candlestick, line, ohlc, plt):
    plt.tabs(
        candlestick,
        line,
        ohlc,
        plt.panel(altair_mix, name="Altair Mix"),
    )
    return


if __name__ == "__main__":
    app.run()
