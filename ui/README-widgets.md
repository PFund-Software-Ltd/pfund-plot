# Widget Build System

This project uses a custom widget build system that creates self-contained JavaScript modules for use with anywidget/Jupyter.

## Architecture

Each widget is built separately to ensure they are completely self-contained with all dependencies bundled inline. This is required for anywidget compatibility.

## Build Scripts

- `npm run build:widget` - Build all widgets for production
- `npm run build:widget:watch` - Watch and rebuild all widgets during development
- `npm run build:widget:watch:single` - Watch and rebuild a single widget during development  
- `npm run build:widget:single` - Build using the standard Vite config (may create shared chunks)

## Adding New Widgets

### Method 1: Auto-discovery (Recommended)
1. Create your widget in `src/widgets/your-widget-name/index.ts`
2. Export a Svelte component as default
3. Run `npm run build:widget` to build all widgets

### Method 2: Explicit entry
1. Create your widget file anywhere in `src/widgets/`
2. Add it to the `allEntries` object in `scripts/build-widgets.js`
3. Run `npm run build:widget`

## Widget Structure

Each widget should follow this pattern:

```typescript
// src/widgets/your-widget/index.ts
import { defineWidget } from '@anywidget/svelte';
import YourComponent from './YourComponent.svelte';

export default defineWidget(YourComponent);
```

```svelte
<!-- src/widgets/your-widget/YourComponent.svelte -->
<script lang="ts">
  import type { AnyModel } from '@anywidget/types';

  interface Props {
    model?: AnyModel<any>;
    bindings?: { data: any[] }; // Your data interface
  }

  let { bindings }: Props = $props();
</script>

<div>
  <!-- Your widget UI here -->
  <!-- Access data via: bindings?.data || [] -->
</div>
```

## Development Workflow

### For new widget development:
```bash
# Watch all widgets simultaneously (default)
npm run build:widget:watch

# Watch a specific widget only (more efficient for focused development)
WIDGET_TARGET=your-widget npm run build:widget:watch:single

# Or use the dedicated single-widget command
npm run build:widget:watch:single
```

### For production:
```bash
# Build all widgets
npm run build:widget
```

## Output

All widgets are built to the `dist/` directory as self-contained `.js` files:
- `dist/candlestick.js` - Candlestick chart widget
- `dist/tv_candlestick.js` - TradingView-style candlestick widget
- `dist/your-widget.js` - Your custom widgets

Each file contains all necessary dependencies and can be used directly with anywidget/Jupyter.

## Troubleshooting

**Problem**: Widget shows "Failed to fetch dynamically imported module"  
**Solution**: Ensure you're building widgets separately. The build system prevents shared chunks that cause this issue.

**Problem**: Widget not found during build  
**Solution**: Check that your widget is either auto-discovered in `src/widgets/**/index.ts` or explicitly added to `scripts/build-widgets.js`.

**Problem**: TypeScript errors in widget  
**Solution**: Ensure your component props match the anywidget interface with optional `model` and `bindings` props.