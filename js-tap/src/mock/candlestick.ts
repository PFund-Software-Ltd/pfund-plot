import type { CandlestickData } from "lightweight-charts";

// Fake OHLC series for the local dev harness (pnpm dev / main.ts) ONLY.
// Not imported by the widget entry (src/lightweight-charts/index.ts), so it
// never ends up in the shipped widget bundle.
//
// Shape mirrors what the Python widget sends: daily candles with `time` as a
// 'YYYY-MM-DD' string (see CandlestickWidget._format_data, which renames the
// `date` column to `time` and stringifies it).

const round2 = (n: number) => Math.round(n * 100) / 100;

/**
 * Deterministic random-walk OHLC generator. Seeded so the chart looks the same
 * across reloads, which makes eyeballing layout/colours easier.
 */
export function makeCandles(count = 90, startPrice = 100): CandlestickData[] {
  const data: CandlestickData[] = [];
  let prev = startPrice;

  // Tiny seeded LCG — no deps, stable output.
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };

  // Build dates in UTC. Using local-time setDate() here would collapse the DST
  // spring-forward day into a duplicate date, and lightweight-charts throws on
  // non-ascending/duplicate times (rendering nothing). One day = 86_400_000 ms.
  const startMs = Date.UTC(2023, 0, 1);
  const DAY_MS = 86_400_000;
  for (let i = 0; i < count; i++) {
    const open = prev;
    const close = Math.max(1, open + (rand() - 0.5) * 4);
    const high = Math.max(open, close) + rand() * 2;
    const low = Math.min(open, close) - rand() * 2;

    const d = new Date(startMs + i * DAY_MS);

    data.push({
      time: d.toISOString().slice(0, 10), // 'YYYY-MM-DD', strictly ascending
      open: round2(open),
      high: round2(high),
      low: round2(low),
      close: round2(close),
    });
    prev = close;
  }

  // Self-check: lightweight-charts silently renders nothing (just throws deep in
  // setData) if times aren't strictly ascending. Catch a bad generator here,
  // with the offending index, instead of debugging a blank chart later.
  for (let i = 1; i < data.length; i++) {
    if (!(data[i].time > data[i - 1].time)) {
      throw new Error(
        `makeCandles: times not strictly ascending at index ${i}: ` +
          `${String(data[i - 1].time)} -> ${String(data[i].time)}`,
      );
    }
  }

  return data;
}

export const candles = makeCandles();
