import marimo

__generated_with = "0.21.0"
app = marimo.App(width="columns")

with app.setup:
    import marimo as mo
    import holoviews as hv
    import matplotlib.pyplot as mpl
    import plotly.graph_objects as go
    import altair as alt
    from bokeh.plotting import figure
    import numpy as np
    import polars as pl
    import pfeed as pe
    import pfund_plot as plt

    feed = pe.Bybit(pipeline_mode=True).market_feed
    products = ['ETH_USDT_PERP', 'BTC_USDT_PERP']
    date = '2026-03-01'
    resolution = '1h'
    storage = 'local'

    # FIXME: use pfund-sampledata when its ready
    for product in products:
        for func in [feed.retrieve, feed.download]:
            df = func(
                product=product,
                resolution=resolution,
                start_date=date,
                end_date=date,
                storage_config=pe.StorageConfig(
                    storage=storage,
                )
            ).run()
            if df is not None:
                break

    # create some fake columns for plt.marker and plt.label
    df = df.collect()
    df = df.with_columns(
        pl.Series('trade', np.random.choice([1, -1], size=len(df))),
    ).with_columns(
        pl.when(pl.col('trade') == 1).then(pl.lit('buy')).otherwise(pl.lit('sell')).alias('label')
    )


@app.cell
def _():
    mo.md("""
    # Gallery
    This is a gallery of plots supported by `pfund-plot` for maintainers to quickly visualize them to make sure they are working correctly. Press `Cmd + .` to toggle the app view to see all the plots nicely.
    > WARNING: somehow some widgets don't work in app view or even after switching back from the app view. So you might want to manually test the widgets a bit before toggling it.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Data Used in the Gallery
    """)
    return


@app.cell
def _():
    df.head()
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # 1. Candlestick
    """)
    return


@app.cell
def _():
    candlestick = plt.ohlc(df).backend('bokeh')
    candlestick
    return (candlestick,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # 2. Line
    """)
    return


@app.cell
def _():
    line = plt.line(df, x='date', y='close').style(color='orange').control(widgets=False)
    line
    return (line,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # 3. Scatter
    """)
    return


@app.cell
def _():
    scatter = plt.scatter(df, x='open', y='close').control(widgets=False)
    scatter
    return (scatter,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # 4. Marker
    """)
    return


@app.cell
def _():
    marker = plt.marker(df, x='date', y='close', signal='trade')
    marker
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # 5. Label
    """)
    return


@app.cell
def _():
    label = plt.label(df, x='date', y='close', text='label')
    label
    return


@app.cell(column=1, hide_code=True)
def _():
    mo.md(r"""
    # Operations: "+" and "|"
    """)
    return


@app.cell
def _(candlestick, line, scatter):
    (candlestick + line) | scatter
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Overlays: "*"
    """)
    return


@app.cell
def _():
    plt.ohlc(df).backend('bokeh') * plt.label(df, x='date', y='close', text='label') * plt.marker(df, x='date', y='close', signal='trade')
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Plotly Wrapper: `plt.plotly`
    """)
    return


@app.cell
def _():
    plotly_fig = go.Figure()
    plotly_fig.add_trace(go.Scatter(x=df["date"], y=df["close"], mode="lines"))
    plotly_fig.update_layout(title="Price", xaxis_title="date", yaxis_title="close")
    plotly_fig = plt.plotly(plotly_fig, sizing_mode='stretch_width')
    plotly_fig
    return (plotly_fig,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Altair Wrapper: `plt.altair`
    """)
    return


@app.cell
def _():
    altair_fig = plt.altair(
        alt.Chart(df).mark_line().encode(
            x="date:T",
            y=alt.Y("close:Q").scale(zero=False),
            tooltip=["date:T", "close:Q"],
        ).properties(
            title="Price",
            width=600,
            height=400,
        ),
        sizing_mode='stretch_width'
    )
    altair_fig
    return (altair_fig,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Matplotlib Wrapper: `plt.matplotlib`
    """)
    return


@app.cell
def _():
    matplotlib_fig, ax = mpl.subplots()
    ax.plot(df["date"], df["close"])
    ax.set_title("Price")
    ax.set_xlabel("date")
    ax.set_ylabel("close")
    matplotlib_fig = plt.matplotlib(matplotlib_fig, height=500, sizing_mode='stretch_width')
    matplotlib_fig
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Bokeh Wrapper: `plt.bokeh`
    """)
    return


@app.cell
def _():
    bokeh_fig = figure(title="Price", x_axis_label="date", y_axis_label="close", x_axis_type="datetime", height=400, width=700)
    bokeh_fig.line(df["date"], df["close"])
    bokeh_fig = plt.bokeh(bokeh_fig, sizing_mode='stretch_width')
    bokeh_fig
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Holoviews Wrapper: `plt.holoviews`
    """)
    return


@app.cell
def _():
    holoviews_fig = hv.Curve(df, kdims="date", vdims="close").opts(title="Price")
    holoviews_fig = plt.holoviews(holoviews_fig, sizing_mode='stretch_width')
    holoviews_fig
    return


@app.cell(column=2, hide_code=True)
def _():
    mo.md(r"""
    # Reactive Widgets
    """)
    return


@app.cell
def _():
    def get_df(product, resolution):
        return feed.retrieve(
            product=product,
            resolution=resolution,
            start_date=date,
            end_date=date,
            storage_config=pe.StorageConfig(
                storage=storage,
            )
        ).run()

    reactive_candlestick = plt.ohlc(
        get_df(products[0], resolution),
        callback=get_df,
        product=products,
        resolution=[resolution],
    )
    reactive_candlestick
    return (reactive_candlestick,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Tabs
    """)
    return


@app.cell
def _(altair_fig, line, plotly_fig, reactive_candlestick):
    tabs = plt.tabs(
        reactive_candlestick,
        line,
        plotly_fig,
        altair_fig,
    )
    tabs
    return (tabs,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Layout + Streaming
    > put streaming plot inside layout so that we can stop them both at the same time
    """)
    return


@app.cell
def _(altair_fig, line, plotly_fig, tabs):
    from threading import Thread

    def stop_later(thread, delay):
        import time
        time.sleep(delay)
        thread.stop()
        print('Stopped the streaming thread')

    streaming_feed = pe.Bybit(pipeline_mode=True).market_feed
    streaming_resolution = '1s'
    for streaming_product in products:
        streaming_feed.stream(
            product=streaming_product,
            resolution=streaming_resolution,
        )

    layout_thread = plt.layout(
        plt.ohlc(streaming_feed).control(update_interval=1000).mode('browser'),
        tabs,
        line,
        plotly_fig,
        altair_fig,
    ).mode('browser').control(allow_drag=False, linked_axes=False).show()

    # stop in background without blocking
    Thread(target=stop_later, args=(layout_thread, 20)).start()
    return


if __name__ == "__main__":
    app.run()
