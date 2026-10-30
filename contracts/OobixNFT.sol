// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

// ============================================================
// OOBIX — Alien Pet NFT Collection
// ERC-721, BNB Smart Chain Mainnet (Chain ID 56)
// ------------------------------------------------------------
// MODELLED ON WEDO (wedo.wtf, public skill file + site,
// 30 Okt 2026 — NOT copied from source: WEDO's source was
// not verified on BscScan at check time, so the mechanism
// below is modelled from the public wedo-skill.md facts and
// the site, plus the proven XOVRATH v2 implementation of
// the same pattern):
//
// FROM WEDO:
// - mint() takes NO arguments and mints exactly 1 token.
//   Selector 0x1249c58b == keccak("mint()")[:4].
// - Gacha deck: a fixed deck of slots is committed before
//   launch. Mint #n opens deck slot #n, rarity is revealed
//   instantly in the Minted event. deckHash() is the
//   keccak256 commitment of the whole deck.
// - currentPrice() returns the price of the NEXT token.
//   The agent reads it and sends exactly that value —
//   no more, no less.
// - Agent-only enforced ON-CHAIN by a SPACE ID Agent ID
//   check: the minter must hold a SPACE ID .ai Agent ID
//   NFT (registry 0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F,
//   the public registry also used by Nomio / AnthroBit /
//   Spoxy). hasAgentId uses a low-level staticcall on
//   purpose: a high-level balanceOf call to an address
//   with no code returns empty data, and the ABI decoder
//   reverts on empty returndata OUTSIDE try/catch.
// - Calls from contracts are rejected (NoContracts).
// - The mint seed is stored on-chain at mint.
// - mintOpen() / totalMinted() / holdsAgentId() /
//   rarityOf() / deckHash() are the read-only names an
//   agent / site uses (WEDO-compatible where they fit).
//   VERIFIED 30 Okt 2026 (bsc-dataseed, block
//   130672359): WEDO contract
//   0x745d7a3b46E704e7A9D79AE1C3B049Da8f335D79 has
//   7,487 bytes of runtime code, name "WEDO", symbol
//   "WEDO", and its BscScan source is NOT verified
//   (empty ContractName/SourceCode) — so NO WEDO
//   source was copied; the mechanism is modelled
//   from the public wedo-skill.md only. The same
//   check found totalSupply() (0x18160ddd) REVERTS
//   on WEDO: WEDO exposes totalMinted(), NOT
//   totalSupply(). OOBIX still provides totalSupply()
//   (its own design, like XOVRATH) alongside
//   totalMinted() — do not assume WEDO has it.
//   The other WEDO reads (mintOpen, currentPrice,
//   deckHash, holdsAgentId, rarityOf) were NOT
//   obtained on-chain in that check (script aborted
//   on the totalSupply revert; the other RPC was
//   rate-limited) — they are cited from the skill
//   file, not presented as on-chain verified.
//
// KEPT FROM THE OOBIX MASTER PROMPT (wins over WEDO
// where they conflict):
// - Supply 3,333 (WEDO: 6,666). Token IDs 1–3,333
//   sequential.
// - Tiered pricing, computed ON-CHAIN per token ID:
//     Token IDs   1–500 : 0.0003 BNB each
//     Token IDs 501–3333: 0.0008 BNB each
//   (WEDO: free mint + a small anti-bot commission.
//   OOBIX v2: both tiers are paid — the v1 free phase
//   for #501+ is gone. v1 (0x6078...2d83) had tier 2
//   FREE, but its prices locked at the first mint.)
//   currentPrice() is the price of the next ID, so
//   the 500 boundary is crossed automatically.
//   Payment must equal currentPrice() exactly.
//   Under- and overpayment are both rejected.
// - Tier prices changeable by the owner ONLY before
//   the first mint (setTierPrices reverts once
//   totalSupply > 0). The 500 boundary is a constant
//   and can never move. Tier 1 must stay > 0; tier 2
//   MAY be 0 (a free phase is allowed before the first
//   mint, but v2 ships with 0.0008 BNB).
// - Rarity tiers (5, different from WEDO's 5):
//     0 Common, 1 Uncommon, 2 Rare, 3 Epic, 4 Legendary
//   (WEDO: 0 Common, 1 Rare, 2 Epic, 3 Legendary,
//   4 Mythic — do not mix the two mappings up.)
//   Exact deck counts: Common 2000, Uncommon 800,
//   Rare 333, Epic 150, Legendary 50 = 3,333.
// - No public mint button and no direct public mint
//   function on the site — the website is informational
//   only; only an authorized mint agent calls mint().
//   The owner can authorize / revoke agent access by
//   the Agent ID check (setAgentIdRegistry /
//   setAgentIdCheckRequired).
//
// DEVIATION FROM WEDO — NO PER-WALLET LIMIT:
//   WEDO caps paid mints at 10 per wallet
//   (paidMintedBy). OOBIX does NOT. This is the
//   user's standing preference (Mythora: all mint
//   limits removed 29 Okt 2026; XOVRATH: the
//   one-per-wallet rule removed 30 Okt 2026,
//   "Jangan kasih batasan untuk mint perwallet").
//   mintedBy is kept as a public counter for
//   transparency only — it is never enforced.
//   Consequence, accepted by the user: one wallet
//   holding an Agent ID CAN buy up a large share
//   of the supply, one token per mint() call.
//
// THE DECK — design + honest limits:
//   The deck is generated OFF-CHAIN by a deterministic
//   seeded shuffle (scripts/generate-deck.js, seed
//   "OOBIX-DECK-SEED-2026-10-30-v1", mulberry32 +
//   Fisher-Yates) and passed to the constructor as
//   3,333 bytes (1 byte per token, tier code 0–4).
//   It is stored ON-CHAIN in full (_deck) and the
//   constructor verifies the exact tier counts, so a
//   wrong deck cannot be deployed by accident.
//   deckHash() = keccak256(_deck) — anyone can
//   re-run the generator and check the commitment.
//   Mint #n draws deck slot #n; rarityOf(tokenId)
//   returns that slot's tier; tokenRarity[tokenId]
//   is stored at mint and emitted in Minted.
//   HONEST LIMITS: (1) the deck is a rarity
//   assignment, not artwork generation — like
//   XOVRATH, OOBIX artwork is pre-generated per
//   token ID; the deck does not draw the artwork,
//   it only decides which rarity tier token #n is.
//   (2) The deck is fixed at deploy and cannot be
//   reshuffled afterwards. (3) The seed is public
//   (it has to be, for the commitment to be
//   verifiable), so anyone can compute the whole
//   deck in advance — rarity is transparent, not
//   secret. That is the WEDO gacha trade-off, kept
//   deliberately.
//   Deployment cost of the full deck is measured in
//   the docs (Hardhat, with the real 3,333-byte
//   deck) — see docs/SMART_CONTRACT.md.
//
// OWNER / REVENUE — constructor parameters, NOT
// hard-coded (except the public Agent ID registry
// default). CONFIRMED by Nugraha 20:30 WIB 30 Okt 2026:
// owner = My Wallet 0x0262e8e5E4584D8AB840fD950a6E2E0A414d4097,
// revenue = Binance Agentic Wallet
// 0x89c37649Ba3BAA9E1ce028612b7DE4e9c3a947B7.
// Funds: each PAID mint forwards msg.value DIRECTLY to
// the revenue (Agentic) wallet inside the same mint()
// call — decided by Nugraha 20:33 WIB 30 Okt 2026:
// "Tidak usah masuk ke kontrak dulu langsung saja ke
// agentic wallet". Mint payments NEVER sit in this
// contract, and no withdraw step is needed for them.
// withdraw() exists only as a safety valve for funds
// that arrive outside mint() (e.g. force-sent ETH).
// Precedent: the Mythora contract forwards the same
// way to the same Agentic Wallet and 6 mints landed
// there exactly, contract balance 0.
//
// ESCAPE HATCH (documented, on-chain, visible):
//   agentIdCheckRequired defaults to true. The owner
//   can turn the Agent ID check off
//   (setAgentIdCheckRequired(false)) or point it at
//   a different registry (setAgentIdRegistry).
//   Turning it off makes minting permissionless
//   on-chain and agent-only in the UI only (the
//   Mythora pattern). Do not hide such a change.
//
// This contract is SOURCE-VERIFIABLE on BscScan.
// It is NOT an independent audit — keep that
// disclosure on the site.
// ============================================================

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract OobixNFT is ERC721, Ownable, ReentrancyGuard {
    using Strings for uint256;

    uint256 public constant MAX_SUPPLY = 3333;
    uint256 public constant TIER_1_END = 500;

    // Rarity tier codes (OOBIX mapping — see header).
    uint8 public constant RARITY_COMMON = 0;
    uint8 public constant RARITY_UNCOMMON = 1;
    uint8 public constant RARITY_RARE = 2;
    uint8 public constant RARITY_EPIC = 3;
    uint8 public constant RARITY_LEGENDARY = 4;

    // Exact deck counts — enforced by the constructor.
    uint256 public constant COUNT_COMMON = 2000;
    uint256 public constant COUNT_UNCOMMON = 800;
    uint256 public constant COUNT_RARE = 333;
    uint256 public constant COUNT_EPIC = 150;
    uint256 public constant COUNT_LEGENDARY = 50;

    uint256 public constant DEFAULT_PRICE_TIER_1 = 0.0003 ether;
    uint256 public constant DEFAULT_PRICE_TIER_2 = 0.0008 ether;

    /// @notice SPACE ID .ai Agent ID NFT on BNB Smart Chain.
    /// Public registry used by WEDO / Nomio / AnthroBit / Spoxy.
    address public constant DEFAULT_AGENT_ID_REGISTRY =
        0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F;

    uint256 public priceTier1 = DEFAULT_PRICE_TIER_1;
    uint256 public priceTier2 = DEFAULT_PRICE_TIER_2;

    bool public mintActive;
    address public revenueWallet;
    address public agentIdRegistry;
    bool public agentIdCheckRequired = true;

    string private _baseTokenURI;
    uint256 private _nextTokenId = 1;

    /// @dev The full gacha deck, 1 byte per token (tier 0–4),
    /// stored on-chain. deckHash() commits to it.
    bytes private _deck;

    /// @dev On-chain mint seed per token.
    mapping(uint256 => bytes32) public tokenSeed;
    /// @dev Rarity tier per minted token (deck slot value).
    mapping(uint256 => uint8) public tokenRarity;
    /// @dev Mints per wallet — transparency only, NEVER enforced.
    mapping(address => uint256) public mintedBy;

    event Minted(address indexed minter, uint256 indexed tokenId, uint256 price, uint8 rarity, bytes32 seed);
    event DeckCommitted(bytes32 indexed deckHash);
    event MintActiveChanged(bool active);
    event BaseURIUpdated(string baseURI);
    event RevenueWalletUpdated(address indexed revenueWallet);
    event AgentIdRegistryUpdated(address indexed agentIdRegistry);
    event AgentIdCheckChanged(bool required);
    event TierPricesUpdated(uint256 priceTier1, uint256 priceTier2);
    event Withdrawn(address indexed revenueWallet, uint256 amount);

    error MintInactive();
    error ExceedsMaxSupply();
    error SoldOut();
    error IncorrectPayment(uint256 expected, uint256 received);
    error InvalidAddress();
    error InvalidDeck();
    error NoFunds();
    error NoAgentId();
    error NoContracts();
    error PricesLocked();
    error InvalidPrice();
    error PaymentForwardFailed();

    constructor(
        address initialOwner,
        address revenueWallet_,
        address agentIdRegistry_,
        string memory baseURI_,
        bytes memory deck_
    ) ERC721("OOBIX", "OOBX") Ownable(initialOwner) {
        if (initialOwner == address(0) || revenueWallet_ == address(0) || agentIdRegistry_ == address(0)) {
            revert InvalidAddress();
        }
        if (deck_.length != MAX_SUPPLY) revert InvalidDeck();
        // Verify the exact tier counts on-chain, so a wrong
        // deck cannot be deployed by accident.
        uint256 c0;
        uint256 c1;
        uint256 c2;
        uint256 c3;
        uint256 c4;
        for (uint256 i = 0; i < MAX_SUPPLY; i++) {
            uint8 tier = uint8(deck_[i]);
            if (tier == 0) c0++;
            else if (tier == 1) c1++;
            else if (tier == 2) c2++;
            else if (tier == 3) c3++;
            else if (tier == 4) c4++;
            else revert InvalidDeck();
        }
        if (
            c0 != COUNT_COMMON || c1 != COUNT_UNCOMMON || c2 != COUNT_RARE || c3 != COUNT_EPIC ||
            c4 != COUNT_LEGENDARY
        ) revert InvalidDeck();

        revenueWallet = revenueWallet_;
        agentIdRegistry = agentIdRegistry_;
        _baseTokenURI = baseURI_;
        _deck = deck_;
        emit DeckCommitted(keccak256(deck_));
    }

    // ---------- supply / pricing (read-only, for UI + agents) ----------

    function totalSupply() public view returns (uint256) {
        return _nextTokenId - 1;
    }

    /// @notice WEDO-compatible alias of totalSupply().
    function totalMinted() public view returns (uint256) {
        return totalSupply();
    }

    function nextTokenId() public view returns (uint256) {
        return _nextTokenId;
    }

    /// @notice True when minting is open (mintActive).
    function mintOpen() public view returns (bool) {
        return mintActive;
    }

    /// @notice Price of a single token ID. Reverts outside 1..MAX_SUPPLY.
    function priceForTokenId(uint256 tokenId) public view returns (uint256) {
        if (tokenId == 0 || tokenId > MAX_SUPPLY) revert ExceedsMaxSupply();
        if (tokenId <= TIER_1_END) return priceTier1;
        return priceTier2;
    }

    /// @notice Price of the next NFT to be minted. Reverts when sold out.
    /// The agent reads this and sends exactly this value with mint().
    function currentPrice() public view returns (uint256) {
        if (_nextTokenId > MAX_SUPPLY) revert SoldOut();
        return priceForTokenId(_nextTokenId);
    }

    /// @notice Alias of currentPrice().
    function getMintPrice() public view returns (uint256) {
        return currentPrice();
    }

    /// @notice keccak256 commitment of the full on-chain deck.
    function deckHash() public view returns (bytes32) {
        return keccak256(_deck);
    }

    /// @notice Rarity tier of a token ID (its deck slot), 0 Common,
    /// 1 Uncommon, 2 Rare, 3 Epic, 4 Legendary. Works before the
    /// token is minted — the deck is public by design.
    function rarityOf(uint256 tokenId) public view returns (uint8) {
        if (tokenId == 0 || tokenId > MAX_SUPPLY) revert ExceedsMaxSupply();
        return uint8(_deck[tokenId - 1]);
    }

    /// @notice True when `wallet` holds at least one SPACE ID
    /// .ai Agent ID NFT in the configured registry. A registry
    /// that does not answer like an ERC-721 returns false
    /// instead of reverting, so a bad registry address can
    /// never brick reads — it only blocks minting.
    /// Implemented with a low-level staticcall on purpose: a
    /// high-level balanceOf call to an address with no code
    /// returns empty data, and the ABI decoder reverts on
    /// empty returndata OUTSIDE try/catch. The low-level call
    /// returns ok=false / short data instead, which we map
    /// to false here.
    function holdsAgentId(address wallet) public view returns (bool) {
        if (agentIdRegistry == address(0)) return false;
        (bool ok, bytes memory data) = agentIdRegistry.staticcall(
            abi.encodeWithSelector(IERC721.balanceOf.selector, wallet)
        );
        if (!ok || data.length < 32) return false;
        return abi.decode(data, (uint256)) > 0;
    }

    /// @notice Alias of holdsAgentId() (XOVRATH name).
    function hasAgentId(address wallet) public view returns (bool) {
        return holdsAgentId(wallet);
    }

    // ---------- minting (WEDO model, OOBIX rules) ----------

    /// @notice Mint exactly ONE OOBIX to msg.sender.
    /// No arguments — the token ID is the next sequential one
    /// and opens deck slot #tokenId. Requires, in order:
    /// mint active; caller is not a contract; caller holds
    /// an Agent ID (unless the check is disabled); supply
    /// remains; msg.value equals currentPrice() exactly.
    /// No per-wallet limit: the same
    /// wallet may call mint() again for another token.
    /// Stores the mint seed and the deck rarity.
    /// PAYMENT FLOW: a paid mint forwards msg.value
    /// DIRECTLY to the revenue wallet in this same call —
    /// it never sits in this contract (Nugraha, 20:33 WIB
    /// 30 Okt 2026). If the forward fails, the whole mint
    /// reverts, so no token is ever minted without payment
    /// landing. A mint with price 0 forwards nothing.
    function mint() external payable nonReentrant {
        if (!mintActive) revert MintInactive();
        if (msg.sender.code.length > 0) revert NoContracts();
        if (agentIdCheckRequired && !holdsAgentId(msg.sender)) revert NoAgentId();

        uint256 tokenId = _nextTokenId;
        if (tokenId > MAX_SUPPLY) revert SoldOut();
        uint256 price = priceForTokenId(tokenId);
        if (msg.value != price) revert IncorrectPayment(price, msg.value);

        uint8 rarity = uint8(_deck[tokenId - 1]);
        _nextTokenId++;
        bytes32 seed = keccak256(
            abi.encodePacked(blockhash(block.number - 1), msg.sender, tokenId)
        );
        tokenSeed[tokenId] = seed;
        tokenRarity[tokenId] = rarity;
        mintedBy[msg.sender]++;
        _safeMint(msg.sender, tokenId);
        emit Minted(msg.sender, tokenId, price, rarity, seed);

        if (price > 0) {
            (bool ok, ) = revenueWallet.call{value: price}("");
            if (!ok) revert PaymentForwardFailed();
        }
    }

    // ---------- metadata ----------

    function baseURI() public view returns (string memory) {
        return _baseTokenURI;
    }

    /// @notice tokenURI = baseURI + tokenId + ".json".
    /// The base URI must therefore end with "/" and point at
    /// the folder holding those files, e.g. ipfs://<CID>/
    /// or a GitHub raw folder URL.
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        if (_ownerOf(tokenId) == address(0)) revert ERC721NonexistentToken(tokenId);
        return string.concat(_baseTokenURI, tokenId.toString(), ".json");
    }

    // ---------- owner-only administration ----------

    function setMintActive(bool active) external onlyOwner {
        mintActive = active;
        emit MintActiveChanged(active);
    }

    function setBaseURI(string calldata baseURI_) external onlyOwner {
        _baseTokenURI = baseURI_;
        emit BaseURIUpdated(baseURI_);
    }

    function setRevenueWallet(address revenueWallet_) external onlyOwner {
        if (revenueWallet_ == address(0)) revert InvalidAddress();
        revenueWallet = revenueWallet_;
        emit RevenueWalletUpdated(revenueWallet_);
    }

    /// @notice Point the Agent ID check at a different registry
    /// (e.g. if SPACE ID migrates the .ai NFT contract).
    function setAgentIdRegistry(address agentIdRegistry_) external onlyOwner {
        if (agentIdRegistry_ == address(0)) revert InvalidAddress();
        agentIdRegistry = agentIdRegistry_;
        emit AgentIdRegistryUpdated(agentIdRegistry_);
    }

    /// @notice Turn the on-chain Agent ID check on/off.
    /// Turning it OFF makes minting permissionless on-chain and
    /// agent-only in the UI only (the Mythora pattern). The
    /// change is public on-chain via this event — do not hide it.
    function setAgentIdCheckRequired(bool required) external onlyOwner {
        agentIdCheckRequired = required;
        emit AgentIdCheckChanged(required);
    }

    /// @notice Change tier prices — ONLY before the first mint.
    /// The 500 boundary itself is a constant and cannot move.
    /// Tier 1 must stay > 0; tier 2 MAY be 0 (a free phase is
    /// allowed, but v2 ships with 0.0008 BNB).
    function setTierPrices(uint256 priceTier1_, uint256 priceTier2_) external onlyOwner {
        if (totalSupply() > 0) revert PricesLocked();
        if (priceTier1_ == 0) revert InvalidPrice();
        priceTier1 = priceTier1_;
        priceTier2 = priceTier2_;
        emit TierPricesUpdated(priceTier1_, priceTier2_);
    }

    /// @notice Safety valve only: send any balance that
    /// arrived OUTSIDE mint() (e.g. force-sent ETH) to the
    /// revenue wallet. Owner-only. Mint payments are
    /// forwarded directly by mint() and never accumulate
    /// here, so in normal operation this reverts NoFunds.
    function withdraw() external onlyOwner nonReentrant {
        uint256 amount = address(this).balance;
        if (amount == 0) revert NoFunds();
        (bool ok, ) = revenueWallet.call{value: amount}("");
        if (!ok) revert("Withdraw failed");
        emit Withdrawn(revenueWallet, amount);
    }
}
