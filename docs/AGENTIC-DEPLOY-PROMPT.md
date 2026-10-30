# OOBIX v2 — Prompt deploy untuk Agen Binance (Agentic Wallet)

> ⚠️ INI DEPLOY v2 (REDEPLOY) — BUKAN deploy pertama.
> Kontrak v1 sudah live sejak 30 Okt 2026 21:05 WIB:
> alamat `0x607840e0a3675cf2181c98453484eb785ddd2d83`,
> tx deploy `0x4abc4f232a3130c8f3b8b8cc1378872828d3d0227a145948bccb1aa099fe10f7`,
> BscScan source-verified, mint AKTIF sejak 21:25 WIB, 16 token sudah di-mint.
> v1 TIDAK BISA diubah harganya (`setTierPrices` revert `PricesLocked` setelah
> mint pertama) — karena itu pemilik menyetujui redeploy sebagai v2.
> Satu-satunya beda v2: harga #501–3.333 menjadi **0,0008 BNB** (v1 GRATIS).
> Deck, alamat, dan semua aturan lain SAMA seperti v1.
> Deploy v2 **SEKALI SAJA** ke Mainnet. v1 tetap live dengan 16 token-nya;
> jangan deploy v1 lagi, jangan deploy v2 dua kali.

## Tugas

Deploy kontrak OobixNFT **v2** ke **BNB Smart Chain MAINNET (chainId 56) saja**.
Jangan testnet. Jangan deploy dua kali.

## Sumber kode

Repo publik: https://github.com/nugian10/OOBIX (branch main).
Kontrak: `contracts/OobixNFT.sol` (OOBIX / OOBX, Solidity 0.8.24, OpenZeppelin 5.4.0).
Deck: `scripts/deck.json` — JANGAN regenerate deck; pakai file ini apa adanya.
Script deploy: `scripts/deploy.js` — jalankan `npx hardhat run scripts/deploy.js --network bsc`.
Sebelum deploy, jalankan `npx hardhat test` — semua 18 test harus lolos.

## Argumen constructor (urutan ini, jangan diubah)

1. `initialOwner` (owner kontrak): `0x0262e8e5E4584D8AB840fD950a6E2E0A414d4097` — My Wallet Nugraha.
   Owner BUKAN Agentic Wallet untuk OOBIX (ini keputusan Nugraha 20:30 WIB 30 Okt 2026).
2. `revenueWallet_` (penerima hasil mint): `0x89c37649Ba3BAA9E1ce028612b7DE4e9c3a947B7` — Binance Agentic Wallet.
   Pembayaran mint diteruskan LANGSUNG ke alamat ini di dalam `mint()` (tidak masuk kontrak dulu).
3. `agentIdRegistry_`: `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` — SPACE ID .ai Agent ID NFT.
4. `baseURI_`: `https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/metadata/`
5. `deck_`: isi `scripts/deck.json` (3.333 byte; deckHash `0xb44bbbfc75bc6bfda8673ea71b6eef7a3389c78d0e30de7b7937c930acddc1a5`,
   counts Common 2000 / Uncommon 800 / Rare 333 / Epic 150 / Legendary 50).

## Gas

Deploy di **0,05 gwei**. Biaya deploy v2 terukur: 5.440.531 gas = **~0,0002720 BNB**
(~Rp 3.500). Wallet deployer (Agentic Wallet) harus punya minimal ~0,001 BNB.
Jangan deploy di atas 1 gwei tanpa konfirmasi pemilik.

## Setelah deploy — cek dan laporkan

Baca balik dari kontrak dan laporkan semuanya:
- alamat kontrak + tx hash deploy + link BscScan
- `owner()` = `0x0262...` (My Wallet)
- `revenueWallet()` = `0x89c3...` (Agentic Wallet)
- `agentIdRegistry()` = `0x60B9...`
- `baseURI()` = URL GitHub di atas
- `totalSupply()` = 0, `mintActive()` = false, `currentPrice()` = 0,0003 BNB
- `MAX_SUPPLY` = 3333, `deckHash()` = `0xb44b...`
- `hasAgentId(0x89c3...)` = true

**Mint TETAP MATI setelah deploy** (`mintActive` false). Jangan nyalakan mint.
Jangan panggil `setMintActive(true)` — itu hanya saat launch, oleh owner.

## Kalau gagal login / koneksi agen

Koneksi agen Binance ini pernah gagal di langkah pertama pada 29 Okt 2026
("Pertama juga sudah tidak bisa"), penyebab tidak diketahui. Kalau login gagal
lagi, perbaikannya adalah pairing ulang / login ulang di aplikasi Binance —
bukan mengubah kontrak. Jangan ubah alamat, deck, atau harga apa pun untuk
"memperbaiki" koneksi.

## Yang TIDAK boleh

- Jangan minta seed phrase, private key, atau pairing code ke siapa pun.
- Jangan deploy ke testnet, jangan deploy dua kali, jangan ubah harga
  (#1–500: 0,0003 BNB, #501–3.333: 0,0008 BNB) atau deck.
- Jangan deploy ulang v1 — v1 sudah live dan harganya terkunci.
- Kontrak ini source-nya BELUM diaudit independen — jangan klaim sudah diaudit.
