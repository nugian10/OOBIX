// Deploy OobixNFT to BNB Testnet (97) or Mainnet (56).
//
// Usage (from ~/workspace/projects/oobix):
//   node scripts/generate-deck.js   # writes scripts/deck.json (already done, do NOT regenerate
//                                    # unless you want a NEW deck — the deckHash would change)
//   cp .env.example .env            # then fill it in — NEVER paste a private key in chat
//   npx hardhat test                # all tests must pass first
//   npx hardhat run scripts/deploy.js --network bscTestnet
//   npx hardhat run scripts/deploy.js --network bsc        # MAINNET, real BNB
//
// The deployer pays gas only. Owner / revenue / agentIdRegistry /
// baseURI / deck are constructor arguments — the deployer address
// does NOT have to be the owner. Owner and revenue were CONFIRMED by
// Nugraha 20:30 WIB 30 Oct 2026 (owner My Wallet, revenue Agentic
// Wallet, same as Mythora/MythRealm/MINTFORM) and are already filled
// in .env.example; BASE_URI is live (GitHub raw, verified 200).
// Minting: mint() takes no arguments, mints 1, requires the
// minter to hold a SPACE ID .ai Agent ID, value must equal
// currentPrice() exactly (0 in the free phase, #501+).
// Mint stays OFF after deploy (mintActive false) — the owner
// turns it on with setMintActive(true) only at launch.
// See contracts/OobixNFT.sol header.
const fs = require("node:fs");
const path = require("node:path");
const { ethers } = require("hardhat");

const DEFAULT_AGENT_ID_REGISTRY = "0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F";

async function main() {
  const network = await ethers.provider.getNetwork();
  const [deployer] = await ethers.getSigners();
  const owner = process.env.OWNER_ADDRESS || "";
  const revenue = process.env.REVENUE_WALLET || "";
  const agentIdRegistry = process.env.AGENT_ID_REGISTRY || DEFAULT_AGENT_ID_REGISTRY;
  const baseURI = process.env.BASE_URI || "";
  const deckPath = path.join(__dirname, "deck.json");
  if (!fs.existsSync(deckPath)) throw new Error("scripts/deck.json not found — run: node scripts/generate-deck.js");
  const deck = JSON.parse(fs.readFileSync(deckPath, "utf8"));

  if (!ethers.isAddress(owner)) throw new Error("OWNER_ADDRESS belum diisi / tidak valid di .env");
  if (!ethers.isAddress(revenue)) throw new Error("REVENUE_WALLET belum diisi / tidak valid di .env");
  if (!ethers.isAddress(agentIdRegistry)) throw new Error("AGENT_ID_REGISTRY tidak valid di .env");
  if (!baseURI.endsWith("/")) throw new Error("BASE_URI harus diakhiri '/' dan menunjuk folder metadata, contoh ipfs://<CID>/ atau https://raw.githubusercontent.com/.../metadata/");
  if (deck.deck.length !== 3333) throw new Error("deck.json: deck length is not 3333");

  console.log("Network:", network.name, "chainId:", Number(network.chainId));
  console.log("Deployer (bayar gas):", deployer.address);
  console.log("Owner:", owner);
  console.log("Revenue wallet:", revenue);
  console.log("Agent ID registry:", agentIdRegistry);
  console.log("Base URI:", baseURI);
  console.log("Deck seed:", deck.seed);
  console.log("Deck hash:", deck.deckHash);
  console.log("Deck counts:", JSON.stringify(deck.counts));
  if (Number(network.chainId) === 56) {
    console.log("!!! MAINNET — BNB SUNGGUHAN, deploy tidak bisa dibatalkan. Periksa alamat di atas sekali lagi.");
  }

  const Factory = await ethers.getContractFactory("OobixNFT");
  const contract = await Factory.deploy(owner, revenue, agentIdRegistry, baseURI, ethers.getBytes(deck.deckHex));
  const receipt = await contract.deploymentTransaction().wait();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log("OobixNFT deployed:", address);
  console.log("Deploy gas used:", receipt.gasUsed.toString());
  console.log("MAX_SUPPLY:", (await contract.MAX_SUPPLY()).toString());
  console.log("TIER_1_END:", (await contract.TIER_1_END()).toString());
  console.log("priceTier1:", ethers.formatEther(await contract.priceTier1()), "BNB");
  console.log("priceTier2:", ethers.formatEther(await contract.priceTier2()), "BNB");
  console.log("currentPrice:", ethers.formatEther(await contract.currentPrice()), "BNB");
  console.log("deckHash on-chain:", await contract.deckHash());
  console.log("mintActive:", await contract.mintActive());
  console.log("agentIdCheckRequired:", await contract.agentIdCheckRequired());
  console.log("BscScan:", `https://bscscan.com/address/${address}`);

  const outDir = path.join(__dirname, "..", "deployments");
  fs.mkdirSync(outDir, { recursive: true });
  const out = path.join(outDir, `oobix-${Number(network.chainId)}.json`);
  fs.writeFileSync(
    out,
    JSON.stringify(
      {
        network: network.name,
        chainId: Number(network.chainId),
        address,
        owner,
        revenueWallet: revenue,
        agentIdRegistry,
        baseURI,
        deckSeed: deck.seed,
        deckHash: deck.deckHash,
        deckCounts: deck.counts,
        maxSupply: 3333,
        tier1End: 500,
        priceTier1: "0.0003",
        priceTier2: "0",
        mintActive: false,
        agentIdCheckRequired: true,
        model: "wedo-gacha",
        deployGasUsed: receipt.gasUsed.toString(),
      },
      null,
      2
    )
  );
  console.log("Saved:", out);
  console.log("Langkah berikut: verifikasi source di BscScan, lalu setBaseURI (kalau metadata belum siap), setMintActive(true) HANYA saat launch.");
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
