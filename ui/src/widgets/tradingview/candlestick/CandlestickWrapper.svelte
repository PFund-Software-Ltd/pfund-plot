<script lang="ts">
  import type { AnyModel } from '@anywidget/types';
  import Candlestick from '$components/tradingview/Candlestick.svelte';

  interface Props {
    model?: AnyModel<any>;
    bindings: { data: any[], height: number, width: number };
  }

  let { bindings }: Props = $props();
</script>

<Candlestick data={bindings.data} height={bindings.height} width={bindings.width} />