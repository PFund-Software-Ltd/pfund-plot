import { createChart, CandlestickSeries, ColorType } from "lightweight-charts";
import type { CandlestickData, CandlestickSeriesOptions, ChartOptions, DeepPartial } from "lightweight-charts";

type Model = {
  get: (key: string) => unknown;
  on?: (event: string, cb: () => void) => void;
};

type RenderCtx = {
  model: Model;
  el: HTMLElement;
};

function render({ model, el }: RenderCtx) {
  const chartOptions: DeepPartial<ChartOptions> = {
    width: 600,
    height: 320,
    layout: {
      textColor: "black",
      background: { type: ColorType.Solid, color: "white" },
    },
  };

  const chart = createChart(el, chartOptions);

  const seriesOptions: DeepPartial<CandlestickSeriesOptions> = {
    upColor: "#26a69a",
    downColor: "#ef5350",
    borderVisible: false,
    wickUpColor: "#26a69a",
    wickDownColor: "#ef5350",
  };

  const candlestickSeries = chart.addSeries(CandlestickSeries, seriesOptions);

  const draw = () => {
    const data = (model.get("data") ?? []) as CandlestickData[];
    candlestickSeries.setData(data);
    if (data.length) chart.timeScale().fitContent();
  };

  draw();
  model.on?.("change:data", draw);
}

export default { render };