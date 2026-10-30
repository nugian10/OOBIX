# OOBIX — Agent Mint Skill

Dokumen ini adalah instruksi untuk agen yang akan melakukan mint OOBIX. Modelnya WEDO (wedo.wtf) — baca dulu `docs/SMART_CONTRACT.md` untuk desain lengkapnya. **Jangan pernah minta seed phrase / private key / pairing code dari siapa pun.**

## Fakta proyek

| Item | Nilai |
|---|---|
| Nama | OOBIX — Alien Pet NFT Collection |
| Simbol | OOBX (asumsi — master prompt tidak memberi simbol; konfirmasi sebelum deploy) |
| Standar | ERC-721 |
| Chain | BNB Smart Chain, Chain ID 56 |
| Total supply | 3.333 |
| Kontrak | BELUM DI-DEPLOY — isi setelah deploy |
| Harga | #1–500: 0,0003 BNB per NFT; #501–3.333: 0 BNB (GRATIS) |
| Mint | `mint()`, tanpa argumen, 1 token per panggilan, selector `0x1249c58b` |
| Gate | Harus memegang SPACE ID .ai Agent ID NFT `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` |
| Deck | Common 2000 / Uncommon 800 / Rare 333 / Epic 150 / Legendary 50; deckHash `0xb44bbbfc75bc6bfda8673ea71b6eef7a3389c78d0e30de7b7937c930acddc1a5` |
| Batas per wallet | TIDAK ADA (deviasi dari WEDO yang membatasi 10) — wallet yang sama boleh mint berulang kali |
| Situs | Informasional saja, tanpa tombol mint publik |

## Prasyarat

1. Wallet yang dipakai mint **harus memegang Agent ID .ai** (SPACE ID). Cek dulu: `holdsAgentId(alamat)` harus `true`. Kalau `false`, mint akan revert `NoAgentId` — klaim Agent ID dulu di aplikasi Binance.
2. Wallet harus EOA (bukan kontrak) — panggilan dari kontrak ditolak (`NoContracts`).
3. Mint harus aktif (`mintOpen()` = `true`). Kalau `false`, mint revert `MintInactive`.
4. CLI `baw` terpasang dan login (Binance Agentic Wallet, Developer Mode ON) — sama seperti proyek Mythora/MythRealm sebelumnya.

## Prosedur: preview → konfirmasi → eksekusi

### 1. Preview (baca dulu, jangan kirim transaksi)

```bash
# Ganti <KONTRAK> dengan alamat kontrak OOBIX setelah deploy
baw call <KONTRAK> mintOpen
baw call <KONTRAK> currentPrice
baw call <KONTRAK> totalMinted
baw call <KONTRAK> holdsAgentId <ALAMAT_WALLET>
baw call <KONTRAK> nextTokenId
```

Catat: harga saat ini (`currentPrice()`), ID berikutnya (`nextTokenId()`), dan rarity slot itu (`rarityOf(nextTokenId)` — 0 Common, 1 Uncommon, 2 Rare, 3 Epic, 4 Legendary).

### 2. Konfirmasi

Tunjukkan ke pemilik sebelum eksekusi: alamat kontrak, token ID yang akan di-mint, rarity-nya, harga persis yang akan dikirim, dan alamat wallet pemint. **Jangan lanjut tanpa konfirmasi eksplisit.**

### 3. Eksekusi

- Kirim **persis** `currentPrice()` — tidak kurang, tidak lebih. Di fase gratis (#501 ke atas) kirim **persis 0 BNB**.
- Satu panggilan `mint()` = satu NFT. Untuk mint lagi, ulangi dari langkah preview (harga bisa berubah di batas tier — tapi di OOBIX, setelah #500 harga tetap 0).
- Setelah transaksi: baca event `Minted(minter, tokenId, price, rarity, seed)` dan cek `ownerOf(tokenId)` = wallet pemint.

## Aturan

- **1 token per panggilan `mint()`.** Tidak ada `mint(quantity)`.
- **Bayar persis `currentPrice()`.** Lebih bayar juga ditolak (`IncorrectPayment`).
- **Tidak ada batas per wallet** — tapi setiap mint tetap 1 token per transaksi.
- **Jangan pernah** memasukkan private key / seed phrase ke perintah apa pun. `baw` memakai wallet yang sudah ter-pairing.
- Kalau mint revert: baca pesannya — `MintInactive` (mint belum dibuka), `NoAgentId` (wallet tidak punya Agent ID), `NoContracts` (pemanggil kontrak), `IncorrectPayment` (nilai salah), `SoldOut` (3.333 sudah habis).
- Owner/revenue kontrak DIKONFIRMASI 20:30 WIB 30 Okt: owner = My Wallet `0x0262e8e5E4584D8AB840fD950a6E2E0A414d4097`, revenue = Binance Agentic Wallet `0x89c37649Ba3BAA9E1ce028612b7DE4e9c3a947B7`.

## Perbedaan dengan WEDO (jangan tertukar)

- WEDO: 6.666 supply, free + komisi, batas 10 per wallet, tier Common/Rare/Epic/Legendary/Mythic.
- OOBIX: 3.333 supply, #1–500 berbayar lalu GRATIS, **tanpa batas per wallet**, tier Common/Uncommon/Rare/Epic/Legendary.
- WEDO memakai `totalMinted()`, bukan `totalSupply()` (terverifikasi on-chain: `totalSupply()` revert di WEDO). OOBIX menyediakan keduanya.
- Source WEDO TIDAK terverifikasi di BscScan — mekanisme ini dimodelkan dari skill file publik, bukan disalin dari source.
