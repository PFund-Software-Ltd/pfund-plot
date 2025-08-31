import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import path from 'path';
import { getAllWidgetEntries } from './scripts/widget-entries.js';

// Plain Vite library build (no SvelteKit plugin)
export default defineConfig(() => {
  // Get widget entries from shared module
  const widgetEntries = getAllWidgetEntries();

  return {
    plugins: [svelte({ compilerOptions: { runes: true } })],
    resolve: {
      alias: {
        '@': path.resolve('./src')
      }
    },
    build: {
      lib: {
        entry: process.env.WIDGET_NAME && process.env.WIDGET_ENTRY ? {
          [process.env.WIDGET_NAME]: process.env.WIDGET_ENTRY  // WIDGET_ENTRY is the full path to entry file, e.g. ui/src/widgets/tradingview/candlestick/index.ts
        } : widgetEntries,
        formats: ["es"],
        fileName: (_format, name) => `${name}.js`,
      },
      rollupOptions: {
        // Bundle all deps so the JS is self-contained for Jupyter
        external: [],
      },
      outDir: 'dist/widgets',
      emptyOutDir: false,     // keep multiple widget files side-by-side
      minify: "esbuild",
      sourcemap: false,
    },
  };
});