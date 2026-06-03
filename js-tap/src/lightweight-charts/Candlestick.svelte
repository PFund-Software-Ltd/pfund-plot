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
  } from "lightweight-charts";

  let {
    data = [],
    height = 280,
    width = 680,
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
  });

  // Create the chart + series once, on mount. chartOptions is read untracked so
  // this effect doesn't re-run (and recreate the chart) when width/height change
  // — that's handled by the applyOptions effect below. Cleanup removes the chart
  // on unmount so re-renders in a notebook don't leak.
  $effect(() => {
    chart = createChart(chartContainer, untrack(() => chartOptions));
    series = chart.addSeries(CandlestickSeries, untrack(() => seriesOptions));

    return () => {
      chart?.remove();
      chart = undefined;
      series = undefined;
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
      <div bind:this={chartContainer}></div>
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
</style>
