// Copy the built first-party component bundles into the Python package so the
// wheel ships them. Run by `pixi run js-package` after the production build.
//
//   js-tap/dist/components/<name>.js  ->  src/pfund_plot/js_tap/components/<name>.js
//
// Flat copy, no hard-coded component names: whatever vite produced gets
// shipped. uv_build picks these up as package data (they live under the module
// tree), so a `pip install` user needs no Node and no build. (Dashboards will
// land under src/pfund_plot/js_tap/dashboards/ with their own packaging.)
import { cpSync, mkdirSync, readdirSync, existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url)) // js-tap/scripts
const repoRoot = resolve(scriptDir, '..', '..') // pfund-plot
const srcDir = join(repoRoot, 'js-tap', 'dist', 'components')
const destDir = join(repoRoot, 'src', 'pfund_plot', 'js_tap', 'components')

if (!existsSync(srcDir)) {
  console.error(`[copy-components] no build output at ${srcDir} — run the component build first`)
  process.exit(1)
}

const bundles = readdirSync(srcDir).filter((f) => f.endsWith('.js'))
if (bundles.length === 0) {
  console.error(`[copy-components] no .js bundles in ${srcDir} — nothing to package`)
  process.exit(1)
}

mkdirSync(destDir, { recursive: true })
for (const file of bundles) {
  cpSync(join(srcDir, file), join(destDir, file))
  console.log(`[copy-components] ${file} -> src/pfund_plot/js_tap/components/${file}`)
}
