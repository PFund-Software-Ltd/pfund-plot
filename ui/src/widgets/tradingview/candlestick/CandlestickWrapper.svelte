<script lang="ts">
  import type { AnyModel } from '@anywidget/types';
  import Candlestick from '$components/tradingview/Candlestick.svelte';

  interface Props {
    model?: AnyModel<any>;
    bindings?: { data: any[] };
  }

  let { bindings }: Props = $props();
</script>

<Candlestick data={bindings?.data || []} />