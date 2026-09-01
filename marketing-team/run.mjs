#!/usr/bin/env node
/**
 * QUITTER marketingteam — runner.
 *
 * Zet één teamlid aan het werk en stuurt het resultaat automatisch door de
 * compliance-poort. Wordt de tekst geblokkeerd, dan krijgt de agent de regels
 * terug en herschrijft hij één keer. Wat daarna nog blokkeert, komt niet in je
 * outputmap terecht zonder waarschuwing.
 *
 * Gebruik:
 *   node marketing-team/run.mjs copywriter --brief "3 zoekadvertenties, 30 tekens kop"
 *   node marketing-team/run.mjs email --brief-file brief.md --lang nl
 *   node marketing-team/run.mjs social --brief "LinkedIn over waarom we programma's verkopen" --channel social_organic
 *
 * Vlaggen:
 *   --channel   own_site | email | search_ads | social_organic | social_paid | pr | b2b
 *   --public    de uiting is publieksreclame (verplichte vermeldingen worden afgedwongen)
 *   --lang      nl (standaard) of en
 *   --out       map voor het resultaat (standaard marketing-team/output)
 *   --dry-run   toon de systeemprompt en stop, zonder de API aan te roepen
 *
 * Inloggen: de SDK pakt ANTHROPIC_API_KEY uit je omgeving, of een profiel van
 * `ant auth login`. Je hoeft niets in dit bestand te zetten.
 */

import Anthropic from "@anthropic-ai/sdk";
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import { check } from "./compliance/check.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const MODEL = "claude-opus-5";

/** De systeemprompt van een agent staat in het ```text-blok van zijn markdownbestand. */
function loadAgentPrompt(name) {
  const files = readdirSync(join(here, "agents"));
  const match = files.find(
    (file) => file.replace(/^\d+-/, "").replace(/\.md$/, "") === name,
  );
  if (!match) {
    const available = files
      .filter((file) => !file.startsWith("_"))
      .map((file) => file.replace(/^\d+-/, "").replace(/\.md$/, ""));
    throw new Error(`Onbekende agent "${name}". Beschikbaar: ${available.join(", ")}`);
  }

  const source = readFileSync(join(here, "agents", match), "utf8");
  const block = source.match(/```text\n([\s\S]*?)```/);
  if (!block) throw new Error(`Geen systeemprompt gevonden in ${match}`);
  return block[1].trim();
}

function loadPreamble() {
  const source = readFileSync(join(here, "agents", "_preamble.md"), "utf8");
  const block = source.match(/```text\n([\s\S]*?)```/);
  return block ? block[1].trim() : "";
}

function buildSystemPrompt(agentName) {
  const preamble = loadPreamble();
  const agent = loadAgentPrompt(agentName).replace("[GEDEELDE PREAMBULE]", "").trim();
  const voice = readFileSync(join(here, "brand", "voice.md"), "utf8");
  const rules = readFileSync(join(here, "compliance", "rules.md"), "utf8");

  return [
    preamble,
    "",
    "---",
    "",
    agent,
    "",
    "---",
    "",
    "# Merkstem",
    voice,
    "",
    "---",
    "",
    "# De volledige juridische regels",
    rules,
  ].join("\n");
}

function parseArgs(argv) {
  const args = { agent: null, brief: null, channel: null, lang: "nl", out: null, public: false, dryRun: false };
  const rest = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--brief") args.brief = argv[++i];
    else if (arg === "--brief-file") args.brief = readFileSync(argv[++i], "utf8");
    else if (arg === "--channel") args.channel = argv[++i];
    else if (arg === "--lang") args.lang = argv[++i];
    else if (arg === "--out") args.out = argv[++i];
    else if (arg === "--public") args.public = true;
    else if (arg === "--dry-run") args.dryRun = true;
    else rest.push(arg);
  }
  args.agent = rest[0] ?? null;
  return args;
}

async function ask(client, system, messages) {
  const stream = client.messages.stream({
    model: MODEL,
    max_tokens: 64000,
    thinking: { type: "adaptive" },
    output_config: { effort: "high" },
    system,
    messages,
  });

  const message = await stream.finalMessage();

  if (message.stop_reason === "refusal") {
    throw new Error(
      `Het model weigerde deze opdracht (${message.stop_details?.category ?? "onbekend"}). ` +
        "Formuleer de briefing anders.",
    );
  }

  return message.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("\n")
    .trim();
}

function describe(result) {
  return [...result.blocks, ...result.warns]
    .map((finding) => `- [${finding.severity.toUpperCase()}] ${finding.id} (${finding.rule}): ${finding.why} → ${finding.instead}`)
    .join("\n");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!args.agent || !args.brief) {
    console.error(
      [
        "Gebruik: node marketing-team/run.mjs <agent> --brief \"...\" [--channel <kanaal>] [--public] [--lang nl|en]",
        "",
        "Agents: orchestrator, research, strategist, copywriter, seo-content, social,",
        "        email-lifecycle, art-director, compliance-officer, analyst",
      ].join("\n"),
    );
    process.exit(2);
  }

  const system = buildSystemPrompt(args.agent);
  const gateOptions = { channel: args.channel, isPublicAd: args.public };

  const briefing = [
    `OPDRACHT: ${args.brief}`,
    `TAAL: ${args.lang}`,
    args.channel ? `KANAAL: ${args.channel}` : "KANAAL: nog niet bepaald",
    `PUBLIEKSRECLAME: ${args.public ? "ja — de verplichte vermeldingen zijn verplicht" : "nee"}`,
  ].join("\n");

  if (args.dryRun) {
    console.log(system);
    console.log("\n--- BRIEFING ---\n");
    console.log(briefing);
    process.exit(0);
  }

  const client = new Anthropic();
  const messages = [{ role: "user", content: briefing }];

  console.error(`→ ${args.agent} aan het werk…`);
  let text;
  try {
    text = await ask(client, system, messages);
  } catch (error) {
    if (error instanceof Anthropic.AuthenticationError) {
      console.error("Geen geldige inloggegevens. Zet ANTHROPIC_API_KEY of log in met `ant auth login`.");
    } else if (error instanceof Anthropic.RateLimitError) {
      console.error("Rate limit geraakt. Probeer het zo opnieuw.");
    } else if (error instanceof Anthropic.APIStatusError) {
      console.error(`API-fout ${error.status}: ${error.message}`);
    } else if (error instanceof Anthropic.APIConnectionError) {
      console.error("Geen verbinding met de API.");
    } else {
      console.error(error.message);
    }
    process.exit(1);
  }

  let result = check(text, gateOptions);
  let rewritten = false;

  if (result.verdict === "BLOCK") {
    console.error(`→ poort blokkeerde (${result.blocks.length}). Eén herschrijfronde…`);
    messages.push({ role: "assistant", content: text });
    messages.push({
      role: "user",
      content: [
        "De compliance-poort heeft dit geblokkeerd:",
        "",
        describe(result),
        "",
        "Herschrijf de tekst zodat elk blokkerend punt verdwijnt. Haal de claim weg in plaats van hem",
        "te verzachten. Lever alleen de herschreven versie.",
      ].join("\n"),
    });
    text = await ask(client, system, messages);
    result = check(text, gateOptions);
    rewritten = true;
  }

  const outDir = args.out ?? join(here, "output");
  mkdirSync(outDir, { recursive: true });
  const stamp = new Date().toISOString().slice(0, 16).replace(/[:T]/g, "-");
  const file = join(outDir, `${stamp}-${args.agent}.md`);

  const header = [
    `<!-- agent: ${args.agent} | kanaal: ${args.channel ?? "n.v.t."} | publieksreclame: ${args.public ? "ja" : "nee"}`,
    `     poort: ${result.verdict}${rewritten ? " (na één herschrijfronde)" : ""}`,
    `     ${result.koagRequired ? "KOAG/KAG-keuring vereist voor publicatie" : ""}`,
    "     Nog niet gepubliceerd: een mens moet dit lezen en goedkeuren. -->",
    "",
  ].join("\n");

  writeFileSync(file, header + text + "\n");

  console.error("");
  console.error(`${result.verdict === "BLOCK" ? "✕" : result.verdict === "PASS" ? "✓" : "!"} ${result.verdict}`);
  if (result.blocks.length || result.warns.length) console.error(describe(result));
  if (result.koagRequired) console.error("\n  Publieksreclame op dit kanaal moet vooraf door de Keuringsraad KOAG/KAG.");
  console.error(`\n  Opgeslagen: ${file}`);
  console.error("  Niets is gepubliceerd. Lees het, en beslis zelf.");

  process.exit(result.verdict === "BLOCK" ? 1 : 0);
}

main();
