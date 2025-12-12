<script lang="ts">
  import { createChart, CandlestickSeries, ColorType } from "lightweight-charts";
  import type { CandlestickData, CandlestickSeriesOptions, ChartOptions, DeepPartial } from "lightweight-charts";
  
  let { data = [] }: { data?: CandlestickData[] } = $props();
  
  let chartContainer: HTMLElement;
  let chart: ReturnType<typeof createChart>;
  let candlestickSeries: ReturnType<typeof chart.addSeries>;
  
  $effect(() => {
    if (chartContainer && !chart) {
      const chartOptions: DeepPartial<ChartOptions> = {
        width: 1000,
        height: 320,
        layout: {
          textColor: "black",
          background: { type: ColorType.Solid, color: "white" },
        },
      };
      
      chart = createChart(chartContainer, chartOptions);
      
      const seriesOptions: DeepPartial<CandlestickSeriesOptions> = {
        upColor: "#26a69a",
        downColor: "#ef5350",
        borderVisible: false,
        wickUpColor: "#26a69a",
        wickDownColor: "#ef5350",
      };
      
      candlestickSeries = chart.addSeries(CandlestickSeries, seriesOptions);
    }
  });
  
  $effect(() => {
    if (candlestickSeries && data) {
      candlestickSeries.setData(data);
      if (data.length) {
        chart.timeScale().fitContent();
      }
    }
  });

</script>

<div bind:this={chartContainer}></div>