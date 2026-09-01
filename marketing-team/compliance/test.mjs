#!/usr/bin/env node
/**
 * Tests voor de compliance-poort.
 *
 * Draai dit na elke wijziging in rules.json:
 *   node marketing-team/compliance/test.mjs
 *
 * Een regel die niet getest is, is een regel die stilletjes kapot kan gaan.
 */

import { check } from "./check.mjs";

const cases = [
  {
    // Let op: dit is merkcommunicatie, geen productaanprijzing. Zolang er geen
    // handelsvergunning is, blokkeert A10 elke tekst die het middel zelf aanprijst —
    // inclusief de huidige websiteteksten. Zet product.marketingAuthorisation op
    // "granted" zodra de vergunning er is, dan vervalt die blokkade.
    name: "schone merkcommunicatie passeert",
    text: "90 dagen. Eén beslissing. Een programma met een begin en een eind.",
    options: {},
    expect: "PASS",
  },
  {
    name: "bewijsclaim wordt geblokkeerd",
    text: "Klinisch bewezen effectief bij stoppen met roken.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A3-bewijs"],
  },
  {
    name: "absolute belofte wordt geblokkeerd",
    text: "Je stopt gegarandeerd binnen 90 dagen.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A2-absoluut"],
  },
  {
    name: "veiligheidsclaim wordt geblokkeerd",
    text: "Zonder bijwerkingen en geschikt voor iedereen.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A6-veiligheid"],
  },
  {
    name: "vergelijking met een ander merk wordt geblokkeerd",
    text: "Beter dan Nicorette, en goedkoper ook.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A4-vergelijking"],
  },
  {
    name: "urgentie wordt geblokkeerd",
    text: "Alleen vandaag: start je 90 dagen. Op=op.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A9-urgentie"],
  },
  {
    name: "aanbeveling door artsen wordt geblokkeerd",
    text: "Aanbevolen door artsen in heel Nederland.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A5-aanbeveling"],
  },
  {
    name: "cadeau bij aankoop geeft een waarschuwing",
    text: "Maak je programma af en krijg je QUITTER ZERO gratis erbij.",
    options: {},
    expect: "PASS_MET_WAARSCHUWINGEN",
    expectIds: ["A8-cadeau"],
  },
  {
    name: "percentage geeft een waarschuwing",
    text: "Onze klanten hebben 40% meer rust in hun hoofd.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A3-statistiek"],
  },
  {
    name: "productaanprijzing zonder handelsvergunning wordt geblokkeerd",
    text: "Bestel nu QUITTER 90 met 4 mg nicotinekauwgom voor € 59,95.",
    options: {},
    expect: "BLOCK",
    expectIds: ["A10-geen-vergunning"],
  },
  {
    name: "merkcommunicatie zonder productaanprijzing mag wel",
    text: "Wij bouwen een merk dat stoppen als een programma van negentig dagen behandelt. Laat je e-mailadres achter.",
    options: {},
    expect: "PASS",
  },
  {
    name: "het woord koop in proza is geen aanprijzing",
    text: "Nog niet te koop. Toch koop je hulp per week, doosje voor doosje.",
    options: {},
    expect: "PASS",
  },
  {
    name: "een koopknop is dat wel",
    text: "## Bestellen",
    options: {},
    expect: "BLOCK",
    expectIds: ["A10-geen-vergunning"],
  },
  {
    name: "interne notities tellen niet mee",
    text: "Een merktekst zonder claims.\n<!-- gate:ignore-start -->\nNiet doen: 4 mg noemen, of Bestel nu.\n<!-- gate:ignore-end -->",
    options: {},
    expect: "PASS",
  },
  {
    name: "influencerkanaal is verboden",
    text: "Een nette merktekst zonder claims.",
    options: { channel: "influencer" },
    expect: "BLOCK",
    expectIds: ["D-kanaal-verboden"],
  },
  {
    name: "publieksreclame zonder waarschuwingszin wordt geblokkeerd",
    text: "QUITTER 90 met nicotinekauwgom. Lees de bijsluiter. 18+.",
    options: { isPublicAd: true, channel: "search_ads" },
    expect: "BLOCK",
    expectIds: ["B1-onbevestigd"],
  },
  {
    name: "publieksreclame zonder bijsluiterverwijzing wordt geblokkeerd",
    text: "QUITTER 90 met nicotine. Voor volwassenen van 18 jaar en ouder.",
    options: { isPublicAd: true },
    expect: "BLOCK",
    expectIds: ["B3-bijsluiter"],
  },
];

let failed = 0;

for (const testCase of cases) {
  const result = check(testCase.text, testCase.options);
  const ids = [...result.blocks, ...result.warns].map((f) => f.id);
  const missing = (testCase.expectIds ?? []).filter((id) => !ids.includes(id));
  const verdictOk = result.verdict === testCase.expect;

  if (verdictOk && missing.length === 0) {
    console.log(`  ✓ ${testCase.name}`);
  } else {
    failed += 1;
    console.log(`  ✕ ${testCase.name}`);
    if (!verdictOk) console.log(`      verwacht ${testCase.expect}, kreeg ${result.verdict}`);
    if (missing.length) console.log(`      miste regels: ${missing.join(", ")}`);
    console.log(`      gevonden: ${ids.join(", ") || "niets"}`);
  }
}

console.log("");
console.log(failed === 0 ? `Alle ${cases.length} tests geslaagd.` : `${failed} van ${cases.length} tests gefaald.`);
process.exit(failed === 0 ? 0 : 1);
