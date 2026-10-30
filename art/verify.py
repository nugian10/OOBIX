#!/usr/bin/env python3
"""Verify the OOBIX collection. Exit non-zero on any failure."""
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "collection")
IMG_DIR = os.path.join(OUT, "images")
META_DIR = os.path.join(OUT, "metadata")
DECK_PATH = os.path.join(BASE, "scripts", "deck.json")
IMAGE_BASE = "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/images/"
TOTAL = 3333
fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


deck = json.load(open(DECK_PATH))
TIER_NAMES = {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Epic", 4: "Legendary"}
EXPECTED_RARITY = {"Common": 2000, "Uncommon": 800, "Rare": 333,
                   "Epic": 150, "Legendary": 50}
SPECIES = {"Round Blob", "Tall Thin", "Long Neck", "Spiky",
           "Quadruped", "Floating Jelly", "Wide Flat", "One-Eye Orb"}
BODY_COLORS = {"Blue", "Purple", "Pink", "Yellow", "Green", "Orange",
               "Teal", "Cream"}
BACKGROUNDS = {"Pink", "Purple", "Yellow", "Blue", "Green", "Cream", "Black"}
EYE_SHAPES = {"Round", "Oval", "Sleepy", "Star"}
EXPRESSIONS = {"Happy", "Surprised", "Grinning", "Sleepy",
               "Mischievous", "Angry", "In Love"}
ANTENNAS = {"None", "Two Ball Antennae", "Three Antenna Eyes",
            "Horns", "Spikes", "Single Stalk"}
LIMBS = {"Two Arms", "Two Arms + Two Legs", "Four Legs", "Wings", "None",
         "Four Legs + Wings", "Tentacles"}

imgs = sorted(os.listdir(IMG_DIR), key=lambda s: int(s[:-4]))
metas = sorted(os.listdir(META_DIR), key=lambda s: int(s[:-5]))
check(len(imgs) == TOTAL, "images count == 3333 (got %d)" % len(imgs))
check(len(metas) == TOTAL, "metadata count == 3333 (got %d)" % len(metas))
check(imgs == ["%d.svg" % i for i in range(1, TOTAL + 1)],
      "image filenames 1..3333.svg")
check(metas == ["%d.json" % i for i in range(1, TOTAL + 1)],
      "metadata filenames 1..3333.json")

hashes, tokens = set(), []
max_size = 0
for i in range(1, TOTAL + 1):
    path = os.path.join(IMG_DIR, "%d.svg" % i)
    data = open(path, "rb").read()
    max_size = max(max_size, len(data))
    hashes.add(hashlib.sha256(data).hexdigest())
    try:
        ET.fromstring(data)
    except ET.ParseError as e:
        fails.append("SVG %d not valid XML: %s" % (i, e))
    if b'viewBox="0 0 900 1125"' not in data:
        fails.append("SVG %d missing viewBox 0 0 900 1125" % i)
    if b"<text" in data:
        fails.append("SVG %d contains <text>" % i)
    if b"Gradient" in data or b"gradient" in data:
        fails.append("SVG %d contains a gradient" % i)
    if b"ipfs://" in data:
        fails.append("SVG %d contains ipfs://" % i)
    m = json.load(open(os.path.join(META_DIR, "%d.json" % i)))
    if m["name"] != "OOBIX — Alien #%04d" % i:
        fails.append("metadata %d bad name: %r" % (i, m.get("name")))
    if m["image"] != IMAGE_BASE + "%d.svg" % i:
        fails.append("metadata %d bad image field: %r" % (i, m.get("image")))
    if "OOBIX" not in m.get("description", "") or "3,333" not in m.get("description", ""):
        fails.append("metadata %d bad description" % i)
    attrs = {a["trait_type"]: a["value"] for a in m["attributes"]}
    for key in ("Species", "Rarity", "Body Color", "Eyes", "Expression",
                "Antenna", "Limbs", "Background"):
        if key not in attrs:
            fails.append("metadata %d missing attribute %s" % (i, key))
    if attrs.get("Species") not in SPECIES:
        fails.append("metadata %d bad Species: %r" % (i, attrs.get("Species")))
    expected_rarity = TIER_NAMES[deck["deck"][i - 1]]
    if attrs.get("Rarity") != expected_rarity:
        fails.append("metadata %d rarity %r != deck %r"
                     % (i, attrs.get("Rarity"), expected_rarity))
    if attrs.get("Body Color") not in BODY_COLORS:
        fails.append("metadata %d bad Body Color: %r" % (i, attrs.get("Body Color")))
    eyes = attrs.get("Eyes", "")
    m_eyes = re.fullmatch(r"([123]) (Round|Oval|Sleepy|Star)", eyes)
    if not m_eyes:
        fails.append("metadata %d bad Eyes: %r" % (i, eyes))
    elif attrs.get("Species") == "One-Eye Orb" and m_eyes.group(1) != "1":
        fails.append("metadata %d One-Eye Orb must have 1 eye" % i)
    if attrs.get("Expression") not in EXPRESSIONS:
        fails.append("metadata %d bad Expression: %r" % (i, attrs.get("Expression")))
    if attrs.get("Antenna") not in ANTENNAS:
        fails.append("metadata %d bad Antenna: %r" % (i, attrs.get("Antenna")))
    if attrs.get("Limbs") not in LIMBS:
        fails.append("metadata %d bad Limbs: %r" % (i, attrs.get("Limbs")))
    if attrs.get("Species") == "Floating Jelly" and attrs.get("Limbs") != "Tentacles":
        fails.append("metadata %d Floating Jelly must have Limbs Tentacles" % i)
    if attrs.get("Species") == "Quadruped" and attrs.get("Limbs") not in (
            "Four Legs", "Four Legs + Wings"):
        fails.append("metadata %d Quadruped must have Limbs Four Legs[ + Wings]" % i)
    if attrs.get("Background") not in BACKGROUNDS:
        fails.append("metadata %d bad Background: %r" % (i, attrs.get("Background")))
    tokens.append({"id": i, "species": attrs["Species"],
                   "rarity": attrs["Rarity"],
                   "bodyColor": attrs["Body Color"], "eyes": eyes,
                   "expression": attrs["Expression"],
                   "antenna": attrs["Antenna"], "limbs": attrs["Limbs"],
                   "background": attrs["Background"],
                   "elements": None,
                   "sha256": hashlib.sha256(data).hexdigest()})

check(len(hashes) == TOTAL,
      "3333 distinct SVG SHA-256 hashes (got %d)" % len(hashes))
check(max_size < 30 * 1024,
      "largest SVG under 30 KB (%d bytes)" % max_size)

rarity_counts = dict(Counter(t["rarity"] for t in tokens))
check(rarity_counts == EXPECTED_RARITY,
      "rarity counts match deck.json exactly %s" % rarity_counts)

coll = json.load(open(os.path.join(OUT, "collection.json")))
alltok = json.load(open(os.path.join(OUT, "all-tokens.json")))
check(coll["total"] == TOTAL, "collection.json total == 3333")
check(coll["rarities"] == EXPECTED_RARITY,
      "collection.json rarities match deck")
check(coll["deckHash"] == deck["deckHash"], "collection.json deckHash matches deck.json")
check(coll["seed"] == deck["seed"], "collection.json seed matches deck.json")
check(coll["contract"] == {"status": "not deployed", "address": ""},
      "contract status not deployed, address empty")
check(coll["imageBase"] == IMAGE_BASE, "collection.json imageBase is GitHub raw URL")
for key, field in (("species", "species"), ("backgrounds", "background"),
                   ("bodyColors", "bodyColor")):
    got = dict(Counter(t[field] for t in tokens))
    check(coll[key] == got,
          "collection.json %s matches metadata (%s)" % (key, got))
    check(sum(got.values()) == TOTAL, "%s sums to 3333" % key)
check([t["id"] for t in alltok] == list(range(1, TOTAL + 1)),
      "all-tokens.json ids 1..3333 sorted")
for a, t in zip(alltok, tokens):
    for k in ("species", "rarity", "bodyColor", "eyes", "expression",
              "antenna", "limbs", "background", "sha256"):
        if a[k] != t[k]:
            fails.append("all-tokens.json token %d field %s mismatch" % (t["id"], k))
    if not isinstance(a["elements"], int) or not (10 <= a["elements"] <= 120):
        fails.append("all-tokens.json token %d elements out of range: %r"
                     % (t["id"], a.get("elements")))

# no IPFS placeholder anywhere in the collection
hits = []
for root, _, files in os.walk(OUT):
    for fn in files:
        p = os.path.join(root, fn)
        data = open(p, "rb").read()
        if b"ipfs://" in data:
            hits.append(p)
check(not hits, "no ipfs:// placeholder anywhere in collection/ (hits: %s)" % hits)

print("XML/metadata parse failures: %d" % len(fails))
if fails:
    for f_ in fails[:20]:
        print("  FAIL:", f_)
    sys.exit(1)
print("ALL CHECKS PASSED")
