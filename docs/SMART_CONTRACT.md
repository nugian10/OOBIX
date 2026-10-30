# OOBIX — Smart Contract

Kontrak: `contracts/OobixNFT.sol` — `OOBIX` / `OOBX`, ERC-721, Solidity 0.8.24, OpenZeppelin 5.4.0, optimizer runs 200, EVM Cancun. Compile bersih (0 error, 0 warning). Creation bytecode 10.894 byte, runtime bytecode 9.137 byte. ABI 97 entri di `abi/OobixNFT.abi.json`.

> **v2 (30 Okt 2026, 22:16 WIB):** redeploy disetujui pemilik — tier 2 berubah dari GRATIS (0 BNB) menjadi **0,0008 BNB**. v1 `0x607840e0a3675cf2181c98453484eb785ddd2d83` (19 mint, tier 2 GRATIS) tidak bisa diubah harganya — `setTierPrices` revert `PricesLocked` setelah mint pertama. **v2 DEPLOYED 30 Okt 2026 ~22:27 WIB di `0x2aE2969ae37CB39abc45375598cEE530C181838A`** (tx `0xe26f701815d0d646747ae86c36ad515f305e604c3e9e5459d1da38fac99d8bac`, blok 130688929, biaya 0,00032966 BNB), BscScan source-verified, mint BELUM aktif. Deck, alamat, dan semua aturan lain SAMA seperti v1.

## Model WEDO — yang diambil dari wedo.wtf

WEDO (`0x745d7a3b46E704e7A9D79AE1C3B049Da8f335D79`, 6.666 gacha Doer NFT, BNB Chain 56, free mint + komisi anti-bot kecil, Agent ID only, tanpa tombol mint di situs):

- `mint()` tanpa argumen, 1 token per panggilan, selector `0x1249c58b`.
- `currentPrice()` = harga token berikutnya; kirim persis nilai itu, tidak kurang tidak lebih.
- Gacha deck: deck slot tetap di-commit sebelum launch; mint #n membuka slot #n, rarity langsung terlihat di event. `deckHash()` = komitmen keccak256 atas seluruh deck.
- Agent-only on-chain lewat **SPACE ID .ai Agent ID NFT** (`0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`): mint hanya kalau `balanceOf(msg.sender) > 0`, kalau tidak revert `NoAgentId`.
- Panggilan dari kontrak ditolak (`NoContracts`); seed disimpan on-chain saat mint.
- Nama read-only: `mintOpen()`, `totalMinted()`, `holdsAgentId(address)`, `rarityOf(uint256)`, `deckHash()`.

**Verifikasi WEDO yang dilakukan 30 Okt 2026 (bsc-dataseed, blok 130672359):** kontrak WEDO ada, runtime code 7.487 byte, nama "WEDO", simbol "WEDO". **Source WEDO TIDAK terverifikasi di BscScan** (ContractName/SourceCode kosong) — jadi TIDAK ADA source WEDO yang disalin; mekanisme di atas dimodelkan dari `wedo-skill.md` publik + situs saja, plus implementasi XOVRATH v2 yang sudah terbukti untuk pola yang sama.

**Temuan penting dari verifikasi itu: `totalSupply()` (selector `0x18160ddd`) REVERT di kontrak WEDO.** WEDO memakai `totalMinted()`, BUKAN `totalSupply()` — kemungkinan WEDO bukan ERC721Enumerable. Itu bukan kegagalan OOBIX: OOBIX tetap menyediakan `totalSupply()` (desain sendiri, seperti XOVRATH) DI SAMPING `totalMinted()`. Jangan berasumsi WEDO punya `totalSupply()`.

**Yang TIDAK terverifikasi on-chain untuk WEDO:** `mintOpen`, `currentPrice`, `deckHash`, `holdsAgentId`, `rarityOf` — pembacaan itu tidak didapat dalam cek tersebut (skrip berhenti di revert `totalSupply()`; RPC lain rate-limited saat itu). Nilai-nilai itu dikutip dari skill file, bukan diklaim terverifikasi on-chain.

## Yang sudah diverifikasi (Hardhat, 18/18 test lolos, 14 detik)

- Nama/symbol, supply 3.333, tier, registry, harga, deckHash — semua sesuai.
- Selector terkonfirmasi: `mint()` `0x1249c58b`, `currentPrice()` `0x9d1b464a`, `rarityOf(uint256)` `0xdd3b5f9a`, `deckHash()` `0x8830dea2`, `mintOpen()` `0x24bbd049`, `totalMinted()` `0xa2309ff8`, `holdsAgentId(address)` `0x11213086`.
- Deck: jumlah tier persis di seluruh 3.333 slot; `rarityOf` cocok dengan deck generator untuk semua ID sampel; deck salah (panjang salah / jumlah tier salah) ditolak constructor dengan `InvalidDeck`.
- Harga (v2): #1–500 = 0,0003 BNB, #501–3.333 = 0,0008 BNB. Batas terbukti: setelah 500 mint, `currentPrice()` = 0,0008 BNB; #501 mint dengan value 0 ditolak (`IncorrectPayment`), dengan 0,0008 persis berhasil dan diteruskan ke revenue wallet. Kurang/lebih bayar juga ditolak.
- Tanpa Agent ID → `NoAgentId`; panggil dari kontrak → `NoContracts`; mint belum aktif → `MintInactive`.
- Tanpa batas mint per wallet: wallet yang sama mint berulang kali; `mintedBy` hanya counter transparansi.
- Cek Agent ID bisa dimatikan owner (escape hatch) lalu dinyalakan lagi; saat mati, siapa pun bisa mint; saat nyala lagi, yang tanpa Agent ID diblokir lagi.
- Registry asli SPACE ID di chain lokal: `holdsAgentId` false, mint revert `NoAgentId` (perilaku yang diharapkan — registry asli tidak ada code-nya di chain lokal).
- Harga tier: tier 2 boleh 0, tier 1 harus > 0; harga bisa diubah owner HANYA sebelum mint pertama — `setTierPrices` revert `PricesLocked` setelah mint pertama. Inilah yang membuat v1 tidak bisa diubah harganya (16 mint sudah terjadi) dan harus di-redeploy sebagai v2. Batas 500 adalah konstanta.
- **Pembayaran langsung ke Agentic Wallet (diputuskan Nugraha 20:33 WIB 30 Okt):** setiap mint berbayar meneruskan `msg.value` LANGSUNG ke `revenueWallet` di dalam panggilan `mint()` yang sama — tidak masuk kontrak dulu, tidak perlu `withdraw()`. Saldo kontrak tetap 0 setelah mint; `withdraw()` hanya safety valve untuk dana yang masuk di luar `mint()`, dan dalam operasi normal revert `NoFunds`. Kalau pengiriman gagal, seluruh mint revert (`PaymentForwardFailed`) — tidak ada token yang ter-mint tanpa pembayaran sampai. Cara yang sama sudah terbukti di Mythora: 6 mint masuk langsung ke Agentic Wallet yang sama, saldo kontrak 0.
- `withdraw()` hanya owner; dalam operasi normal saldo 0 jadi revert `NoFunds`; non-owner ditolak.
- Supply cap TERBUKTI PENUH (bukan shortcut): seluruh 3.333 token di-mint dalam test, lalu `currentPrice()` dan `mint()` revert `SoldOut`, `totalSupply()` = 3.333, `nextTokenId()` = 3.334.
- `tokenURI` = baseURI + tokenId + ".json"; token yang belum ada revert `ERC721NonexistentToken`.

## Deck gacha

- Generator: `scripts/generate-deck.js` (deterministic, seed `OOBIX-DECK-SEED-2026-10-30-v1`, mulberry32 + Fisher-Yates). Output: `scripts/deck.json`.
- Jumlah tier (jumlah total 3.333): Common 2000, Uncommon 800, Rare 333, Epic 150, Legendary 50.
- Kode tier OOBIX: 0 Common, 1 Uncommon, 2 Rare, 3 Epic, 4 Legendary. **Berbeda dari WEDO** (0 Common, 1 Rare, 2 Epic, 3 Legendary, 4 Mythic) — jangan tertukar.
- `deckHash`: `0xb44bbbfc75bc6bfda8673ea71b6eef7a3389c78d0e30de7b7937c930acddc1a5` — cocok antara generator dan on-chain (diuji di `scripts/measure-deploy-gas.js`).
- Deck disimpan PENUH on-chain (3.333 byte, 1 byte per token). Constructor memverifikasi jumlah tier-nya, jadi deck yang salah tidak bisa ter-deploy.
- Mint #n membuka slot deck #n; rarity disimpan di `tokenRarity[tokenId]` dan di-emit di event `Minted(minter, tokenId, price, rarity, seed)`.

## Biaya deploy (diukur Hardhat, deck asli 3.333 byte)

- **Gas deploy (v2): 5.440.531 gas.** Deck-lah yang mendominasi: menyimpan 3.333 byte + validasi jumlah tier di constructor. Ini PRAKTIS di BSC (limit gas blok ~140 juta), tapi HARGA GAS menentukan biaya:
  - 0,05 gwei (minimum jaringan, dipakai deploy Mythora/MythRealm/MINTFORM): **0,0002720 BNB (~Rp 3.500** pada Rp 12,75 jt/BNB).
  - 1 gwei: 0,00544 BNB (~Rp 69.000).
  - 3 gwei: 0,0163 BNB (~Rp 207.000).
- **Deploy-lah di 0,05 gwei seperti proyek sebelumnya.** Kalau gas naik, biaya naik sebanding — tidak ada fallback yang diimplementasikan, karena deck penuh terbukti bisa di-deploy dengan angka di atas. (Fallback yang dipertimbangkan dan TIDAK dipakai: hanya simpan deckHash + undian sisa-jumlah — itu akan menghilangkan verifikasi deck on-chain.)

## Tiga deviasi kunci dari WEDO

1. **Supply 3.333, bukan 6.666.**
2. **Harga (v2): #1–500 = 0,0003 BNB, #501–3.333 = 0,0008 BNB.** WEDO: free mint + komisi anti-bot kecil. OOBIX v1 punya fase gratis (tier 2 = 0 BNB), tapi v2 menghapusnya — kedua tier berbayar. v1 tidak bisa diubah harganya (terkunci setelah mint pertama), jadi v2 adalah redeploy dengan deck dan aturan yang sama.
3. **TIDAK ADA batas mint per wallet.** WEDO membatasi 10 mint berbayar per wallet (`paidMintedBy`). OOBIX menghapusnya atas preferensi Nugraha yang sudah berdiri ("Jangan kasih batasan untuk mint perwallet", Mythora + XOVRATH). Satu wallet ber-Agent ID BISA memborong sebagian besar supply — itu trade-off yang diterima.

Deviasi lain: 5 tier rarity OOBIX (Common/Uncommon/Rare/Epic/Legendary) vs 5 tier WEDO (Common/Rare/Epic/Legendary/Mythic); deck OOBIX disimpan penuh on-chain; `totalSupply()` disediakan OOBIX (WEDO tidak punya).

## Alamat — parameter constructor, TIDAK di-hardcode (kecuali registry publik)

- Owner: **DIKONFIRMASI Nugraha 20:30 WIB 30 Okt** — My Wallet `0x0262e8e5E4584D8AB840fD950a6E2E0A414d4097` (sama seperti Mythora/MythRealm/MINTFORM). Owner memegang semua fungsi owner (setBaseURI, setMintActive, setRevenueWallet, withdraw, dll).
- Revenue: **DIKONFIRMASI Nugraha 20:30 WIB 30 Okt** — Binance Agentic Wallet `0x89c37649Ba3BAA9E1ce028612b7DE4e9c3a947B7`. **Pembayaran mint LANGSUNG ke sini** — setiap mint berbayar meneruskan `msg.value` langsung ke Agentic Wallet di dalam `mint()` yang sama, tidak masuk kontrak dulu (diputuskan Nugraha 20:33 WIB 30 Okt). Bukan pola XOVRATH (owner = Agentic) yang ditolak untuk OOBIX.
- Alternatif XOVRATH (owner = revenue = Agentic Wallet) DITOLAK untuk OOBIX — owner tetap My Wallet.
- Agent ID registry: SPACE ID .ai NFT `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` (bisa diubah owner kalau SPACE ID migrasi; cek bisa dimatikan owner via `setAgentIdCheckRequired(false)` — kalau dimatikan, mint jadi permissionless on-chain).
- baseURI: **Penyimpanan GitHub (diputuskan Nugraha 20:25 WIB 30 Okt, BUKAN IPFS)** — `https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/metadata/` (repo publik `nugian10/OOBIX`, branch main — repo SUDAH ADA dan koleksi sudah di-push 20:47 WIB 30 Okt, raw URLs terverifikasi 200). Harus diakhiri `/`.

## Fungsi (ringkas)

| Fungsi | Keterangan |
|---|---|
| `mint()` `0x1249c58b` | 1 token, tanpa argumen, bayar persis `currentPrice()` |
| `currentPrice()` / `getMintPrice()` | Harga token berikutnya (0 di fase gratis) |
| `priceForTokenId(id)` | Harga satu token ID |
| `mintOpen()` | `mintActive` |
| `totalSupply()` / `totalMinted()` | Jumlah sudah di-mint |
| `nextTokenId()` | ID berikutnya |
| `holdsAgentId(addr)` / `hasAgentId(addr)` | Punya Agent ID? |
| `rarityOf(id)` | Tier deck slot token ID (0–4) |
| `deckHash()` | Komitmen keccak256 deck |
| `tokenSeed(id)` / `tokenRarity(id)` / `mintedBy(addr)` | Data per token / per wallet |
| `setMintActive`, `setBaseURI`, `setRevenueWallet`, `setAgentIdRegistry`, `setAgentIdCheckRequired`, `setTierPrices` (sebelum mint pertama) | Owner only |
| `withdraw()` | Owner only, safety valve: hanya dana yang masuk di luar `mint()` → revenueWallet (operasi normal: saldo 0, revert `NoFunds`) |

## Peringatan jujur (baca sebelum deploy)

1. Kontrak ini BELUM diaudit independen. Setelah deploy, verifikasi source di BscScan, tapi tetap tulis "belum diaudit" di situs.
2. Deck bersifat publik (harus begitu supaya komitmennya bisa dicek) — siapa pun bisa menghitung seluruh deck dari seed sebelum mint. Rarity transparan, bukan rahasia.
3. Deck TIDAK menggambar artwork (tidak seperti klaim gacha penuh): artwork OOBIX digenerate per token ID; deck hanya menentukan tier rarity token #n. Seed adalah sidik jari on-chain dari mint itu.
4. Mint HANYA untuk wallet yang memegang Agent ID .ai. Pembeli WAJIB klaim Agent ID dulu di aplikasi Binance, kalau tidak mint mereka revert `NoAgentId`.
5. Deploy mainnet (Chain ID 56) pakai BNB sungguhan dan tidak bisa dibatalkan. Deploy di gas 0,05 gwei.
6. Simbol `OOBX` adalah asumsi — master prompt tidak memberi simbol. Mudah diubah sebelum deploy (satu baris di constructor); konfirmasi sebelum deploy.

## Deploy

```bash
cd ~/workspace/projects/oobix
node scripts/generate-deck.js   # JANGAN regenerate kalau deck sudah final — deckHash akan berubah
cp .env.example .env            # isi OWNER_ADDRESS, REVENUE_WALLET, BASE_URI (registry sudah default)
npx hardhat test                # 18 test, harus lolos semua
npx hardhat run scripts/deploy.js --network bscTestnet   # latihan dulu
npx hardhat run scripts/deploy.js --network bsc          # MAINNET, BNB asli
```

Setelah deploy: verifikasi source di BscScan (flattened / standard-JSON, solc 0.8.24, optimizer runs 200, EVM cancun, MIT, constructor args = owner, revenueWallet, agentIdRegistry, baseURI, deck bytes — deck-nya 3.333 byte, jadi constructor args-nya panjang), `setBaseURI` ke folder metadata, `setMintActive(true)` HANYA saat launch. Mint tetap OFF setelah deploy.
