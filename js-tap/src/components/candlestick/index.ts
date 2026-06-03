import { defineWidget } from "@anywidget/svelte";
import CandlestickWrapper from "./CandlestickWrapper.svelte";

// anywidget entry point for the `candlestick` component. The build
// (scripts/build-components.js) auto-discovers this file by its folder name,
// and this default export is what anywidget loads as the component's _esm in
// Python.
export default defineWidget(CandlestickWrapper);
