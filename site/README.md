# OOBIX — Website

Static site, no build step, no framework. Open `index.html` directly or
serve the project root:

```bash
cd ~/workspace/projects/oobix
python3 -m http.server 8123
# then open http://localhost:8123/site/
```

## Pages

| Page | Contents |
|---|---|
| `index.html` | Hero (mascot = preview 4), tagline, stats, featured aliens |
| `collection.html` | Full gallery, 48 per page, filters by rarity/species/search, token detail view (`?id=N`) |
| `mint.html` | Mint information (PLANNED pricing, labelled as planned, not live), agent steps, prompt for your agent |
| `about.html` | Concept, eight species, gacha deck / rarity counts |
| `faq.html` | Collection, blockchain, agent-only minting, supply, pricing, ownership, storage, audit |

## Honesty rules (do not break these)

- Contract is **not deployed**: `config.js` `CONTRACT_ADDRESS` is `""`.
  Every page shows "CONTRACT NOT DEPLOYED YET" and the footer says
  "Contract not deployed yet. No independent audit."
- Total minted on-chain is **0** everywhere. Mint numbers on the mint page
  are labelled **planned**, never presented as live chain data.
- No mint button, no Connect Wallet, no Simulate/Demo anywhere.
- X / Discord links are `href="#"` labelled "links not yet set".
- No BscScan link (there is no contract address to link to).

## Data

- Gallery reads the collection from the public GitHub repo at runtime
  (`https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/…`),
  so it works wherever the site is hosted, including Vercel with the
  `site/` folder as root. The repo does not exist yet — until it is
  created (public) and the collection pushed, the gallery shows the
  honest "not yet published" states.
- Hero mascot is a local copy of preview 4:
  `site/assets/mascot.webp` (previews 1–3 are also copied to
  `site/assets/` for reuse).

## Checks

```bash
# syntax
node --check site/app.js && node --check site/config.js
# serve + verify (from ~/workspace/projects/oobix)
python3 -m http.server 8123
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8123/site/index.html
# …repeat for every page, styles.css, config.js, app.js, and a sample
# of collection images; expect 200 everywhere, 0 404s.
```
