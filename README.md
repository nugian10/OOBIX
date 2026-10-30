# OOBIX — Alien Pet NFT Collection

OOBIX adalah koleksi 3.333 alien pet NFT bergaya kartun retro (Saturday Morning Cartoon 1990-an / awal 2000-an), ERC-721 di BNB Smart Chain (Chain ID 56). Tagline: **WEIRD LITTLE UNIVERSE.**

## Ringkas

- **Supply:** 3.333, token ID 1–3.333, sequential.
- **Harga on-chain:** #1–500 = 0,0003 BNB; #501–3.333 = 0 BNB (GRATIS). `currentPrice()` = harga token berikutnya.
- **Mint:** agent-only. `mint()` tanpa argumen, 1 token per panggilan. Pemint harus memegang SPACE ID .ai Agent ID NFT. Tanpa batas mint per wallet.
- **Gacha deck:** Common 2000 / Uncommon 800 / Rare 333 / Epic 150 / Legendary 50, di-commit on-chain (`deckHash` `0xb44bbbfc75bc6bfda8673ea71b6eef7a3389c78d0e30de7b7937c930acddc1a5`). Mint #n membuka slot deck #n.
- **Model:** WEDO (wedo.wtf) — dimodelkan dari skill file publiknya; source WEDO sendiri TIDAK terverifikasi di BscScan, jadi tidak ada source WEDO yang disalin.
- **Status:** kontrak SUDAH DI-DEPLOY 30 Okt 2026 21:05 WIB — `0x607840e0a3675cf2181c98453484eb785ddd2d83` (deploy tx `0x4abc4f232a3130c8f3b8b8cc1378872828d3d0227a145948bccb1aa099fe10f7`, blok 130678042, biaya 0,000282 BNB). Mint masih MATI (`mintActive` false), totalSupply 0. Verifikasi source di BscScan sedang diproses (GUID `zgwli1i7kedmqtj1ad3bu8tef4pwgjnf8cdw9bzxzmpcgre2dz`); belum diaudit independen. Owner/revenue DIKONFIRMASI 20:30 WIB 30 Okt (owner My Wallet, revenue Agentic Wallet); baseURI GitHub (repo `nugian10/OOBIX` sudah publik, artwork + metadata sudah di-push).

## File penting

| File | Isi |
|---|---|
| `contracts/OobixNFT.sol` | Kontrak (Solidity 0.8.24, OZ 5.4.0, runs 200, cancun) |
| `scripts/generate-deck.js` + `scripts/deck.json` | Generator deck deterministik + deck yang dipakai deploy |
| `scripts/deploy.js` | Deploy ke BSC testnet/mainnet (butuh `.env`) |
| `scripts/measure-deploy-gas.js` | Ukur gas deploy dengan deck asli |
| `test/OobixNFT.test.js` | 18 test Hardhat — semua lolos |
| `docs/SMART_CONTRACT.md` | Desain lengkap, deviasi dari WEDO, biaya deploy, peringatan |
| `docs/oobix-skill.md` | Instruksi mint untuk agen (model wedo-skill.md) |
| `abi/OobixNFT.abi.json` | ABI kontrak |

## Verifikasi

```bash
cd ~/workspace/projects/oobix
npx hardhat compile   # 0 error, 0 warning; runtime bytecode 9.130 byte
npx hardhat test      # 18 passing
```

Gas deploy terukur (deck asli): **5.419.052 gas** — 0,0002710 BNB pada 0,05 gwei (~Rp 3.500). Deploy-lah di 0,05 gwei.

## Yang masih butuh pemilik

1. ~~Konfirmasi owner + revenue~~ — SUDAH DIKONFIRMASI 20:30 WIB 30 Okt: owner My Wallet `0x0262e8e5E4584D8AB840fD950a6E2E0A414d4097`, revenue Binance Agentic Wallet `0x89c37649Ba3BAA9E1ce028612b7DE4e9c3a947B7`. Pembayaran mint langsung ke Agentic Wallet di dalam `mint()` (diputuskan 20:33 WIB).
2. ~~Konfirmasi simbol `OOBX`~~ — SUDAH DIKONFIRMASI 21:00 WIB 30 Okt: simbol `OOBX`.
3. baseURI: `https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/metadata/` — repo ini sudah publik dan koleksi sudah di-push.
4. ~~Keputusan deploy~~ — SUDAH DI-DEPLOY 30 Okt 2026 21:05 WIB, langsung mainnet (56): `0x607840e0a3675cf2181c98453484eb785ddd2d83`.
