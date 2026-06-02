/*
 * Workaround for license-webpack-plugin@4.0.2 (bundled, unmaintained) which
 * crashes on webpack 5's module-federation "provide module" identifiers.
 *
 * Newer webpack emits e.g.
 *     provide module (default) fits-lab-extension@0.1.0|/abs/path/lib/index.js
 * (separated by "|"), but the plugin's `provide module` branch assumes an older
 * `... = /abs/path` format and does `filename.split('=')[1].trim()`, throwing
 * "Cannot read properties of undefined (reading 'trim')".
 *
 * This patch makes that branch fall back to the "|" format so the actual file
 * path is recovered (keeping license detection correct). Idempotent.
 */
const fs = require('fs');
const path = require('path');

const target = path.join(
  __dirname,
  '..',
  'node_modules',
  'license-webpack-plugin',
  'dist',
  'WebpackModuleFileIterator.js'
);

const ORIGINAL = "return filename.split('=')[1].trim();";
const PATCHED = [
  'var __after = filename.split(\'=\')[1];',
  'if (__after === undefined) {',
  '  var __parts = filename.split(\'|\');',
  '  return __parts[__parts.length - 1];',
  '}',
  'return __after.trim();'
].join(' ');

if (!fs.existsSync(target)) {
  // Plugin not installed (e.g. nothing to build) — nothing to do.
  process.exit(0);
}

let source = fs.readFileSync(target, 'utf8');
if (source.includes(ORIGINAL)) {
  source = source.replace(ORIGINAL, PATCHED);
  fs.writeFileSync(target, source);
  console.log('[fix-license-plugin] patched ' + target);
} else {
  console.log('[fix-license-plugin] already patched or not applicable, skipping');
}
