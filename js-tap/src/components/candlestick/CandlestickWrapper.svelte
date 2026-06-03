<script lang="ts">
  import type { AnyModel } from "@anywidget/types";
  import type { CandlestickData } from "lightweight-charts";
  // The pure, reusable chart lives in the building-blocks dir; this first-party
  // component just wraps it with anywidget glue.
  import Candlestick from "../../lightweight-charts/Candlestick.svelte";

  // `style` / `control` mirror the Python-side CandlestickWidget dict traits of
  // the same name (snake_case keys, since they come straight from Python).
  type Style = {
    height: number;
    width: number;
    title: string;
    xlabel: string;
    ylabel: string;
    pos_color: string;
    neg_color: string;
    bg_color: string;
    grid: boolean;
  };
  type Control = { datetime_precision: "d" | "s" };
  type Bindings = {
    data: CandlestickData[];
    style: Style;
    control: Control;
  };

  // `bindings` is the reactive Proxy of the model's traits, supplied by
  // @anywidget/svelte. Typed optional to match defineWidget's expected
  // component signature (`bindings?: T`); it's always defined at render time.
  // This wrapper's only job is to map those traits onto the pure Candlestick
  // component's props, keeping the chart anywidget-agnostic.
  let { bindings }: { model?: AnyModel<Bindings>; bindings?: Bindings } = $props();
</script>

<Candlestick
  data={bindings?.data}
  height={bindings?.style?.height}
  width={bindings?.style?.width}
  title={bindings?.style?.title}
  xlabel={bindings?.style?.xlabel}
  ylabel={bindings?.style?.ylabel}
  posColor={bindings?.style?.pos_color}
  negColor={bindings?.style?.neg_color}
  bgColor={bindings?.style?.bg_color}
  grid={bindings?.style?.grid}
  datetimePrecision={bindings?.control?.datetime_precision}
/>
