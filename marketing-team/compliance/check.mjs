#!/usr/bin/env node
/**
 * QUITTER compliance gate — deterministisch.
 *
 * Dit is met opzet geen AI. Een taalmodel dat zijn eigen tekst beoordeelt, keurt zijn eigen
 * tekst goed. Deze poort kent geen enthousiasme: hij vergelijkt tekst met rules.json en geeft
 * een exitcode terug. De compliance-agent draait er daarna nog overheen voor context en toon,
 * maar wat hier BLOCK is, is BLOCK.
 *
 * Gebruik:
 *   node marketing-team/compliance/check.mjs "tekst om te checken"
 *   node marketing-team/compliance/check.mjs --file concept.md --channel social_organic --public
 *   echo "tekst" | node marketing-team/compliance/check.mjs --json
 *
 * Exitcodes: 0 = PASS (mogelijk met waarschuwingen), 1 = BLOCK, 2 = gebruiksfout.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const rules = JSON.parse(readFileSync(resolve(here, "rules.json"), "utf8"));

function parseArgs(argv) {
  const args = { text: null, file: null, channel: null, json: false, public: false };
  const rest = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--file") args.file = argv[++i];
    else if (arg === "--channel") args.channel = argv[++i];
    else if (arg === "--json") args.json = true;
    else if (arg === "--public") args.public = true;
    else if (arg === "--help" || arg === "-h") args.help = true;
    else rest.push(arg);
  }
  if (rest.length) args.text = rest.join(" ");
  return args;
}

function readStdin() {
  try {
    return readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

/** Eén match, met genoeg context om te zien waar het fout gaat. */
function findMatches(text, entry) {
  const hits = [];
  for (const pattern of entry.patterns) {
    const regex = new RegExp(pattern, "gi");
    let match;
    while ((match = regex.exec(text)) !== null) {
      const start = Math.max(0, match.index - 40);
      const end = Math.min(text.length, match.index + match[0].length + 40);
      hits.push({
        id: entry.id,
        rule: entry.rule,
        severity: entry.severity,
        why: entry.why,
        instead: entry.instead,
        matched: match[0],
        context: `…${text.slice(start, end).replace(/\s+/g, " ").trim()}…`,
      });
      if (match.index === regex.lastIndex) regex.lastIndex += 1;
    }
  }
  return hits;
}

export function check(text, { channel = null, isPublicAd = false } = {}) {
  const findings = [];

  for (const entry of rules.blockPatterns) findings.push(...findMatches(text, entry));
  for (const entry of rules.warnPatterns) findings.push(...findMatches(text, entry));

  // Verplichte vermeldingen — alleen afdwingen voor echte publieksreclame.
  if (isPublicAd) {
    const lower = text.toLowerCase();
    const notice = rules.mandatoryNotice;

    if (notice.status === "BEVESTIGD") {
      if (!text.includes(notice.text)) {
        findings.push({
          id: "B1-waarschuwingszin",
          rule: "B1",
          severity: "block",
          why: "De verplichte waarschuwingszin ontbreekt letterlijk.",
          instead: `Neem letterlijk op: "${notice.text}"`,
          matched: "(ontbreekt)",
          context: "",
        });
      }
    } else {
      findings.push({
        id: "B1-onbevestigd",
        rule: "B1",
        severity: "block",
        why: "De verplichte waarschuwingszin is nog niet vastgesteld in rules.json. Zolang die niet klopt, mag er geen publieksreclame naar buiten.",
        instead: "Haal de exacte zin bij de Keuringsraad KOAG/KAG, zet hem in rules.json en zet status op BEVESTIGD.",
        matched: "(status TE_BEVESTIGEN)",
        context: "",
      });
    }

    if (!/nicotine/i.test(text)) {
      findings.push({
        id: "B2-werkzame-stof",
        rule: "B2",
        severity: "warn",
        why: "Het werkzame bestanddeel (nicotine) wordt niet genoemd.",
        instead: "Noem het werkzame bestanddeel bij de merknaam en sterkte.",
        matched: "(ontbreekt)",
        context: "",
      });
    }

    if (!/bijsluiter|patient information|leaflet/i.test(text)) {
      findings.push({
        id: "B3-bijsluiter",
        rule: "B3",
        severity: "block",
        why: "De aansporing om de bijsluiter te lezen ontbreekt.",
        instead: "Voeg de verwijzing naar de bijsluiter toe.",
        matched: "(ontbreekt)",
        context: "",
      });
    }

    if (!/\b18\s*\+|18 jaar|adults 18|18 and over/i.test(text)) {
      findings.push({
        id: "B6-leeftijd",
        rule: "B6",
        severity: "warn",
        why: "Geen leeftijdsvermelding (18+).",
        instead: "Vermeld dat het product bestemd is voor 18 jaar en ouder.",
        matched: "(ontbreekt)",
        context: "",
      });
    }
  }

  const channelInfo = channel ? rules.channels[channel] : null;
  if (channel && !channelInfo) {
    findings.push({
      id: "D-kanaal-onbekend",
      rule: "D",
      severity: "warn",
      why: `Onbekend kanaal "${channel}" — geen kanaalregels toegepast.`,
      instead: `Kies uit: ${Object.keys(rules.channels).join(", ")}`,
      matched: "",
      context: "",
    });
  }
  if (channelInfo && channelInfo.allowed === false) {
    findings.push({
      id: "D-kanaal-verboden",
      rule: "D",
      severity: "block",
      why: `Kanaal "${channel}" is voor QUITTER niet toegestaan. ${channelInfo.notes}`,
      instead: "Kies een ander kanaal.",
      matched: "",
      context: "",
    });
  }

  const blocks = findings.filter((f) => f.severity === "block");
  const warns = findings.filter((f) => f.severity === "warn");

  return {
    verdict: blocks.length > 0 ? "BLOCK" : warns.length > 0 ? "PASS_MET_WAARSCHUWINGEN" : "PASS",
    channel,
    isPublicAd,
    blocks,
    warns,
    koagRequired: channelInfo ? channelInfo.koagRequired : null,
  };
}

function render(result) {
  const lines = [];
  const mark = { BLOCK: "✕", PASS_MET_WAARSCHUWINGEN: "!", PASS: "✓" }[result.verdict];
  lines.push(`${mark} ${result.verdict}${result.channel ? ` · kanaal: ${result.channel}` : ""}`);

  for (const finding of [...result.blocks, ...result.warns]) {
    lines.push("");
    lines.push(`  [${finding.severity.toUpperCase()}] ${finding.id} (regel ${finding.rule})`);
    lines.push(`  ${finding.why}`);
    if (finding.matched && finding.matched !== "(ontbreekt)") lines.push(`  gevonden: "${finding.matched}"`);
    if (finding.context) lines.push(`  context:  ${finding.context}`);
    lines.push(`  → ${finding.instead}`);
  }

  if (result.koagRequired) {
    lines.push("");
    lines.push("  Let op: dit kanaal vraagt voorafgaande keuring door de Keuringsraad KOAG/KAG.");
  }

  lines.push("");
  lines.push("  Deze poort vervangt geen jurist en geen Keuringsraad.");
  return lines.join("\n");
}

const isMain = process.argv[1] && import.meta.url === `file://${resolve(process.argv[1])}`;

if (isMain) {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    console.log(
      [
        "QUITTER compliance gate",
        "",
        '  node check.mjs "tekst"',
        "  node check.mjs --file concept.md --channel social_organic --public",
        "  echo tekst | node check.mjs --json",
        "",
        "  --channel  " + Object.keys(rules.channels).join(", "),
        "  --public   uiting is publieksreclame: verplichte vermeldingen worden afgedwongen",
        "  --json     machineleesbare uitvoer",
      ].join("\n"),
    );
    process.exit(0);
  }

  const text = args.file ? readFileSync(args.file, "utf8") : args.text || readStdin();

  if (!text.trim()) {
    console.error("Geen tekst. Gebruik --help.");
    process.exit(2);
  }

  const result = check(text, { channel: args.channel, isPublicAd: args.public });
  console.log(args.json ? JSON.stringify(result, null, 2) : render(result));
  process.exit(result.verdict === "BLOCK" ? 1 : 0);
}
