// VIBE-CODED: Claude Sonnet 4
import { glob } from 'glob';
import path from 'path';

// Auto-discover widget entry points
function discoverWidgetEntries() {
  return glob.sync('src/widgets/**/index.ts').reduce((entries, file) => {
    const name = path.basename(path.dirname(file));
    entries[name] = file;
    return entries;
  }, {});
}

// Get all widget entries (explicit + auto-discovered)
export function getAllWidgetEntries() {
  const widgetEntries = discoverWidgetEntries();
  
  return {
    no_svelte_test: "src/widgets/no_svelte_test.ts", // a case where Svelte or anywidget/svelte is not used
    ...widgetEntries,
  };
}

export default getAllWidgetEntries;