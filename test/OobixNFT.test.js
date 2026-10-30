const { expect } = require("chai");
const { ethers } = require("hardhat");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");
const fs = require("node:fs");
const path = require("node:path");

const TIER1 = ethers.parseEther("0.0003");
const TIER2 = ethers.parseEther("0.0008"); // v2: tier 2 is paid (v1 was FREE = 0)
const REAL_REGISTRY = "0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F";
const DECK = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "scripts", "deck.json"), "utf8"));
const DECK_BYTES = ethers.getBytes(DECK.deckHex);

async function deployFixture() {
  const [owner, revenue, alice, bob] = await ethers.getSigners();
  const Mock = await ethers.getContractFactory("MockAgentIdNFT");
  const mock = await Mock.deploy();
  await mock.waitForDeployment();
  const Factory = await ethers.getContractFactory("contracts/OobixNFT.sol:OobixNFT");
  const contract = await Factory.deploy(
    owner.address,
    revenue.address,
    await mock.getAddress(),
    "ipfs://bafyTESTmetadata/",
    DECK_BYTES
  );
  await contract.waitForDeployment();
  return { contract, mock, owner, revenue, alice, bob };
}

async function giveAgentId(mock, wallet) {
  await mock.mintTo(wallet.address);
}

describe("OobixNFT (WEDO model, OOBIX rules)", function () {
  it("has the right name, symbol, supply, tiers, registry, deck and defaults", async function () {
    const { contract, mock, owner, revenue } = await deployFixture();
    expect(await contract.name()).to.equal("OOBIX");
    expect(await contract.symbol()).to.equal("OOBX");
    expect(await contract.MAX_SUPPLY()).to.equal(3333);
    expect(await contract.TIER_1_END()).to.equal(500);
    expect(await contract.DEFAULT_AGENT_ID_REGISTRY()).to.equal(REAL_REGISTRY);
    expect(await contract.agentIdRegistry()).to.equal(await mock.getAddress());
    expect(await contract.agentIdCheckRequired()).to.equal(true);
    expect(await contract.priceTier1()).to.equal(TIER1);
    expect(await contract.priceTier2()).to.equal(TIER2);
    expect(await contract.priceForTokenId(1)).to.equal(TIER1);
    expect(await contract.priceForTokenId(500)).to.equal(TIER1);
    expect(await contract.priceForTokenId(501)).to.equal(TIER2);
    expect(await contract.priceForTokenId(3333)).to.equal(TIER2);
    expect(await contract.currentPrice()).to.equal(TIER1);
    expect(await contract.getMintPrice()).to.equal(TIER1);
    expect(await contract.mintActive()).to.equal(false);
    expect(await contract.mintOpen()).to.equal(false);
    expect(await contract.owner()).to.equal(owner.address);
    expect(await contract.revenueWallet()).to.equal(revenue.address);
    expect(await contract.totalSupply()).to.equal(0);
    expect(await contract.totalMinted()).to.equal(0);
    expect(await contract.nextTokenId()).to.equal(1);
    expect(await contract.deckHash()).to.equal(DECK.deckHash);
    await expect(contract.priceForTokenId(0)).to.be.revertedWithCustomError(contract, "ExceedsMaxSupply");
    await expect(contract.priceForTokenId(3334)).to.be.revertedWithCustomError(contract, "ExceedsMaxSupply");
  });

  it("selectors: mint() is 0x1249c58b and rarityOf(uint256) is 0xdd3b5f9a", async function () {
    const { contract } = await deployFixture();
    expect(contract.interface.getFunction("mint()").selector).to.equal("0x1249c58b");
    expect(contract.interface.getFunction("rarityOf(uint256)").selector).to.equal("0xdd3b5f9a");
    expect(contract.interface.getFunction("currentPrice()").selector).to.equal("0x9d1b464a");
    expect(contract.interface.getFunction("deckHash()").selector).to.equal("0x8830dea2");
    expect(contract.interface.getFunction("mintOpen()").selector).to.equal("0x24bbd049");
    expect(contract.interface.getFunction("totalMinted()").selector).to.equal("0xa2309ff8");
    expect(contract.interface.getFunction("holdsAgentId(address)").selector).to.equal("0x11213086");
  });

  it("deck: exact tier counts over all 3333 slots, rarityOf matches the generator deck", async function () {
    const { contract } = await deployFixture();
    const counts = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 };
    for (const t of DECK.deck) counts[t]++;
    expect(counts).to.deep.equal({ 0: 2000, 1: 800, 2: 333, 3: 150, 4: 50 });
    expect(DECK.deck.length).to.equal(3333);
    // Sampled on-chain reads match the generator deck exactly.
    for (const id of [1, 2, 13, 100, 500, 501, 1000, 2000, 3333]) {
      expect(await contract.rarityOf(id)).to.equal(DECK.deck[id - 1]);
    }
    await expect(contract.rarityOf(0)).to.be.revertedWithCustomError(contract, "ExceedsMaxSupply");
    await expect(contract.rarityOf(3334)).to.be.revertedWithCustomError(contract, "ExceedsMaxSupply");
  });

  it("rejects a deck with wrong length or wrong tier counts (InvalidDeck)", async function () {
    const [owner, revenue] = await ethers.getSigners();
    const Mock = await ethers.getContractFactory("MockAgentIdNFT");
    const mock = await Mock.deploy();
    await mock.waitForDeployment();
    const Factory = await ethers.getContractFactory("contracts/OobixNFT.sol:OobixNFT");
    await expect(
      Factory.deploy(owner.address, revenue.address, await mock.getAddress(), "", DECK_BYTES.slice(0, 100))
    ).to.be.revertedWithCustomError(Factory, "InvalidDeck");
    const allCommon = new Uint8Array(3333); // 3333 Commons, counts wrong
    await expect(
      Factory.deploy(owner.address, revenue.address, await mock.getAddress(), "", allCommon)
    ).to.be.revertedWithCustomError(Factory, "InvalidDeck");
  });

  it("refuses mint while inactive", async function () {
    const { contract, mock, alice } = await deployFixture();
    await giveAgentId(mock, alice);
    await expect(contract.connect(alice).mint({ value: TIER1 })).to.be.revertedWithCustomError(
      contract,
      "MintInactive"
    );
  });

  it("rejects mint without an Agent ID (NoAgentId)", async function () {
    const { contract, owner } = await deployFixture();
    await contract.connect(owner).setMintActive(true);
    await expect(contract.mint({ value: TIER1 })).to.be.revertedWithCustomError(contract, "NoAgentId");
  });

  it("mints token #1 with exact tier-1 price, deck rarity, seed, tokenURI, mintedBy", async function () {
    const { contract, mock, owner, revenue, alice } = await deployFixture();
    await giveAgentId(mock, alice);
    expect(await contract.holdsAgentId(alice.address)).to.equal(true);
    expect(await contract.hasAgentId(alice.address)).to.equal(true);
    expect(await contract.holdsAgentId(owner.address)).to.equal(false);
    await contract.connect(owner).setMintActive(true);
    expect(await contract.mintOpen()).to.equal(true);
    const rarity1 = DECK.deck[0];
    const revenueBefore = await ethers.provider.getBalance(revenue.address);
    const addr = await contract.getAddress();
    await expect(contract.connect(alice).mint({ value: TIER1 }))
      .to.emit(contract, "Minted")
      .withArgs(alice.address, 1, TIER1, rarity1, anyValue);
    // Paid mint forwards straight to the revenue (Agentic) wallet
    // in the same call — the contract keeps nothing.
    expect(await ethers.provider.getBalance(revenue.address)).to.equal(revenueBefore + TIER1);
    expect(await ethers.provider.getBalance(addr)).to.equal(0);
    expect(await contract.ownerOf(1)).to.equal(alice.address);
    expect(await contract.tokenURI(1)).to.equal("ipfs://bafyTESTmetadata/1.json");
    expect(await contract.totalSupply()).to.equal(1);
    expect(await contract.totalMinted()).to.equal(1);
    expect(await contract.nextTokenId()).to.equal(2);
    expect(await contract.tokenSeed(1)).to.not.equal(ethers.ZeroHash);
    expect(await contract.tokenRarity(1)).to.equal(rarity1);
    expect(await contract.mintedBy(alice.address)).to.equal(1);
    expect(await contract.currentPrice()).to.equal(TIER1);
  });

  it("has NO per-wallet limit: the same wallet can mint again (mintedBy is a counter only)", async function () {
    const { contract, mock, owner, alice } = await deployFixture();
    await giveAgentId(mock, alice);
    await contract.connect(owner).setMintActive(true);
    await contract.connect(alice).mint({ value: TIER1 });
    await expect(contract.connect(alice).mint({ value: TIER1 }))
      .to.emit(contract, "Minted")
      .withArgs(alice.address, 2, TIER1, DECK.deck[1], anyValue);
    expect(await contract.ownerOf(1)).to.equal(alice.address);
    expect(await contract.ownerOf(2)).to.equal(alice.address);
    expect(await contract.mintedBy(alice.address)).to.equal(2);
    expect(await contract.totalSupply()).to.equal(2);
  });

  it("rejects underpayment and overpayment in the paid phase", async function () {
    const { contract, mock, owner, alice } = await deployFixture();
    await giveAgentId(mock, alice);
    await contract.connect(owner).setMintActive(true);
    await expect(contract.connect(alice).mint({ value: TIER1 - 1n })).to.be.revertedWithCustomError(
      contract,
      "IncorrectPayment"
    );
    await expect(contract.connect(alice).mint({ value: TIER1 + 1n })).to.be.revertedWithCustomError(
      contract,
      "IncorrectPayment"
    );
  });

  it("rejects calls from contracts (NoContracts)", async function () {
    const { contract, mock, owner } = await deployFixture();
    const Caller = await ethers.getContractFactory("MockCaller");
    const caller = await Caller.deploy();
    await caller.waitForDeployment();
    await mock.mintTo(await caller.getAddress());
    await contract.connect(owner).setMintActive(true);
    expect(await caller.tryMint.staticCall(await contract.getAddress(), { value: TIER1 })).to.equal(false);
    expect(await contract.totalSupply()).to.equal(0);
  });

  it("boundary: #500 costs 0.0003, #501 costs 0.0008, a 0-value mint reverts, paid #501 forwards to revenue", async function () {
    this.timeout(300000);
    const { contract, mock, owner, revenue, alice } = await deployFixture();
    await giveAgentId(mock, alice);
    await contract.connect(owner).setMintActive(true);
    for (let i = 0; i < 500; i++) {
      await contract.connect(alice).mint({ value: TIER1 });
    }
    expect(await contract.totalSupply()).to.equal(500);
    expect(await contract.nextTokenId()).to.equal(501);
    expect(await contract.ownerOf(500)).to.equal(alice.address);
    expect(await contract.currentPrice()).to.equal(TIER2);
    expect(await contract.priceForTokenId(500)).to.equal(TIER1);
    expect(await contract.priceForTokenId(501)).to.equal(TIER2);
    // #501 with 0 value reverts: tier 2 is paid in v2 (no free phase).
    await expect(contract.connect(alice).mint({ value: 0 })).to.be.revertedWithCustomError(
      contract,
      "IncorrectPayment"
    );
    // #501 mints with exactly 0.0008, carries its deck rarity, forwards to revenue.
    const revenueBefore = await ethers.provider.getBalance(revenue.address);
    await expect(contract.connect(alice).mint({ value: TIER2 }))
      .to.emit(contract, "Minted")
      .withArgs(alice.address, 501, TIER2, DECK.deck[500], anyValue);
    expect(await contract.totalSupply()).to.equal(501);
    expect(await contract.tokenRarity(501)).to.equal(DECK.deck[500]);
    expect(await ethers.provider.getBalance(await contract.getAddress())).to.equal(0);
    expect(await ethers.provider.getBalance(revenue.address)).to.equal(revenueBefore + TIER2);
    // Underpaying in tier 2 (1 wei) also reverts.
    await expect(contract.connect(alice).mint({ value: 1 })).to.be.revertedWithCustomError(
      contract,
      "IncorrectPayment"
    );
  });

  it("owner can change registry and disable the Agent ID check — then anyone can mint; re-enabling blocks again", async function () {
    const { contract, owner, alice } = await deployFixture();
    await contract.connect(owner).setMintActive(true);
    await expect(contract.connect(alice).mint({ value: TIER1 })).to.be.revertedWithCustomError(
      contract,
      "NoAgentId"
    );
    await contract.connect(owner).setAgentIdCheckRequired(false);
    expect(await contract.agentIdCheckRequired()).to.equal(false);
    await contract.connect(alice).mint({ value: TIER1 });
    expect(await contract.ownerOf(1)).to.equal(alice.address);
    await contract.connect(owner).setAgentIdCheckRequired(true);
    await expect(contract.connect(alice).mint({ value: TIER1 })).to.be.revertedWithCustomError(
      contract,
      "NoAgentId"
    );
    await expect(contract.connect(alice).setAgentIdCheckRequired(true)).to.be.revertedWithCustomError(
      contract,
      "OwnableUnauthorizedAccount"
    );
    await expect(
      contract.connect(owner).setAgentIdRegistry(ethers.ZeroAddress)
    ).to.be.revertedWithCustomError(contract, "InvalidAddress");
  });

  it("with the real SPACE ID registry on a local chain, mint reverts NoAgentId", async function () {
    const [owner, revenue] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("contracts/OobixNFT.sol:OobixNFT");
    const contract = await Factory.deploy(owner.address, revenue.address, REAL_REGISTRY, "", DECK_BYTES);
    await contract.waitForDeployment();
    expect(await contract.agentIdRegistry()).to.equal(REAL_REGISTRY);
    await contract.connect(owner).setMintActive(true);
    expect(await contract.holdsAgentId(owner.address)).to.equal(false);
    await expect(contract.connect(owner).mint({ value: TIER1 })).to.be.revertedWithCustomError(
      contract,
      "NoAgentId"
    );
  });

  it("tier prices: tier2 may be 0 before the first mint, tier1 must stay >0, changeable only before the first mint", async function () {
    const { contract, mock, owner, alice } = await deployFixture();
    // v2 default is 0.0008, but setting tier2 = 0 pre-mint is still valid.
    await contract.connect(owner).setTierPrices(ethers.parseEther("0.0004"), 0);
    expect(await contract.priceTier1()).to.equal(ethers.parseEther("0.0004"));
    expect(await contract.priceTier2()).to.equal(0);
    await expect(
      contract.connect(owner).setTierPrices(0, 0)
    ).to.be.revertedWithCustomError(contract, "InvalidPrice");
    await contract.connect(owner).setTierPrices(TIER1, TIER2);
    await expect(
      contract.connect(alice).setTierPrices(TIER1, TIER2)
    ).to.be.revertedWithCustomError(contract, "OwnableUnauthorizedAccount");
    await giveAgentId(mock, alice);
    await contract.connect(owner).setMintActive(true);
    await contract.connect(alice).mint({ value: TIER1 });
    await expect(
      contract.connect(owner).setTierPrices(TIER1, TIER2)
    ).to.be.revertedWithCustomError(contract, "PricesLocked");
    expect(await contract.TIER_1_END()).to.equal(500);
  });

  it("owner-only admin: non-owner setMintActive / setBaseURI / setRevenueWallet revert", async function () {
    const { contract, owner, alice } = await deployFixture();
    await expect(contract.connect(alice).setMintActive(true)).to.be.revertedWithCustomError(
      contract,
      "OwnableUnauthorizedAccount"
    );
    await expect(contract.connect(alice).setBaseURI("ipfs://x/")).to.be.revertedWithCustomError(
      contract,
      "OwnableUnauthorizedAccount"
    );
    await expect(
      contract.connect(alice).setRevenueWallet(alice.address)
    ).to.be.revertedWithCustomError(contract, "OwnableUnauthorizedAccount");
    await expect(
      contract.connect(owner).setRevenueWallet(ethers.ZeroAddress)
    ).to.be.revertedWithCustomError(contract, "InvalidAddress");
    await contract.connect(owner).setBaseURI("ipfs://new/");
    expect(await contract.baseURI()).to.equal("ipfs://new/");
  });

  it("paid mints forward straight to revenue — contract keeps 0, withdraw has nothing to send", async function () {
    const { contract, mock, owner, revenue, alice, bob } = await deployFixture();
    await giveAgentId(mock, alice);
    await giveAgentId(mock, bob);
    await contract.connect(owner).setMintActive(true);
    const revenueBefore = await ethers.provider.getBalance(revenue.address);
    await contract.connect(alice).mint({ value: TIER1 });
    await contract.connect(bob).mint({ value: TIER1 });
    const addr = await contract.getAddress();
    expect(await ethers.provider.getBalance(addr)).to.equal(0);
    expect(await ethers.provider.getBalance(revenue.address)).to.equal(revenueBefore + TIER1 * 2n);
    await expect(contract.connect(alice).withdraw()).to.be.revertedWithCustomError(
      contract,
      "OwnableUnauthorizedAccount"
    );
    await expect(contract.connect(owner).withdraw()).to.be.revertedWithCustomError(contract, "NoFunds");
  });

  it("tokenURI reverts for a nonexistent token", async function () {
    const { contract } = await deployFixture();
    await expect(contract.tokenURI(1)).to.be.revertedWithCustomError(contract, "ERC721NonexistentToken");
  });

  it("supply cap: minting all 3333, then currentPrice and mint() revert SoldOut", async function () {
    this.timeout(600000);
    const { contract, mock, owner, alice } = await deployFixture();
    await giveAgentId(mock, alice);
    await contract.connect(owner).setMintActive(true);
    for (let i = 1; i <= 3333; i++) {
      await contract.connect(alice).mint({ value: i <= 500 ? TIER1 : TIER2 });
    }
    expect(await contract.totalSupply()).to.equal(3333);
    expect(await contract.totalMinted()).to.equal(3333);
    expect(await contract.nextTokenId()).to.equal(3334);
    expect(await contract.ownerOf(3333)).to.equal(alice.address);
    expect(await contract.tokenRarity(3333)).to.equal(DECK.deck[3332]);
    expect(await contract.mintedBy(alice.address)).to.equal(3333);
    await expect(contract.currentPrice()).to.be.revertedWithCustomError(contract, "SoldOut");
    await expect(contract.getMintPrice()).to.be.revertedWithCustomError(contract, "SoldOut");
    await expect(contract.connect(alice).mint({ value: 0 })).to.be.revertedWithCustomError(
      contract,
      "SoldOut"
    );
  });
});
