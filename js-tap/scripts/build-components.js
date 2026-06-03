// Build every first-party component to a self-contained ESM.
//
// Auto-discovery: each component is a folder src/components/<name>/index.ts;
// <name> (the folder) is the bundle name. Add a folder -> it builds. No entry
// list to hand-maintain, no per-component config edits.
//
// Each component is built in its OWN isolated Vite build (one build() call per
// component) so the outputs stay self-contained: putting multiple entries in a
// single build would let Rollup hoist shared code into a chunk, turning the
// bundles into `import './chunk.js'` — which anywidget can't load (it fetches
// one _esm file, no module resolution at runtime).
//
//   node scripts/build-components.js            production (minified)
//   node scripts/build-components.js --watch     dev (unminified + sourcemap, rebuild on save)
//
// Output: dist/components/<name>.js  (copy-components.js ships these in the wheel)
import { build } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import { readdirSync, existsSync, rmSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

// Resolve paths from this script, not cwd, so it runs the same from anywhere.
const jsTap = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const componentsDir = join(jsTap, 'src', 'components')
const outDir = join(jsTap, 'dist', 'components')
const dev = process.argv.includes('--watch')

// A component = a folder under src/components/ containing an index.ts entry.
function discoverComponents() {
  if (!existsSync(componentsDir)) return []
  return readdirSync(componentsDir, { withFileTypes: true })
    .filter((d) => d.isDirectory() && existsSync(join(componentsDir, d.name, 'index.ts')))
    .map((d) => d.name)
    .sort()
}

async function buildComponent(name) {
  await build({
    root: jsTap,
    configFile: false, // self-contained config below; ignore vite.config.ts (that's the dev harness)
    plugins: [
      // emitCss: false -> Svelte injects component styles via JS at runtime
      // instead of vite emitting a separate .css file, keeping each component
      // a single self-contained .js.
      svelte({ emitCss: false }),
    ],
    build: {
      outDir: 'dist/components',
      emptyOutDir: false, // don't wipe sibling components between per-component builds
      target: 'esnext', // modern notebook browser; also avoids vite 8's esbuild-transpile path
      minify: !dev, // true -> rolldown's built-in oxc minifier
      sourcemap: dev,
      watch: dev ? {} : null,
      lib: {
        entry: { [name]: `src/components/${name}/index.ts` },
        formats: ['es'],
        fileName: (_format, n) => `${n}.js`,
      },
      // Bundle everything: components run standalone in the browser with no
      // external module resolution. Nothing is a peer dependency.
      rollupOptions: { external: [] },
    },
  })
}

const names = discoverComponents()
if (names.length === 0) {
  console.error(`[build-components] no components in ${componentsDir} (expected <name>/index.ts)`)
  process.exit(1)
}
// Clean once up front so a bundle from a since-removed component doesn't linger
// (the per-component builds use emptyOutDir:false so they don't wipe each other).
rmSync(outDir, { recursive: true, force: true })

console.log(`[build-components] ${dev ? 'watching' : 'building'}: ${names.join(', ')}`)
for (const name of names) {
  await buildComponent(name)
}
