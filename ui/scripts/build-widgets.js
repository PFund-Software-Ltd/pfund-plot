import { spawn } from 'child_process';
import { getAllWidgetEntries } from './widget-entries.js';

const isWatch = process.argv.includes('--watch');
const showHelp = process.argv.includes('--help') || process.argv.includes('-h');

if (showHelp) {
  console.log(`
Widget Build System

Usage:
  npm run build:widget              Build all widgets for production
  npm run build:widget:watch        Watch and rebuild all widgets during development
  npm run build:widget:watch:single Watch a single widget during development
  npm run build:widget:single       Use standard Vite build (may create shared chunks)

Environment Variables:
  WIDGET_TARGET=<name>              Specify widget to watch (single watch mode)
  WIDGET_TARGET=all                 Watch all widgets simultaneously (default for :watch)

Examples:
  npm run build:widget
  npm run build:widget:watch
  WIDGET_TARGET=candlestick npm run build:widget:watch:single

Available widgets will be auto-discovered from src/widgets/**/index.ts
`);
  process.exit(0);
}

// Get all widget entries from shared module
const allEntries = getAllWidgetEntries();

if (isWatch) {
  console.log('Available widgets:', Object.keys(allEntries));
} else {
  console.log('Building widgets:', Object.keys(allEntries));
}

// Build each widget separately to ensure they're self-contained
async function buildWidget(name, entry) {
  return new Promise((resolve, reject) => {
    const args = ['build', '--config', 'vite.widget.config.ts'];
    if (isWatch) args.push('--watch', '--mode', 'development');
    
    const child = spawn('npx', ['vite', ...args], {
      env: {
        ...process.env,
        WIDGET_NAME: name,
        WIDGET_ENTRY: entry,
      },
      stdio: 'inherit'
    });

    child.on('exit', (code) => {
      if (code === 0) {
        console.log(`✓ Built ${name}`);
        resolve();
      } else {
        console.error(`✗ Failed to build ${name}`);
        reject(new Error(`Widget ${name} build failed with code ${code}`));
      }
    });
  });
}

// Build widgets sequentially to avoid conflicts
async function buildAll() {
  if (isWatch) {
    const targetWidget = process.env.WIDGET_TARGET;
    if (targetWidget === 'all') {
      // Watch all widgets simultaneously
      console.log(`👀 Watching all widgets: ${Object.keys(allEntries).join(', ')}`);
      for (const [name, entry] of Object.entries(allEntries)) {
        buildWidget(name, entry).catch(console.error);
      }
    } else if (targetWidget && allEntries[targetWidget]) {
      console.log(`👀 Watching ${targetWidget}...`);
      buildWidget(targetWidget, allEntries[targetWidget]).catch(console.error);
    } else if (targetWidget) {
      console.error(`Widget "${targetWidget}" not found. Available: ${Object.keys(allEntries).join(', ')}`);
      process.exit(1);
    } else {
      // Default to first widget for single-widget development
      const defaultWidget = Object.keys(allEntries)[0];
      console.log(`👀 Watching ${defaultWidget}... (Use WIDGET_TARGET=all to watch all widgets)`);
      buildWidget(defaultWidget, allEntries[defaultWidget]).catch(console.error);
    }
  } else {
    // For regular builds, build all widgets sequentially
    for (const [name, entry] of Object.entries(allEntries)) {
      try {
        await buildWidget(name, entry);
      } catch (error) {
        console.error(`Failed to build ${name}:`, error.message);
        process.exit(1);
      }
    }
    console.log('\n✓ All widgets built successfully!');
  }
}

buildAll().catch((error) => {
  console.error('Build failed:', error);
  process.exit(1);
});