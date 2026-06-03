import { mount } from 'svelte'
import Candlestick from './lightweight-charts/Candlestick.svelte'
import { candles } from './mock/candlestick'

// Local dev harness: render the bare Candlestick component in the browser
// (pnpm dev) with fake data, to eyeball the chart before the anywidget round-
// trip. This path never touches Python or the widget wrapper.
const app = mount(Candlestick, {
  target: document.getElementById('app')!,
  props: { data: candles, height: 400, width: 900 },
})

export default app
