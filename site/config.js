// OOBIX — site configuration.
// The v2 contract IS deployed: OobixNFT at 0x2aE2969ae37CB39abc45375598cEE530C181838A
// on BNB Smart Chain Mainnet (56), deployed 30 Oct 2026 ~22:27 WIB by My Wallet
// (deploy tx 0xe26f701815d0d646747ae86c36ad515f305e604c3e9e5459d1da38fac99d8bac,
// block 130688929). Mint is NOT active yet (mintActive false) — it opens
// when the owner activates it. v1 contract 0x607840e0a3675cf2181c98453484eb785ddd2d83
// (19 minted, tier 2 FREE) is superseded and stays live on-chain.
// Never fill in a guessed address.
//
// NOTE: this MUST be window.OOBIX_CONFIG (not a bare const) — app.js reads
// window.OOBIX_CONFIG, and a top-level const in a classic script does NOT
// attach to window. Using const here silently kills the whole site script:
// the prompt box stays on "Loading prompt…", the copy button does nothing,
// and the live counts never run (bug found 30 Oct 2026 21:33 WIB).
//
// Storage is GitHub (chosen 30 Okt 2026), NOT IPFS. The repo is
// nugian10/OOBIX (branch main) — it exists and is PUBLIC, so these raw URLs
// work and the gallery loads from them, wherever the site is hosted
// (including Vercel with the site folder as root — relative ../collection
// paths would 404 there, so the site must NOT use them).
window.OOBIX_CONFIG = {
  CONTRACT_ADDRESS: "0x2aE2969ae37CB39abc45375598cEE530C181838A",
  CHAIN_ID: 56,
  CHAIN_NAME: "BNB Smart Chain Mainnet",
  TOTAL_SUPPLY: 3333,
  DECK_HASH: "0xb44bbbfc75bc6bfda8673ea71b6eef7a3389c78d0e30de7b7937c930acddc1a5",
  IMAGES_BASE: "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/images/",
  METADATA_BASE: "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/metadata/",
  // Collection data loads from the public GitHub repo (see above).
  COLLECTION_JSON: "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/collection.json",
  ALL_TOKENS_JSON: "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/all-tokens.json",
  IMAGE_PATH: (id) => `https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/images/${id}.svg`,
  METADATA_PATH: (id) => `https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/metadata/${id}.json`,
  RARITIES: ["Common", "Uncommon", "Rare", "Epic", "Legendary"],
  RARITY_COUNTS: { Common: 2000, Uncommon: 800, Rare: 333, Epic: 150, Legendary: 50 },
  SPECIES: ["Round Blob", "Tall Thin", "Long Neck", "Spiky", "Quadruped", "Floating Jelly", "Wide Flat", "One-Eye Orb"],
  // Mint pricing (from the v2 contract):
  // tokens #1-500: 0.0003 BNB each; #501-3333: 0.0008 BNB each.
  PRICE_TIER_1: "0.0003 BNB",
  PRICE_TIER_2: "0.0008 BNB",
  TIER_1_END: 500,
};
