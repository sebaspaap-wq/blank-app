#!/usr/bin/env node
/**
 * QUITTER × Higgsfield — beeld maken binnen de merk- en reclameregels.
 *
 * Wat dit doet, in deze volgorde:
 *   1. plakt de vaste QUITTER-beeldtaal aan je prompt en zet de verboden erin;
 *   2. controleert vóór het uitgeven van credits of de prompt niets vraagt wat
 *      niet mag (sigaretten, rook, artsen, iemand die het product gebruikt);
 *   3. haalt bijschrift en alt-tekst door de compliance-poort — tekst bij een
 *      beeld is nog steeds reclame;
 *   4. roept Higgsfield Soul aan en wacht het resultaat af;
 *   5. bewaart het beeld plus een notitie met prompt, alt-tekst en oordeel.
 *
 * Gebruik:
 *   node marketing-team/image.mjs --prompt "twee verpakkingen op een stenen richel"
 *   node marketing-team/image.mjs --from marketing-team/output/beeld-brief.md
 *   node marketing-team/image.mjs --prompt "..." --size PORTRAIT_1152x2048 --alt "Twee QUITTER-verpakkingen"
 *
 * Inloggen (Higgsfield Cloud → credentials):
 *   export HF_CREDENTIALS="KEY_ID:KEY_SECRET"
 *
 * Let op: elke run kost Higgsfield-credits. Er wordt niets gepubliceerd.
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { createHiggsfieldClient, SoulSize, SoulQuality, BatchSize } from "@higgsfield/client/v2";
import { check } from "./compliance/check.mjs";

const here = dirname(fileURLToPath(import.meta.url));

/**
 * Het model-eindpunt. De SDK spreekt Soul aan onder een pad dat per versie kan
 * verschillen; klopt dit niet voor jouw account, kijk het na op docs.higgsfield.ai
 * en geef het mee met --endpoint. De foutmelding hieronder zegt dat ook.
 */
const DEFAULT_ENDPOINT = "text2image/soul";

/** De vaste beeldtaal uit agents/07-art-director.md, als promptstaart. */
const BRAND_STYLE = [
  "Studio product photography, matte materials, soft directional key light from upper left,",
  "true soft shadows, warm white background (#F7F6F2), charcoal (#191919) and taupe (#A69B8D) only,",
  "no other colours, architectural composition, generous negative space, calm, expensive,",
  "editorial still life, shot on medium format, 100mm lens, f/8, natural depth of field.",
].join(" ");

/** Wat er nooit in beeld mag. Gaat mee de prompt in én wordt vooraf gecontroleerd. */
const BRAND_NEGATIVE = [
  "no cigarettes, no ashtrays, no smoke, no lungs, no medical equipment, no lab coats,",
  "no doctors, no person using or chewing the product, no mouth close-ups, no before-and-after,",
  "no children or anyone who could look under 18, no stock-photo smiling, no green health symbolism,",
  "no gradients, no cartoons, no text overlay, no logos other than the pack.",
].join(" ");

/** Vraagt de prompt zelf om iets wat niet in beeld mag? Dat vangen we vóór de credits. */
const FORBIDDEN_VISUALS = [
  { pattern: /\b(sigaret|cigarette|smoking|rokende?|rook\b|smoke)\b/i, why: "sigaretten of rook in beeld" },
  { pattern: /\b(long|lungs|orgaan|organ)\b/i, why: "medische beelden van organen" },
  { pattern: /\b(arts|dokter|doctor|apotheker|pharmacist|nurse|verpleeg)\b/i, why: "zorgverleners in beeld — raakt regel A5" },
  { pattern: /\b(kind|kinderen|child|children|teen|tiener|school)\b/i, why: "minderjarigen — raakt regel A7" },
  { pattern: /\b(kauwt?|chewing|in de mond|in mouth|tong|tongue)\b/i, why: "iemand die het product gebruikt" },
  { pattern: /\b(voor en na|before and after|transformation)\b/i, why: "voor-en-na — suggereert een resultaat" },
];

function parseArgs(argv) {
  const args = {
    prompt: null, from: null, alt: null, caption: null,
    size: "PORTRAIT_1152x2048", quality: "HD", batch: 1,
    endpoint: DEFAULT_ENDPOINT, out: null, dryRun: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--prompt") args.prompt = argv[++i];
    else if (arg === "--from") args.from = argv[++i];
    else if (arg === "--alt") args.alt = argv[++i];
    else if (arg === "--caption") args.caption = argv[++i];
    else if (arg === "--size") args.size = argv[++i];
    else if (arg === "--quality") args.quality = argv[++i];
    else if (arg === "--batch") args.batch = Number(argv[++i]);
    else if (arg === "--endpoint") args.endpoint = argv[++i];
    else if (arg === "--out") args.out = argv[++i];
    else if (arg === "--dry-run") args.dryRun = true;
    else if (arg === "--sizes") args.listSizes = true;
    else if (arg === "--help" || arg === "-h") args.help = true;
  }
  return args;
}

/** Haalt PROMPT / NEGATIEF / ALT-TEKST uit een beeldbriefing van de art-director. */
function readBriefing(path) {
  const source = readFileSync(path, "utf8");
  const grab = (label) => {
    const match = source.match(new RegExp(`^${label}[:\\s]*\\n?([\\s\\S]*?)(?=\\n[A-ZÀ-Ü -]{3,}:|\\n#{1,3} |$)`, "m"));
    return match ? match[1].trim() : null;
  };
  return { prompt: grab("PROMPT"), alt: grab("ALT-TEKST") ?? grab("ALT") };
}

function preflight(prompt) {
  return FORBIDDEN_VISUALS
    .filter((rule) => rule.pattern.test(prompt))
    .map((rule) => rule.why);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    console.log(readFileSync(fileURLToPath(import.meta.url), "utf8").split("*/")[0].replace(/^\/\*\*|^ \* ?/gm, ""));
    process.exit(0);
  }

  if (args.listSizes) {
    console.log("Formaten:", Object.keys(SoulSize).join(", "));
    console.log("Kwaliteit:", Object.keys(SoulQuality).join(", "), "| Batch:", Object.values(BatchSize).join(", "));
    process.exit(0);
  }

  let prompt = args.prompt;
  let alt = args.alt;

  if (args.from) {
    const briefing = readBriefing(args.from);
    prompt = prompt ?? briefing.prompt;
    alt = alt ?? briefing.alt;
    if (!prompt) {
      console.error(`Geen PROMPT-blok gevonden in ${args.from}. Geef er een mee met --prompt.`);
      process.exit(2);
    }
  }

  if (!prompt) {
    console.error('Geef een prompt mee: --prompt "..." of --from <beeldbriefing.md>. Zie --help.');
    process.exit(2);
  }

  // 1 — vraagt de prompt om iets wat niet in beeld mag?
  const visualIssues = preflight(prompt);
  if (visualIssues.length) {
    console.error("✕ De prompt vraagt om beeld dat voor QUITTER niet mag:\n");
    visualIssues.forEach((issue) => console.error(`  - ${issue}`));
    console.error("\nPas de prompt aan. Er zijn geen credits uitgegeven.");
    process.exit(1);
  }

  // 2 — tekst bij het beeld is nog steeds reclame
  const copy = [alt, args.caption].filter(Boolean).join("\n");
  if (copy) {
    const gate = check(copy, { channel: "social_organic" });
    if (gate.verdict === "BLOCK") {
      console.error("✕ De tekst bij dit beeld komt niet door de poort:\n");
      gate.blocks.forEach((f) => console.error(`  [${f.id}] ${f.why}\n      → ${f.instead}`));
      console.error("\nGeen credits uitgegeven.");
      process.exit(1);
    }
    if (gate.warns.length) {
      console.error("! Waarschuwing bij de tekst:");
      gate.warns.forEach((f) => console.error(`  [${f.id}] ${f.why}`));
      console.error("");
    }
  }

  const fullPrompt = `${prompt}. ${BRAND_STYLE} Strictly avoid: ${BRAND_NEGATIVE}`;
  const size = SoulSize[args.size] ?? args.size;
  const quality = SoulQuality[args.quality] ?? args.quality;

  if (args.dryRun) {
    console.log("ENDPOINT:", args.endpoint);
    console.log("FORMAAT :", size, "|", quality, "| batch", args.batch);
    console.log("\nPROMPT:\n" + fullPrompt);
    console.log("\nGeen aanroep gedaan (--dry-run). Geen credits uitgegeven.");
    process.exit(0);
  }

  if (!process.env.HF_CREDENTIALS && !(process.env.HF_API_KEY && process.env.HF_API_SECRET)) {
    console.error('Geen Higgsfield-inloggegevens. Zet: export HF_CREDENTIALS="KEY_ID:KEY_SECRET"');
    console.error("Je maakt ze aan in Higgsfield Cloud onder credentials.");
    process.exit(2);
  }

  const client = createHiggsfieldClient(
    process.env.HF_CREDENTIALS ? { credentials: process.env.HF_CREDENTIALS } : {},
  );

  console.error(`→ Higgsfield Soul · ${size} · ${quality} · ${args.batch}×`);

  let response;
  try {
    response = await client.subscribe(args.endpoint, {
      input: {
        prompt: fullPrompt,
        width_and_height: size,
        quality,
        batch_size: args.batch === 4 ? BatchSize.QUAD : BatchSize.SINGLE,
      },
      withPolling: true,
    });
  } catch (error) {
    const name = error?.constructor?.name ?? "";
    if (name === "CredentialsMissedError" || name === "AuthenticationError") {
      console.error("Inloggegevens werden niet geaccepteerd. Controleer HF_CREDENTIALS.");
    } else if (name === "NotEnoughCreditsError") {
      console.error("Niet genoeg credits op je Higgsfield-account.");
    } else if (name === "ValidationError" || name === "BadInputError") {
      console.error(`Higgsfield accepteerde de aanvraag niet: ${error.message}`);
      console.error(`Klopt het eindpunt "${args.endpoint}" voor jouw account? Kijk het na op`);
      console.error("docs.higgsfield.ai en geef het juiste mee met --endpoint.");
    } else if (name === "TimeoutError") {
      console.error("Higgsfield deed er te lang over. Probeer het opnieuw.");
    } else {
      console.error(`Fout van Higgsfield: ${error?.message ?? error}`);
    }
    process.exit(1);
  }

  if (response.status === "nsfw") {
    console.error("Higgsfield markeerde het resultaat als ongeschikt. Pas de prompt aan.");
    process.exit(1);
  }
  if (response.status !== "completed" || !response.images?.length) {
    console.error(`Geen beeld terug (status: ${response.status}). Volg ${response.status_url}`);
    process.exit(1);
  }

  const outDir = args.out ?? join(here, "output", "images");
  mkdirSync(outDir, { recursive: true });
  const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, "-");

  const saved = [];
  for (const [index, image] of response.images.entries()) {
    const suffix = response.images.length > 1 ? `-${index + 1}` : "";
    const file = join(outDir, `${stamp}${suffix}.jpg`);
    const download = await fetch(image.url);
    if (!download.ok) {
      console.error(`Downloaden mislukt (${download.status}): ${image.url}`);
      continue;
    }
    writeFileSync(file, Buffer.from(await download.arrayBuffer()));
    saved.push(file);
  }

  const noteFile = join(outDir, `${stamp}.md`);
  writeFileSync(
    noteFile,
    [
      `# Beeld — ${stamp}`,
      "",
      "<!-- gate:ignore-start -->",
      `Eindpunt: ${args.endpoint}`,
      `Formaat: ${size} · ${quality} · batch ${args.batch}`,
      `Higgsfield request: ${response.request_id}`,
      `Bestanden: ${saved.map((f) => f.replace(`${here}/`, "")).join(", ") || "geen"}`,
      "<!-- gate:ignore-end -->",
      "",
      "## Prompt",
      "",
      fullPrompt,
      "",
      "## Alt-tekst",
      "",
      alt ?? "[nog invullen — verplicht voor toegankelijkheid]",
      "",
      "## Status",
      "",
      "Niet gepubliceerd. Een mens moet dit beeld bekijken voordat het ergens verschijnt.",
      "Wordt het beeld gebruikt in publieksreclame, dan gaat de hele uiting eerst langs de",
      "Keuringsraad KOAG/KAG.",
      "",
    ].join("\n"),
  );

  console.error("");
  saved.forEach((file) => console.error(`✓ ${file}`));
  console.error(`  notitie: ${noteFile}`);
  console.error("  Niets gepubliceerd. Bekijk het beeld en beslis zelf.");
}

main();
