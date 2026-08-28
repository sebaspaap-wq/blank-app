#!/usr/bin/env node
/**
 * CAVÁ — Higgsfield renderer
 *
 * Renders campaign imagery with Higgsfield Soul (text-to-image) and optionally
 * animates a still into a Reel with DoP (image-to-video).
 *
 * Usage:
 *   node render.mjs preflight
 *   node render.mjs <brief.json> [outdir]
 *
 * Auth (either form):
 *   export HF_CREDENTIALS="KEY_ID:KEY_SECRET"
 *   export HF_API_KEY=... HF_API_SECRET=...
 *
 * Keys come from Higgsfield Cloud. Never commit them.
 */
import { higgsfield, config } from '@higgsfield/client/v2';
import { writeFile, mkdir, readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';

const SOUL = '/v1/text2image/soul';
const DOP  = '/v1/image2video/dop';

/**
 * Soul emits a fixed set of resolutions — there is no native 4:5 or 2:1.
 * We render the nearest larger ratio and crop down. `crop` is the final
 * delivery size the campaign actually needs.
 */
const RATIOS = {
  'feed-4x5':   { gen: '1536x2048', crop: '1080x1350', use: 'Meta feed' },
  'story-9x16': { gen: '1152x2048', crop: '1080x1920', use: 'Reels / Stories' },
  'square-1x1': { gen: '1536x1536', crop: '1080x1080', use: 'Feed square' },
  'email-2x1':  { gen: '2048x1152', crop: '1200x600',  use: 'Email hero' },
};

function credentials() {
  const c = process.env.HF_CREDENTIALS;
  if (c && c.includes(':')) return c;
  const { HF_API_KEY, HF_API_SECRET } = process.env;
  if (HF_API_KEY && HF_API_SECRET) return `${HF_API_KEY}:${HF_API_SECRET}`;
  throw new Error(
    'No Higgsfield credentials. Set HF_CREDENTIALS="KEY_ID:KEY_SECRET" ' +
    '(or HF_API_KEY + HF_API_SECRET). Create keys in Higgsfield Cloud.'
  );
}

function explain(err) {
  const msg = String(err?.message ?? err);
  // The SDK maps EVERY HTTP 403 to NotEnoughCreditsError, including a 403 from an
  // egress proxy that never reached Higgsfield. Never let this send someone to top
  // up an account when the real problem is the network.
  if (/not enough credits/i.test(msg)) {
    return `${msg}\n\n` +
      'Careful: the SDK reports any HTTP 403 as "Not enough credits". If you are behind\n' +
      'a proxy or sandbox, this may be an egress block, not your balance.\n' +
      'Run `node render.mjs preflight` to tell the two apart before topping up.';
  }
  if (/ENOTFOUND|ECONNREFUSED|EAI_AGAIN|blocked|CONNECT/i.test(msg)) {
    return `${msg}\n\n` +
      'Looks like a network block rather than a bad key. platform.higgsfield.ai must be\n' +
      'reachable — in a sandboxed environment it has to be on the egress allowlist.';
  }
  if (/401|403 .*auth|invalid.*credential/i.test(msg)) {
    return `${msg}\n\nCheck HF_CREDENTIALS is "KEY_ID:KEY_SECRET" and the key is active.`;
  }
  return msg;
}

async function download(url, path) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download failed ${res.status} for ${url}`);
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, Buffer.from(await res.arrayBuffer()));
}

/** One Soul shot. Returns the manifest row. */
async function renderShot(shot, outdir) {
  const ratio = RATIOS[shot.ratio];
  if (!ratio) {
    throw new Error(`Unknown ratio "${shot.ratio}". Use: ${Object.keys(RATIOS).join(', ')}`);
  }

  const input = {
    prompt: shot.prompt,
    width_and_height: ratio.gen,
    quality: shot.quality ?? '1080p',
    batch_size: shot.batch_size ?? 4,   // 4 gives the agent options to pick from
    enhance_prompt: shot.enhance_prompt ?? false, // off: our prompts are already art-directed
    ...(shot.seed !== undefined && { seed: shot.seed }),
    ...(shot.style_id && { style_id: shot.style_id, style_strength: shot.style_strength ?? 0.7 }),
    // Product consistency. Both need to be set up in Higgsfield first:
    //  - image_reference.image_url must be a PUBLIC url (local files will not work)
    //  - custom_reference_id comes from a trained custom reference
    ...(shot.reference_url && {
      image_reference: { type: 'image_url', image_url: shot.reference_url },
    }),
    ...(shot.custom_reference_id && {
      custom_reference_id: shot.custom_reference_id,
      custom_reference_strength: shot.custom_reference_strength ?? 0.6,
    }),
  };

  process.stdout.write(`  ${shot.id} (${shot.ratio}, ${ratio.gen}) … `);
  const res = await higgsfield.subscribe(SOUL, { input, withPolling: true });

  if (res.status === 'nsfw') {
    console.log('REJECTED (nsfw filter)');
    return { ...shot, status: 'nsfw', request_id: res.request_id, files: [],
             note: 'Soul filtered this prompt. Close the robe, drop skin references, retry.' };
  }
  if (res.status !== 'completed' || !res.images?.length) {
    console.log(`FAILED (${res.status})`);
    return { ...shot, status: res.status, request_id: res.request_id, files: [] };
  }

  const files = [];
  for (const [i, img] of res.images.entries()) {
    const name = `${shot.id}-${shot.ratio}-${String(i + 1).padStart(2, '0')}.jpg`;
    await download(img.url, join(outdir, name));
    files.push(name);
  }
  console.log(`ok — ${files.length} variant(s)`);
  return { ...shot, status: 'completed', request_id: res.request_id, files,
           generated_at: ratio.gen, deliver_at: ratio.crop };
}

/** Animate an existing still into a Reel. */
async function renderVideo(shot, outdir) {
  process.stdout.write(`  ${shot.id} (video) … `);
  const res = await higgsfield.subscribe(DOP, {
    input: {
      model: shot.model ?? 'dop-standard',
      prompt: shot.prompt,
      input_images: [{ type: 'image_url', image_url: shot.image_url }],
      ...(shot.motions && { motions: shot.motions }),
      ...(shot.seed !== undefined && { seed: shot.seed }),
    },
    withPolling: true,
  });
  if (res.status !== 'completed' || !res.video?.url) {
    console.log(`FAILED (${res.status})`);
    return { ...shot, status: res.status, request_id: res.request_id, files: [] };
  }
  const name = `${shot.id}.mp4`;
  await download(res.video.url, join(outdir, name));
  console.log('ok');
  return { ...shot, status: 'completed', request_id: res.request_id, files: [name] };
}

async function preflight() {
  console.log('Higgsfield preflight\n');
  let creds;
  try {
    creds = credentials();
    console.log(`  credentials  ok (key id ${creds.split(':')[0].slice(0, 8)}…)`);
  } catch (e) {
    console.log(`  credentials  MISSING — ${e.message}`);
    process.exit(1);
  }
  process.stdout.write('  reachability ');
  try {
    const res = await fetch('https://platform.higgsfield.ai/', { method: 'HEAD' });
    // 403/407 here is almost always an egress proxy denying CONNECT, not Higgsfield
    // answering. Treat it as blocked rather than reporting a false pass.
    if (res.status === 403 || res.status === 407) {
      console.log(`BLOCKED (HTTP ${res.status} — egress proxy denied the connection)\n`);
      console.log('  platform.higgsfield.ai is not on this environment\'s allowlist.');
      console.log('  Run this on a machine with open egress, or add the host to the');
      console.log('  environment network policy.');
      process.exit(1);
    }
    console.log(`ok (HTTP ${res.status})`);
  } catch (e) {
    console.log(`BLOCKED — ${explain(e)}`);
    process.exit(1);
  }
  console.log('\nReady. Run: node render.mjs <brief.json> <outdir>');
}

async function main() {
  const [arg, outArg] = process.argv.slice(2);
  if (!arg || arg === '--help' || arg === '-h') {
    console.log('usage: node render.mjs preflight | node render.mjs <brief.json> [outdir]');
    process.exit(arg ? 0 : 1);
  }
  if (arg === 'preflight') return preflight();

  config({ credentials: credentials() });

  const brief = JSON.parse(await readFile(arg, 'utf8'));
  const outdir = outArg ?? brief.outdir ?? 'creative';
  await mkdir(outdir, { recursive: true });

  console.log(`Rendering ${brief.shots.length} shot(s) → ${outdir}\n`);
  const manifest = [];
  for (const shot of brief.shots) {
    try {
      manifest.push(shot.type === 'video'
        ? await renderVideo(shot, outdir)
        : await renderShot(shot, outdir));
    } catch (e) {
      console.log(`FAILED\n    ${explain(e)}`);
      manifest.push({ ...shot, status: 'error', error: String(e?.message ?? e), files: [] });
    }
  }

  await writeFile(join(outdir, 'manifest.json'),
    JSON.stringify({ brief: arg, rendered_at: new Date().toISOString(), shots: manifest }, null, 2));

  const ok = manifest.filter((m) => m.status === 'completed').length;
  console.log(`\n${ok}/${manifest.length} rendered. Manifest: ${join(outdir, 'manifest.json')}`);
  if (ok < manifest.length) process.exitCode = 1;
}

main().catch((e) => { console.error(`\nfatal: ${explain(e)}`); process.exit(1); });
