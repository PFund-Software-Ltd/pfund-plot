<!-- test script -->
<script lang="ts">
	import Candlestick from '@/components/tradingview/Candlestick.svelte';
	import type { CandlestickData } from 'lightweight-charts';

	// Fake candlestick data - 10 days of sample stock data
	const data: CandlestickData[] = [
		{ open: 10, high: 10.63, low: 9.49, close: 9.55, time: '2022-01-17' },
		{ open: 9.55, high: 10.3, low: 9.42, close: 9.94, time: '2022-01-18' },
		{ open: 9.94, high: 10.17, low: 9.92, close: 9.78, time: '2022-01-19' },
		{ open: 9.78, high: 10.59, low: 9.18, close: 9.51, time: '2022-01-20' },
		{ open: 9.51, high: 10.46, low: 9.1, close: 10.17, time: '2022-01-21' },
		{ open: 10.17, high: 10.96, low: 10.16, close: 10.47, time: '2022-01-24' },
		{ open: 10.47, high: 11.39, low: 10.4, close: 10.81, time: '2022-01-25' },
		{ open: 10.81, high: 11.6, low: 10.3, close: 10.75, time: '2022-01-26' },
		{ open: 10.75, high: 11.6, low: 10.49, close: 10.93, time: '2022-01-27' },
		{ open: 10.93, high: 11.53, low: 10.76, close: 10.96, time: '2022-01-28' }
	];
</script>

<h1>Candlestick Chart Test</h1>
<Candlestick {data} />
