const fs = require("node:fs");
const path = require("node:path");
const { ethers } = require("hardhat");
async function main() {
  const deck = JSON.parse(fs.readFileSync(path.join(__dirname, "deck.json"), "utf8"));
  const [owner, revenue] = await ethers.getSigners();
  const Mock = await ethers.getContractFactory("MockAgentIdNFT");
  const mock = await Mock.deploy();
  await mock.waitForDeployment();
  const Factory = await ethers.getContractFactory("OobixNFT");
  const contract = await Factory.deploy(owner.address, revenue.address, await mock.getAddress(), "ipfs://test/", ethers.getBytes(deck.deckHex));
  const tx = contract.deploymentTransaction();
  const receipt = await tx.wait();
  await contract.waitForDeployment();
  console.log("deploy gasUsed:", receipt.gasUsed.toString());
  console.log("deckHash on-chain:", await contract.deckHash());
  console.log("deckHash expected:", deck.deckHash);
  console.log("match:", (await contract.deckHash()) === deck.deckHash);
  const art = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "artifacts", "contracts", "OobixNFT.sol", "OobixNFT.json"), "utf8"));
  console.log("creation bytecode bytes:", (art.bytecode.length - 2) / 2);
  console.log("runtime bytecode bytes:", (art.deployedBytecode.length - 2) / 2);
  // gas cost at BSC gas prices
  for (const gwei of ["0.05", "1", "3"]) {
    const cost = receipt.gasUsed * ethers.parseUnits(gwei, "gwei");
    console.log(`cost at ${gwei} gwei:`, ethers.formatEther(cost), "BNB");
  }
}
main().catch((e) => { console.error(e); process.exitCode = 1; });
