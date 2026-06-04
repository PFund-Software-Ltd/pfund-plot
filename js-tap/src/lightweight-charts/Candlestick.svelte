<script lang="ts">
  import { untrack } from "svelte";
  import { createChart, CandlestickSeries, ColorType } from "lightweight-charts";
  import type {
    CandlestickData,
    CandlestickSeriesOptions,
    ChartOptions,
    DeepPartial,
    IChartApi,
    ISeriesApi,
    MouseEventParams,
    Time,
  } from "lightweight-charts";

  let {
    data = [],
    height = 280,
    width = 670,
    title = "Candlestick",
    xlabel = "date",
    ylabel = "price",
    posColor = "#26a69a",
    negColor = "#ef5350",
    bgColor = "white",
    grid = true,
    datetimePrecision = "s",
  }: {
    data?: CandlestickData[];
    height?: number;
    width?: number;
    title?: string;
    xlabel?: string;
    ylabel?: string;
    posColor?: string;
    negColor?: string;
    bgColor?: string;
    grid?: boolean;
    datetimePrecision?: "d" | "s";
  } = $props();

  let chartContainer: HTMLDivElement;
  let chart: IChartApi | undefined;
  let series: ISeriesApi<"Candlestick"> | undefined;

  // lightweight-charts has no native tooltip, so we render our own: a floating
  // HTML element driven by the crosshair-move subscription (set up in the create
  // effect). `tooltip` is null when the crosshair is off the chart / off a bar.
  // Prices are pre-formatted strings (via the series' own price formatter) so the
  // markup stays dumb and the values match the axis exactly.
  type Tooltip = {
    open: string;
    high: string;
    low: string;
    close: string;
    volume?: string;
    x: number;
    y: number;
  };
  let tooltip = $state<Tooltip | null>(null);

  // Volume rides along on the data dicts from Python but isn't part of the
  // candlestick series (OHLC only), so the crosshair payload can't surface it.
  // Index it by time here so the handler can look it up O(1). Optional: absent
  // when the df had no volume column (see OPTIONAL_COLS), in which case the
  // tooltip simply omits the V row.
  const volumeByTime = $derived(
    new Map<Time, number>(
      (data as Array<CandlestickData & { volume?: number }>)
        .filter((d) => d.volume != null)
        .map((d) => [d.time, d.volume as number]),
    ),
  );

  // Decimal precision for price display, inferred from the data so it suits the
  // instrument: 2 for stocks/indices, more for sub-dollar crypto. Driven off the
  // smallest non-zero low (the most demanding value): `leading zeros after the
  // decimal point + 4` ⇒ ~4 significant figures, clamped to lightweight-charts'
  // max of 8. `ceil(-log10) - 1` is the leading-zero count (correct even at exact
  // powers of ten, where floor would over-count by one: 0.1 has 0 leading zeros,
  // not 1), so precision = ceil(-log10) + 3. Applied to the series' priceFormat
  // (below) so the AXIS uses it too, and reused by the tooltip via
  // series.priceFormatter() — axis and tooltip stay identical by construction. To
  // make this exact rather than inferred, pass the instrument's tick size from
  // Python instead.
  const pricePrecision = $derived.by(() => {
    let min = Infinity;
    for (const d of data) if (d.low > 0 && d.low < min) min = d.low;
    if (!isFinite(min) || min >= 1) return 2;
    return Math.min(8, Math.ceil(-Math.log10(min)) + 3);
  });

  function handleCrosshairMove(param: MouseEventParams) {
    if (
      !series ||
      param.point === undefined ||
      param.time === undefined ||
      param.point.x < 0 ||
      param.point.y < 0
    ) {
      tooltip = null;
      return;
    }
    const bar = param.seriesData.get(series) as CandlestickData | undefined;
    if (!bar) {
      tooltip = null;
      return;
    }
    // Keep .format on its formatter object — it relies on `this`, so detaching it
    // into a bare variable (`const fmt = ...format`) throws when called.
    const formatter = series.priceFormatter();
    const volume = volumeByTime.get(param.time);
    tooltip = {
      open: formatter.format(bar.open),
      high: formatter.format(bar.high),
      low: formatter.format(bar.low),
      close: formatter.format(bar.close),
      volume: volume != null ? volume.toLocaleString() : undefined,
      x: param.point.x,
      y: param.point.y,
    };
  }

  // Single source of truth for chart-level options. Recomputes when width/height
  // change; the static layout stays put. Used both to create the chart and to
  // re-apply on resize, so width/height live in exactly one place.
  const chartOptions = $derived<DeepPartial<ChartOptions>>({
    width,
    height,
    layout: {
      textColor: "black",
      background: { type: ColorType.Solid, color: bgColor },
    },
    // grid (from Python) toggles both gridline families at once, matching the
    // Bokeh backend's single `grid` flag.
    grid: {
      vertLines: { visible: grid },
      horzLines: { visible: grid },
    },
    timeScale: {
      // fitContent() refuses to compress bars below minBarSpacing (default
      // 0.5px), so a long series (e.g. ~13y of daily bars in 700px ≈ 0.2px/bar)
      // gets clipped on the left and must be dragged into view. Lower the floor
      // so the whole span fits, matching the Bokeh backend's auto-range behavior.
      minBarSpacing: 0.001,
      // datetime_precision (from Python) controls how much of the timestamp the
      // axis/crosshair shows: "d" = date only; "s" = date + time-of-day. Without
      // timeVisible, intraday (hourly/minute) bars all label as the bare day
      // number. lightweight-charts still hides the time for coarse (daily+) spans,
      // and only surfaces seconds for second-level data, so this stays sensible
      // across resolutions. (Sub-second isn't offered: time is a second-resolution
      // UTCTimestamp.)
      timeVisible: datetimePrecision !== "d",
    },
  });

  // Series styling. Body + wick colors follow posColor/negColor, so this is
  // $derived (recomputes when the colors change) and re-applied via the effect
  // below. Used untracked at creation so the create effect doesn't re-run.
  const seriesOptions = $derived<DeepPartial<CandlestickSeriesOptions>>({
    upColor: posColor,
    downColor: negColor,
    borderVisible: false,
    wickUpColor: posColor,
    wickDownColor: negColor,
    // Drives the price-axis label precision; the tooltip reuses the resulting
    // formatter so the two never disagree. minMove is the smallest tick the
    // scale steps by, = 10^-precision.
    priceFormat: {
      type: "price",
      precision: pricePrecision,
      minMove: Math.pow(10, -pricePrecision),
    },
  });

  // Create the chart + series once, on mount. chartOptions is read untracked so
  // this effect doesn't re-run (and recreate the chart) when width/height change
  // — that's handled by the applyOptions effect below. Cleanup removes the chart
  // on unmount so re-renders in a notebook don't leak.
  $effect(() => {
    chart = createChart(chartContainer, untrack(() => chartOptions));
    series = chart.addSeries(CandlestickSeries, untrack(() => seriesOptions));
    chart.subscribeCrosshairMove(handleCrosshairMove);

    return () => {
      // chart.remove() also drops its subscriptions, so no explicit unsubscribe.
      chart?.remove();
      chart = undefined;
      series = undefined;
      tooltip = null;
    };
  });

  // Push data whenever it changes, and re-frame to fit it. Re-fitting on every
  // update keeps the view in sync with the datetime-range slider: filtering to a
  // sub-range (either handle) always re-frames the chart to the selection,
  // matching the Bokeh backend (which rebuilds + auto-ranges each update).
  // NOTE: this means a streaming append also re-fits; if that becomes a problem,
  // distinguish replace (fit) from append (don't) via an explicit signal from
  // the Python widget rather than inferring it here.
  $effect(() => {
    if (!series) return;
    series.setData(data);
    tooltip = null; // any visible tooltip refers to the old bars; drop it
    if (data.length) chart?.timeScale().fitContent();
  });

  // Re-apply chart options (width/height) whenever they change.
  $effect(() => {
    chart?.applyOptions(chartOptions);
  });

  // Re-apply series options (pos/neg colors) whenever they change.
  $effect(() => {
    series?.applyOptions(seriesOptions);
  });
</script>

<!--
  lightweight-charts has no native title or axis labels, so they're plain HTML
  siblings around the canvas. Living inside this component (rather than the Panel
  layer) means they render identically across every host — marimo, jupyter,
  browser, desktop. Empty string ⇒ the element is omitted entirely.
-->
<div class="candlestick">
  {#if title}<div class="title">{title}</div>{/if}
  <div class="plot-row">
    {#if ylabel}<div class="ylabel">{ylabel}</div>{/if}
    <div class="plot-col">
      <!-- position:relative anchor so the absolutely-positioned tooltip tracks
           the crosshair within the chart canvas. -->
      <div class="chart-wrap">
        <div bind:this={chartContainer}></div>
        {#if tooltip}
          <!-- Flip the tooltip to the left of the cursor past the chart midpoint
               so it never spills off the right edge. -->
          <div
            class="tooltip"
            class:flip={tooltip.x > width / 2}
            style="left: {tooltip.x}px; top: {tooltip.y}px;"
          >
            <div><span>O</span>{tooltip.open}</div>
            <div><span>H</span>{tooltip.high}</div>
            <div><span>L</span>{tooltip.low}</div>
            <div><span>C</span>{tooltip.close}</div>
            {#if tooltip.volume != null}
              <div><span>V</span>{tooltip.volume}</div>
            {/if}
          </div>
        {/if}
      </div>
      {#if xlabel}<div class="xlabel">{xlabel}</div>{/if}
    </div>
  </div>
</div>

<style>
  /* Match lightweight-charts' default text (sans-serif, black) so the labels
     read as part of the chart rather than the surrounding page. */
  .candlestick {
    display: inline-block;
    font-family:
      -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu,
      sans-serif;
    color: black;
  }
  .title {
    text-align: center;
    font-weight: bold;
    margin-bottom: 4px;
  }
  .plot-row {
    display: flex;
    align-items: center;
  }
  /* Rotated so it reads bottom-to-top, like a conventional y-axis title. */
  .ylabel {
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    text-align: center;
    margin-right: 4px;
    font-style: italic;
  }
  .xlabel {
    text-align: center;
    margin-top: 4px;
    font-style: italic;
  }
  .chart-wrap {
    position: relative;
  }
  /* Floating OHLC(V) readout. pointer-events:none so it never eats crosshair
     moves (which would make it flicker). Offset from the cursor; .flip moves it
     to the left side past the chart midpoint to stay on-canvas. */
  .tooltip {
    position: absolute;
    pointer-events: none;
    z-index: 2;
    transform: translate(12px, 12px);
    padding: 4px 8px;
    font-size: 11px;
    line-height: 1.4;
    white-space: nowrap;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  }
  .tooltip.flip {
    transform: translate(-100%, 12px) translateX(-12px);
  }
  /* Fixed-width label gutter so the OHLC numbers line up in a column. */
  .tooltip span {
    display: inline-block;
    width: 1.1em;
    color: #787b86;
    font-weight: bold;
  }
</style>
