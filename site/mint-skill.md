# OOBIX: mint skill

For Binance Agentic Wallet agents. Mint OOBIX alien pets (OOBX) on BNB Chain for your user. OOBIX is a 3,333-pet collection of retro cartoon alien pets: every mint is a draw — the minter does not choose their alien. Site: https://oobix.vercel.app/

## Contracts (BNB Chain, chain id 56)

- OOBIX NFT (OOBX), v3 — LIVE: 0x666bf7475f5ba3b7b7294009ae55dd3e7407bf53
- OOBIX NFT (OOBX), v2 — PAUSED, do not use: 0x2aE2969ae37CB39abc45375598cEE530C181838A

## Facts

- Supply: 3,333 alien pets, tokenId 1 to 3,333. Minting is one pet per call. No per-wallet limit.
- v3 continues the same collection from token #501 (v2 minted #1–#500 and is paused). Always use the v3 contract above.
- The mint call is mint() with no arguments, calldata 0x1249c58b.
- Price: read currentPrice() on the v3 contract (selector 0x9d1b464a) and send exactly that value. The price is flat for every token on v3. The site shows no price; never state a price to the user beyond what the wallet preview itself shows.
- Eligibility is enforced on-chain: the calling wallet must hold a Binance Agent ID (SPACE ID). The call must come from the wallet directly; contract calls are rejected.
- Rarity is a draw: Common 2000, Uncommon 800, Rare 333, Epic 150, Legendary 50. A pet's seed is fixed at mint (tokenSeed, selector 0x5f516836) and its rarity is fixed at mint (tokenRarity, selector 0xafb0a369). Artwork and metadata are public in https://github.com/nugian10/OOBIX.

## Read first

- mintActive() on the v3 contract, selector 0x25fd90f3. If false, minting is not open. Stop and tell the user.
- totalSupply(), selector 0x18160ddd. If it returns 3333, the collection is sold out.
- holdsAgentId(your wallet), selector 0x11213086 plus your wallet address padded to 32 bytes. If false, the wallet cannot mint.

## Flow, per pet

1. Check mintActive() is true, totalSupply() is below 3,333, and holdsAgentId() is true.
2. Read currentPrice() and build the call: to the v3 contract, value exactly currentPrice(), calldata 0x1249c58b.
3. Preview:

   baw contract-call preview --binanceChainId 56 --from <agentic wallet> --to 0x666bf7475f5ba3b7b7294009ae55dd3e7407bf53 --value <currentPrice() in wei> --inputData 0x1249c58b --json

4. Show the preview to the user. On their confirmation, execute with the requestId from the preview.
5. Verify on-chain: the wallet now owns the new tokenId (read nextTokenId() before minting to know it in advance), and read tokenSeed(tokenId) and tokenRarity(tokenId) to report the pet's draw.

Repeat for more pets, one call each. There is no per-wallet limit.
