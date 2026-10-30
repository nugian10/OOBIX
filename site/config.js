// OOBIX — site configuration.
// The contract is NOT deployed. CONTRACT_ADDRESS stays empty until the
// owner deploys OobixNFT.sol on BNB Smart Chain Mainnet (56) and
// records the real address here. Never fill in a guessed address.
//
// Storage is GitHub (chosen 30 Okt 2026), NOT IPFS. The planned repo is
// nugian10/OOBIX (branch main) — it does NOT exist yet. Once the repo
// exists and is PUBLIC, these raw URLs work and the gallery loads from
// them, wherever the site is hosted (including Vercel with the site
// folder as root — relative ../collection paths would 404 there, so
// the site must NOT use them). Until the push, the gallery shows the
// honest "not yet published" states the app already handles.
const OOBIX_CONFIG = {
  CONTRACT_ADDRESS: "",
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
  // Planned mint pricing (from the contract, not yet live):
  // tokens #1-500: 0.0003 BNB each; #501-3333: FREE (0 BNB).
  PRICE_TIER_1: "0.0003 BNB",
  PRICE_TIER_2: "FREE",
  TIER_1_END: 500,
};
