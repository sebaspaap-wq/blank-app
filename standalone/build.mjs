/**
 * Builds the standalone, single-file CAVÁ page: every photograph is inlined as
 * a data URI so the page opens from one URL with no external requests.
 */
import sharp from 'sharp';
import fs from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const IMAGES = path.join(root, 'public/images');

const EMBED = {
  SAND_TERRACE:   ['cava-sand-terrace.webp', 78],
  SAND_POOLSIDE:  ['cava-sand-poolside.webp', 74],
  IVORY_INTERIOR: ['cava-ivory-interior.webp', 76],
  IVORY_POOLSIDE: ['cava-ivory-poolside.webp', 74],
  CACAO_SUNSET:   ['cava-cacao-sunset.webp', 76],
  CACAO_POOL:     ['cava-cacao-pool.webp', 74],
};

const out = process.argv[2] || path.join(root, 'standalone/cava.html');
let html = await fs.readFile(path.join(root, 'standalone/cava.template.html'), 'utf8');

const fonts = await fs.readFile(path.join(root, 'standalone/fonts.css'), 'utf8');
html = html.replace('{{FONTS}}', fonts.trim());

let total = 0;
for (const [token, [file, quality]] of Object.entries(EMBED)) {
  const buf = await sharp(path.join(IMAGES, file)).webp({ quality, effort: 6 }).toBuffer();
  total += buf.length;
  console.log(token.padEnd(16), (buf.length / 1024).toFixed(0) + ' kB');
  html = html.replaceAll(`{{${token}}}`, `data:image/webp;base64,${buf.toString('base64')}`);
}

if (html.includes('{{')) throw new Error('unresolved token in template');
await fs.writeFile(out, html);
console.log('\nphotography', (total / 1024).toFixed(0) + ' kB  →  page', ((await fs.stat(out)).size / 1024).toFixed(0) + ' kB');
console.log('written to', out);
