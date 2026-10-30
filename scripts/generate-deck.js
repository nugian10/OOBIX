// OOBIX gacha deck generator — deterministic, seeded shuffle.
// Usage: node scripts/generate-deck.js
// Writes scripts/deck.json: { seed, counts, deck (array of tier codes 0-4),
// deckHex ("0x..." 3333 bytes, 1 byte per token), deckHash (keccak256) }.
// The same file is read by scripts/deploy.js and by the Hardhat tests,
// so the on-chain deck is exactly the deck generated here.
//
// Tier codes (OOBIX mapping — DIFFERS from WEDO):
//   0 Common, 1 Uncommon, 2 Rare, 3 Epic, 4 Legendary
// Exact counts (must sum to 3333):
//   Common 2000, Uncommon 800, Rare 333, Epic 150, Legendary 50
//
// PRNG: mulberry32 seeded from the seed string via FNV-1a, then
// Fisher-Yates. Deterministic: same seed always gives the same deck.
// Anyone can re-run this script and check deckHash matches the
// on-chain deckHash() — that is the whole point of the commitment.
const fs = require("node:fs");
const path = require("node:path");
const { ethers } = require("ethers");

const SEED = "OOBIX-DECK-SEED-2026-10-30-v1";
const COUNTS = { 0: 2000, 1: 800, 2: 333, 3: 150, 4: 50 };
const TOTAL = 3333;

function fnv1a(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

function mulberry32(a) {
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function main() {
  const deck = [];
  for (const [tier, count] of Object.entries(COUNTS)) {
    for (let i = 0; i < count; i++) deck.push(Number(tier));
  }
  if (deck.length !== TOTAL) throw new Error(`deck length ${deck.length} != ${TOTAL}`);

  const rand = mulberry32(fnv1a(SEED));
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }

  const counts = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 };
  for (const t of deck) counts[t]++;
  for (const [tier, count] of Object.entries(COUNTS)) {
    if (counts[tier] !== count) throw new Error(`count mismatch tier ${tier}: ${counts[tier]} != ${count}`);
  }

  const deckHex = ethers.hexlify(new Uint8Array(deck));
  const deckHash = ethers.keccak256(deckHex);
  const out = {
    seed: SEED,
    total: TOTAL,
    counts: { Common: 2000, Uncommon: 800, Rare: 333, Epic: 150, Legendary: 50 },
    tierCodes: { 0: "Common", 1: "Uncommon", 2: "Rare", 3: "Epic", 4: "Legendary" },
    deck,
    deckHex,
    deckHash,
  };
  const outPath = path.join(__dirname, "deck.json");
  fs.writeFileSync(outPath, JSON.stringify(out, null, 2) + "\n");
  console.log("seed:    ", SEED);
  console.log("total:   ", TOTAL);
  console.log("counts:  ", JSON.stringify(counts));
  console.log("deckHash:", deckHash);
  console.log("wrote:   ", outPath);
}

main();
