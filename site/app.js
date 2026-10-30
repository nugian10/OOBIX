/* OOBIX — shared site logic.
   Reads collection data at runtime. Nothing about supply, counts or
   artwork is hard-coded here beyond the known collection size (3,333)
   and the five rarities. If the collection files are not there yet,
   the site shows honest "not yet published" states.
   The v2 contract IS deployed (0x2aE2969ae37CB39abc45375598cEE530C181838A)
   and mint is NOT active yet — it opens when the owner activates it.
   Minted counts are read live from the chain (refreshLiveMint);
   static numbers are fallbacks only. v1 (0x607840e0a3675cf2181c98453484eb785ddd2d83)
   had 19 mints and stays live on-chain. */

(function () {
  "use strict";
  const CFG = window.OOBIX_CONFIG || {}; // || {} so a missing config degrades instead of killing the whole script
  const $ = (sel, el) => (el || document).querySelector(sel);
  const $$ = (sel, el) => Array.from((el || document).querySelectorAll(sel));

  const pad = (n) => String(n).padStart(4, "0");
  const esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);

  /* ---------- nav active state ---------- */
  const page = (location.pathname.split("/").pop() || "index.html").split("?")[0];
  $$(".nav-links a").forEach((a) => {
    const href = a.getAttribute("href");
    if (href === page || (page === "" && href === "index.html")) {
      a.classList.add("active");
    }
  });

  /* ---------- contract status line ---------- */
  $$(".js-contract-status").forEach((el) => {
    if (CFG.CONTRACT_ADDRESS) {
      el.innerHTML = '<span class="dot"></span><span>CONTRACT DEPLOYED — ' + esc(CFG.CONTRACT_ADDRESS) + "</span>";
    } else {
      el.innerHTML = '<span class="dot"></span><span>CONTRACT NOT DEPLOYED YET — MINTING OPENS AFTER DEPLOY</span>';
    }
  });
  $$(".js-contract-address").forEach((el) => {
    el.textContent = CFG.CONTRACT_ADDRESS || "Not deployed yet — no contract address exists.";
  });

  /* ---------- data loading ---------- */
  let collectionCache = null;
  let tokensCache = null;

  async function fetchJSON(url) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) return null;
      return await res.json();
    } catch (e) {
      return null;
    }
  }

  async function loadCollection() {
    if (collectionCache !== null) return collectionCache;
    collectionCache = await fetchJSON(CFG.COLLECTION_JSON);
    return collectionCache;
  }

  // Returns an array of token records for every token 1..TOTAL_SUPPLY.
  // Uses all-tokens.json when present; otherwise synthesises placeholder
  // slots so the collection still lists all 3,333 slots honestly.
  async function loadTokens() {
    if (tokensCache) return tokensCache;
    const data = await fetchJSON(CFG.ALL_TOKENS_JSON);
    const byId = {};
    if (Array.isArray(data)) {
      data.forEach((t) => { if (t && t.id != null) byId[Number(t.id)] = t; });
    }
    const tokens = [];
    for (let i = 1; i <= CFG.TOTAL_SUPPLY; i++) {
      const t = byId[i];
      tokens.push({
        id: i,
        species: t && t.species ? t.species : null,
        rarity: t && t.rarity ? t.rarity : null,
        bodyColor: t && t.bodyColor ? t.bodyColor : null,
        eyes: t && t.eyes != null ? t.eyes : null,
        expression: t && t.expression ? t.expression : null,
        antenna: t && t.antenna ? t.antenna : null,
        limbs: t && t.limbs ? t.limbs : null,
        background: t && t.background ? t.background : null,
        elements: t && t.elements != null ? t.elements : null,
        known: Boolean(t),
      });
    }
    tokensCache = tokens;
    return tokens;
  }

  /* ---------- home stats ---------- */
  async function initStats() {
    const host = $("#stats");
    if (!host) return;
    const col = await loadCollection();
    const tokens = await loadTokens();
    const known = tokens.filter((t) => t.known).length;
    const species = new Set(tokens.map((t) => t.species).filter(Boolean)).size;
    const total = (col && (col.totalSupply || col.total || col.maxSupply)) || CFG.TOTAL_SUPPLY;
    const set = (key, val) => {
      const el = host.querySelector('[data-stat="' + key + '"]');
      if (el) el.textContent = val;
    };
    set("total", Number(total).toLocaleString("en-US"));
    set("species", species > 0 ? String(species) : String(CFG.SPECIES.length));
    set("published", known > 0 ? Number(known).toLocaleString("en-US") : "—");
    set("supply", "0");
    const note = $("#stats-note");
    if (note) {
      note.textContent = known === 0
        ? "Collection artwork has not been published yet. Counts update here automatically once the collection files land."
        : known < CFG.TOTAL_SUPPLY
          ? known.toLocaleString("en-US") + " of " + CFG.TOTAL_SUPPLY.toLocaleString("en-US") + " artworks published so far. Mint is OPEN — loading live minted count from the chain…"
          : "All " + CFG.TOTAL_SUPPLY.toLocaleString("en-US") + " artworks published. Mint is OPEN — loading live minted count from the chain…";
    }
  }

  /* ---------- featured artworks (home) ---------- */
  function initFeatured() {
    const host = $("#featured");
    if (!host) return;
    const ids = [1, 2, 3, 4, 5, 6];
    loadTokens().then((tokens) => {
      const byId = {};
      tokens.forEach((t) => { byId[t.id] = t; });
      host.innerHTML = ids.map((id) => cardHTML(byId[id] || { id: id, known: false })).join("");
      bindArtFallbacks(host);
    });
  }

  /* ---------- card markup ---------- */
  function cardHTML(t) {
    const rar = t.rarity || "Unknown";
    const rarClass = t.rarity ? " rar-" + rar.replace(/[^A-Za-z]/g, "") : "";
    return (
      '<a class="card" href="collection.html?id=' + t.id + '">' +
        '<span class="art">' +
          '<img src="' + esc(CFG.IMAGE_PATH(t.id)) + '" alt="OOBIX #' + pad(t.id) + '" loading="lazy" data-token="' + t.id + '">' +
        "</span>" +
        '<span class="meta">' +
          '<span class="id">#' + pad(t.id) + "</span>" +
          '<span class="cls' + rarClass + '">' + esc(rar) + "</span>" +
        "</span>" +
      "</a>"
    );
  }

  function bindArtFallbacks(root) {
    $$("img[data-token]", root).forEach((img) => {
      img.addEventListener("error", () => {
        const art = img.closest(".art");
        if (art) {
          art.innerHTML = '<span class="pending">OOBIX<br>#' + pad(img.getAttribute("data-token")) + "<br>ARTWORK PENDING</span>";
        }
      }, { once: true });
      if (img.complete && img.naturalWidth === 0) {
        img.dispatchEvent(new Event("error"));
      }
    });
  }

  /* ---------- collection: paginated gallery + filters + detail ---------- */
  const PAGE_SIZE = 48;
  let collectionTokens = [];
  let collectionFiltered = [];
  let collectionPage = 1;

  function renderCollectionPage() {
    const host = $("#collection-grid");
    if (!host) return;
    const start = (collectionPage - 1) * PAGE_SIZE;
    const slice = collectionFiltered.slice(start, start + PAGE_SIZE);
    host.innerHTML = slice.map(cardHTML).join("");
    bindArtFallbacks(host);
    const totalPages = Math.max(1, Math.ceil(collectionFiltered.length / PAGE_SIZE));
    const count = $("#collection-count");
    if (count) {
      count.textContent = "PAGE " + collectionPage + " / " + totalPages + " — SHOWING " +
        (slice.length ? start + 1 : 0) + "–" + Math.min(start + PAGE_SIZE, collectionFiltered.length) +
        " OF " + collectionFiltered.length.toLocaleString("en-US");
    }
    const prev = $("#collection-prev"), next = $("#collection-next");
    if (prev) prev.disabled = collectionPage <= 1;
    if (next) next.disabled = collectionPage >= totalPages;
    if (prev) prev.style.opacity = collectionPage <= 1 ? 0.35 : 1;
    if (next) next.style.opacity = collectionPage >= totalPages ? 0.35 : 1;
  }

  function applyCollectionFilters() {
    const rar = ($("#filter-rarity") || {}).value || "";
    const sp = ($("#filter-species") || {}).value || "";
    const q = (($("#filter-search") || {}).value || "").trim();
    let list = collectionTokens;
    if (rar) list = list.filter((t) => t.rarity === rar);
    if (sp) list = list.filter((t) => t.species === sp);
    if (q) {
      const n = parseInt(q.replace(/^#/, ""), 10);
      if (!isNaN(n)) list = list.filter((t) => t.id === n);
      else list = list.filter((t) => ((t.species || "") + " " + (t.rarity || "")).toLowerCase().includes(q.toLowerCase()));
    }
    collectionFiltered = list;
    collectionPage = 1;
    renderCollectionPage();
  }

  function fillFilter(select, values, label) {
    if (!select) return;
    const opts = ['<option value="">' + label + "</option>"].concat(
      values.map((v) => '<option value="' + esc(v) + '">' + esc(v) + "</option>")
    );
    select.innerHTML = opts.join("");
  }

  function initCollection() {
    const host = $("#collection-grid");
    if (!host) return;
    const params = new URLSearchParams(location.search);
    const idParam = parseInt(params.get("id") || "", 10);
    if (!isNaN(idParam) && idParam >= 1 && idParam <= CFG.TOTAL_SUPPLY) {
      showDetail(idParam);
      return;
    }
    loadTokens().then((tokens) => {
      collectionTokens = tokens;
      collectionFiltered = tokens;
      const species = [...new Set(tokens.map((t) => t.species).filter(Boolean))].sort();
      fillFilter($("#filter-rarity"), CFG.RARITIES, "ALL RARITIES");
      fillFilter($("#filter-species"), species.length ? species : CFG.SPECIES, "ALL SPECIES");
      ["filter-rarity", "filter-species", "filter-search"].forEach((fid) => {
        const el = document.getElementById(fid);
        if (el) el.addEventListener("input", applyCollectionFilters);
      });
      renderCollectionPage();
      const prev = $("#collection-prev"), next = $("#collection-next");
      if (prev) prev.addEventListener("click", () => { if (collectionPage > 1) { collectionPage--; renderCollectionPage(); window.scrollTo({ top: 0, behavior: "smooth" }); } });
      if (next) next.addEventListener("click", () => {
        const totalPages = Math.ceil(collectionFiltered.length / PAGE_SIZE);
        if (collectionPage < totalPages) { collectionPage++; renderCollectionPage(); window.scrollTo({ top: 0, behavior: "smooth" }); }
      });
    });
  }

  /* ---------- token detail ---------- */
  async function showDetail(id) {
    const listView = $("#collection-list");
    const detailView = $("#token-detail");
    if (listView) listView.style.display = "none";
    if (!detailView) return;
    detailView.style.display = "block";
    const tokens = await loadTokens();
    const t = tokens.find((x) => x.id === id) || { id: id, known: false };
    const meta = await fetchJSON(CFG.METADATA_PATH(id));
    const title = $("#detail-title");
    if (title) title.textContent = "OOBIX #" + pad(id);
    const art = $("#detail-art");
    if (art) {
      art.innerHTML = '<img src="' + esc(CFG.IMAGE_PATH(id)) + '" alt="OOBIX #' + pad(id) + '" data-token="' + id + '">';
      bindArtFallbacks(art);
    }
    const rarEl = $("#detail-rarity");
    if (rarEl) rarEl.textContent = t.rarity || (meta && meta.attributes
      ? (meta.attributes.find((a) => a.trait_type === "Rarity") || {}).value || "Unknown"
      : "Unknown");
    const rows = [];
    rows.push(["Token ID", "#" + pad(id)]);
    rows.push(["Rarity", t.rarity || "Unknown"]);
    if (t.species) rows.push(["Species", t.species]);
    if (t.bodyColor) rows.push(["Body Color", t.bodyColor]);
    if (t.eyes != null) rows.push(["Eyes", String(t.eyes)]);
    if (t.expression) rows.push(["Expression", t.expression]);
    if (t.antenna) rows.push(["Antenna", t.antenna]);
    if (t.limbs) rows.push(["Limbs", t.limbs]);
    if (t.background) rows.push(["Background", t.background]);
    if (t.elements != null) rows.push(["Elements", String(t.elements)]);
    if (meta && Array.isArray(meta.attributes)) {
      meta.attributes.forEach((a) => {
        if (a && a.trait_type && !rows.some((r) => r[0] === a.trait_type)) {
          rows.push([a.trait_type, String(a.value)]);
        }
      });
    }
    if (meta && meta.name) rows.push(["Name", meta.name]);
    const minted = liveTotal != null && id <= liveTotal;
    rows.push(["Status", minted ? "Minted on-chain" : "Not minted yet — mint is OPEN"]);
    rows.push(["Total minted on-chain", liveTotal == null ? "Mint is OPEN — live count loads on the Mint page" : String(liveTotal) + " (live, on-chain)"]);
    const body = $("#detail-attrs");
    if (body) {
      body.innerHTML = rows.map((r) =>
        "<tr><td>" + esc(r[0]) + "</td><td>" + esc(r[1]) + "</td></tr>"
      ).join("");
    }
    const metaNote = $("#detail-meta-note");
    if (metaNote) {
      metaNote.textContent = meta
        ? "Metadata loaded from the collection."
        : "Metadata for this token has not been published yet. Attributes shown come from the collection index, if available.";
    }
    document.title = "OOBIX #" + pad(id) + " — OOBIX";
  }

  /* ---------- mint page: agent prompt ---------- */
  // The prompt's mint-state line is built from the live chain state:
  // buildPrompt() runs once at load (state unknown → "checking" line) and
  // again from refreshLiveMint() once mintActive() has been read, so the
  // prompt never claims OPEN while the contract says closed.
  function promptStateText() {
    if (liveActive === null) return "Mint status is read live from the contract — check the status banner on this page before minting.";
    if (liveActive) return "Mint is OPEN.";
    return "Mint is NOT active yet — do not mint until the owner activates it.";
  }
  function buildPrompt() {
    const pre = $("#agent-prompt");
    if (!pre) return;
    const addr = CFG.CONTRACT_ADDRESS;
    const addrLine = addr
      ? "The OOBIX contract address is " + addr + " on BNB Smart Chain Mainnet (chain 56)."
      : "The OOBIX contract is not deployed yet. Do not mint anything until the owner gives you the deployed contract address — if there is no deployed contract address, stop and say so.";
    pre.textContent =
      "Mint one OOBIX on BNB Smart Chain (chain id 56).\n" +
      addrLine + " " + promptStateText() + "\n" +
      "First check that my wallet holds a SPACE ID .ai Agent ID: call hasAgentId(my wallet address) on the OOBIX contract — it must return true, otherwise the mint will revert. The Agent ID registry is 0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F. There is no per-wallet mint limit.\n" +
      "Then read currentPrice() on the contract and call mint() with no arguments, sending exactly that value. Live pricing: tokens #1-500 cost 0.0003 BNB each, tokens #501-3333 cost 0.0008 BNB each. One token per mint() call. The payment goes directly to the revenue wallet in the same call; it never sits in the contract.\n" +
      "Show me the exact amount before I sign, and confirm the transaction on-chain once it is done: https://bscscan.com/address/" + addr;
  }
  function initMint() {
    buildPrompt();
    const btn = $("#copy-prompt");
    if (btn) {
      btn.addEventListener("click", () => {
        const text = pre.textContent;
        const done = (ok) => { btn.textContent = ok ? "COPIED" : "COPY FAILED — SELECT THE TEXT MANUALLY"; setTimeout(() => { btn.textContent = "COPY PROMPT"; }, 2500); };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(() => done(true)).catch(() => fallbackCopy(text, done));
        } else {
          fallbackCopy(text, done);
        }
      });
    }
  }
  function fallbackCopy(text, done) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "0";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    ta.setSelectionRange(0, text.length);
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    done(ok);
  }

  /* ---------- live on-chain mint state ---------- */
  // Reads totalSupply() + mintActive() straight from the chain with a plain
  // JSON-RPC call (no wallet, no library). Falls back silently to the static
  // numbers in the HTML when the RPC is unreachable.
  const RPC_URLS = ["https://bsc-dataseed.binance.org/", "https://bsc.publicnode.com"];
  let liveTotal = null;
  let liveActive = null;
  async function rpcCall(data) {
    for (const url of RPC_URLS) {
      try {
        const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "eth_call", params: [{ to: CFG.CONTRACT_ADDRESS, data: data }, "latest"] }) });
        const json = await res.json();
        if (json && json.result) return json.result;
      } catch (e) { /* try next RPC */ }
    }
    return null;
  }
  async function refreshLiveMint() {
    if (!CFG.CONTRACT_ADDRESS) return;
    const totalHex = await rpcCall("0x18160ddd"); // totalSupply()
    if (totalHex == null) return;
    liveTotal = parseInt(totalHex, 16);
    const activeHex = await rpcCall("0x25fd90f3"); // mintActive()
    liveActive = activeHex != null ? parseInt(activeHex, 16) === 1 : true;
    buildPrompt(); // refresh the prompt's mint-state line with the live state
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set("mint-total", String(liveTotal));
    set("mint-remaining", String(CFG.TOTAL_SUPPLY - liveTotal));
    const host = $("#stats");
    if (host) {
      const el = host.querySelector('[data-stat="supply"]');
      if (el) el.textContent = String(liveTotal);
    }
    const note = $("#stats-note");
    if (note) note.textContent = liveActive ? "Mint is OPEN. " + liveTotal + " minted on-chain so far." : "Mint is not active. " + liveTotal + " minted on-chain so far.";
    $$(".js-contract-status").forEach((el) => {
      el.innerHTML = '<span class="dot"></span><span>' + (liveActive ? "MINT IS OPEN — " + liveTotal + " MINTED SO FAR" : "CONTRACT DEPLOYED — MINT NOT ACTIVE") + " — " + esc(CFG.CONTRACT_ADDRESS) + "</span>";
    });
  }

  /* ---------- boot ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    initStats();
    initFeatured();
    initCollection();
    initMint();
    refreshLiveMint();
  });
})();
