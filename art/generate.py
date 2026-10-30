#!/usr/bin/env python3
"""
OOBIX — Alien Pet NFT. Generative artwork + metadata collection.
3,333 retro Saturday Morning Cartoon alien pets (#1-3333), BNB Chain (56).

SEED SCHEME (the only source of randomness):
  Every token is generated from its token id alone, plus one fixed
  collection salt. No wall-clock, no environment, no external input.
    SALT = 0x4F4F4249  ("OOBI" in ASCII, fixed constant)
    seed(token_id) = ((token_id * 2654435761) ^ SALT) & 0xFFFFFFFF
    rng = mulberry32(seed)  -- same deterministic PRNG as XOVRATH.
  Rarity is NOT random: it comes from scripts/deck.json per token id
  (Common 2000 / Uncommon 800 / Rare 333 / Epic 150 / Legendary 50,
  deckHash 0xb44bbbfc75bc6bfda8673ea71b6eef7a3389c78d0e30de7b7937c930acddc1a5).
  All other traits are drawn from that token's own rng stream, in a
  fixed order, so re-running regenerates byte-identical files.

USAGE:
    python3 art/generate.py
  Regenerates collection/images/<id>.svg, collection/metadata/<id>.json,
  collection/collection.json and collection/all-tokens.json in place.
  Local only: no deploy, no upload, no pin, no network, no spend.

    python3 art/generate.py --only 1,2,3 --out /tmp/preview
  Preview mode: render only the listed token ids as SVGs into --out,
  without touching the collection.

STYLE: retro 1990s/early-2000s Saturday Morning Cartoon. Bold clean
black outlines (#141414, width 5-8), flat fills, simple cel shading
(one darker flat shape on one side), bright contrasting colours,
exaggerated expressions, strange alien anatomy, a different species
per character. NO gradients, NO <text> in artwork, NO 3D.
Storage is GitHub (chosen 30 Okt 2026), NOT IPFS: image fields point
at https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/images/<id>.svg
"""
import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter

SALT = 0x4F4F4249
TOTAL = 3333
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "collection")
IMG_DIR = os.path.join(OUT, "images")
META_DIR = os.path.join(OUT, "metadata")
DECK_PATH = os.path.join(BASE, "scripts", "deck.json")
IMAGE_BASE = "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/images/"
META_BASE = "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/metadata/"

INK = "#141414"
SPECIES = ["Round Blob", "Tall Thin", "Long Neck", "Spiky",
           "Quadruped", "Floating Jelly", "Wide Flat", "One-Eye Orb"]
# body colour: (hex, darker cel-shade, lighter belly/highlight)
BODY_COLORS = {
    "Blue":   ("#3B6FD4", "#2A4FA0", "#7AA8FF"),
    "Purple": ("#7B4FBF", "#5A3794", "#A98AE0"),
    "Pink":   ("#FF7AA8", "#E85A8C", "#FFB3C7"),
    "Yellow": ("#FFD23F", "#E0AC1A", "#FFE27A"),
    "Green":  ("#3DBB7A", "#2A8F5C", "#7AD6A8"),
    "Orange": ("#FF7A2F", "#D95A14", "#FFA866"),
    "Teal":   ("#2AB8A6", "#1E8A7C", "#6ED6C8"),
    "Cream":  ("#FFF3D6", "#E8D5A8", "#FFFBEF"),
}
# background: (hex, lighter flat, darker flat/ground)
BACKGROUNDS = {
    "Pink":   ("#FFB3C7", "#FFD6E2", "#E88AA8"),
    "Purple": ("#8A6BCF", "#B39DDE", "#6B4FA8"),
    "Yellow": ("#FFD23F", "#FFE27A", "#D9A91F"),
    "Blue":   ("#7AA8FF", "#A9C4FF", "#5B84D6"),
    "Green":  ("#8FD6A0", "#B8E6C4", "#6BB87E"),
    "Cream":  ("#FFF3D6", "#FFFBEF", "#E8D5A8"),
    "Black":  ("#141414", "#3A3A3A", "#000000"),
}
EYE_SHAPES = ["Round", "Oval", "Sleepy", "Star"]
EXPRESSIONS = ["Happy", "Surprised", "Grinning", "Sleepy",
               "Mischievous", "Angry", "In Love"]
ANTENNAS = ["None", "Two Ball Antennae", "Three Antenna Eyes",
            "Horns", "Spikes", "Single Stalk"]
LIMBS = ["Two Arms", "Two Arms + Two Legs", "Four Legs", "Wings", "None"]
TIER_NAMES = {0: "Common", 1: "Uncommon", 2: "Rare", 3: "Epic", 4: "Legendary"}

DESCRIPTION = (
    "OOBIX — Alien Pet #%04d. One of 3,333 retro cartoon alien pets "
    "on BNB Smart Chain. Bold outlines, flat colours, big feelings, "
    "weird little universe. Agent-only mint. WEIRD LITTLE UNIVERSE."
)


# ---------------------------------------------------------------- PRNG ----
def mulberry32(seed):
    a = seed & 0xFFFFFFFF

    def rand():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (t | 61))) & 0xFFFFFFFF
        return (((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0)

    return rand


def seed_for(token_id):
    return ((token_id * 2654435761) ^ SALT) & 0xFFFFFFFF


def load_deck():
    with open(DECK_PATH) as fh:
        deck = json.load(fh)
    assert len(deck["deck"]) == TOTAL, "deck length != 3333"
    return deck


# ------------------------------------------------------------- helpers ----
def f(v):
    s = "%.1f" % v
    return s[:-2] if s.endswith(".0") else s


def pick(rng, items):
    return items[int(rng() * len(items))]


def star_path(cx, cy, r):
    """4-point sparkle star centred at (cx, cy)."""
    return ("M %s %s L %s %s L %s %s L %s %s L %s %s L %s %s L %s %s L %s %s Z"
            % (f(cx), f(cy - r), f(cx + r * 0.3), f(cy - r * 0.3),
               f(cx + r), f(cy), f(cx + r * 0.3), f(cy + r * 0.3),
               f(cx), f(cy + r), f(cx - r * 0.3), f(cy + r * 0.3),
               f(cx - r), f(cy), f(cx - r * 0.3), f(cy - r * 0.3)))


def heart_path(cx, cy, s):
    return ("M %s %s C %s %s %s %s %s %s C %s %s %s %s %s %s C %s %s %s %s %s %s Z"
            % (f(cx), f(cy + s * 0.9),
               f(cx - s * 1.3), f(cy - s * 0.2), f(cx - s * 0.7), f(cy - s * 1.1), f(cx), f(cy - s * 0.3),
               f(cx + s * 0.7), f(cy - s * 1.1), f(cx + s * 1.3), f(cy - s * 0.2), f(cx), f(cy + s * 0.9),
               f(cx), f(cy + s * 0.9), f(cx), f(cy + s * 0.9), f(cx), f(cy + s * 0.9)))


def arm_path(x1, y1, x2, y2, colour):
    """A cartoon arm: thick black under-stroke + colour over-stroke,
    round caps, drawn as two paths so the outline reads cleanly."""
    return ('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" '
            'stroke-width="30" stroke-linecap="round"/>'
            '<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" '
            'stroke-width="20" stroke-linecap="round"/>'
            % (f(x1), f(y1), f((x1 + x2) / 2), f((y1 + y2) / 2 + 18),
               f(x2), f(y2), INK,
               f(x1), f(y1), f((x1 + x2) / 2), f((y1 + y2) / 2 + 18),
               f(x2), f(y2), colour))


def hand(cx, cy, colour):
    """Mitten hand: one big circle + two small finger bumps."""
    return ('<circle cx="%s" cy="%s" r="26" fill="%s" stroke="%s" stroke-width="6"/>'
            '<circle cx="%s" cy="%s" r="11" fill="%s" stroke="%s" stroke-width="5"/>'
            '<circle cx="%s" cy="%s" r="11" fill="%s" stroke="%s" stroke-width="5"/>'
            % (f(cx), f(cy), colour, INK,
               f(cx - 18), f(cy - 16), colour, INK,
               f(cx + 16), f(cy - 18), colour, INK))


def leg(x, y_top, y_bot, colour):
    return ('<path d="M %s %s L %s %s" stroke="%s" stroke-width="34" stroke-linecap="round"/>'
            '<path d="M %s %s L %s %s" stroke="%s" stroke-width="24" stroke-linecap="round"/>'
            '<ellipse cx="%s" cy="%s" rx="34" ry="16" fill="%s" stroke="%s" stroke-width="6"/>'
            % (f(x), f(y_top), f(x), f(y_bot), INK,
               f(x), f(y_top), f(x), f(y_bot), colour,
               f(x + 8), f(y_bot + 6), colour, INK))


# ------------------------------------------------------------ background ----
def draw_background(rng, els, bg_name):
    """Flat background: base colour + ground + one flat scenery set."""
    base, light, dark = BACKGROUNDS[bg_name]
    n = 0
    els.append('<rect width="900" height="1125" fill="%s"/>' % base)
    n += 1
    kind = pick(rng, ["Ground", "Hills", "Stars", "Planet"])
    if kind == "Ground":
        els.append('<rect x="0" y="880" width="900" height="245" fill="%s"/>' % dark)
        n += 1
        for _ in range(4):
            rx = 60 + rng() * 780
            els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>'
                       % (f(rx), f(920 + rng() * 160), f(26 + rng() * 42),
                          f(14 + rng() * 16), light))
            n += 1
    elif kind == "Hills":
        els.append('<path d="M 0 880 Q 220 %s 450 880 Q 680 %s 900 880 L 900 1125 L 0 1125 Z" fill="%s"/>'
                   % (f(700 + rng() * 80), f(720 + rng() * 80), dark))
        n += 1
        els.append('<path d="M 0 950 Q 300 %s 620 950 Q 780 %s 900 950 L 900 1125 L 0 1125 Z" fill="%s"/>'
                   % (f(820 + rng() * 60), f(840 + rng() * 60), light))
        n += 1
        for _ in range(3):
            els.append('<path d="%s" fill="%s"/>'
                       % (star_path(120 + rng() * 660, 140 + rng() * 220,
                                    14 + rng() * 16), light))
            n += 1
    elif kind == "Stars":
        for _ in range(9):
            els.append('<path d="%s" fill="%s"/>'
                       % (star_path(60 + rng() * 780, 60 + rng() * 420,
                                    10 + rng() * 18), light))
            n += 1
        els.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>'
                   % (f(680 + rng() * 80), f(150 + rng() * 80),
                      f(52 + rng() * 22), light))
        n += 1
        els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="none" stroke="%s" stroke-width="6"/>'
                   % (f(700 + rng() * 60), f(170 + rng() * 60),
                      f(96 + rng() * 20), f(26 + rng() * 8), dark))
        n += 1
        els.append('<rect x="0" y="920" width="900" height="205" fill="%s"/>' % dark)
        n += 1
    else:  # Planet
        els.append('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="6"/>'
                   % (f(660 + rng() * 60), f(190 + rng() * 60),
                      f(120 + rng() * 30), light, INK))
        n += 1
        els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="none" stroke="%s" stroke-width="7" transform="rotate(-18 %s %s)"/>'
                   % (f(690), f(200), f(190), f(42), INK, f(690), f(200)))
        n += 1
        for _ in range(4):
            els.append('<path d="%s" fill="%s"/>'
                       % (star_path(80 + rng() * 500, 90 + rng() * 300,
                                    10 + rng() * 14), light))
            n += 1
        els.append('<rect x="0" y="900" width="900" height="225" fill="%s"/>' % dark)
        n += 1
    # soft ground shadow under the alien (flat, dark, low opacity)
    els.append('<ellipse cx="450" cy="968" rx="265" ry="34" fill="#000000" opacity="0.16"/>')
    return n + 1

# ------------------------------------------------------------ face parts ----
def draw_eye(els, cx, cy, r, shape, rng):
    """One cartoon eye. Returns 1 element-group count (approx 3 shapes)."""
    n = 0
    if shape == "Sleepy":
        els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>'
                   % (f(cx - r * 0.9), f(cy), f(cx), f(cy + r * 0.75),
                      f(cx + r * 0.9), f(cy), INK))
        els.append('<path d="M %s %s l -8 12 M %s %s l 0 14 M %s %s l 8 12" fill="none" stroke="%s" stroke-width="4" stroke-linecap="round"/>'
                   % (f(cx - r * 0.45), f(cy + r * 0.35), f(cx), f(cy + r * 0.45),
                      f(cx + r * 0.45), f(cy + r * 0.35), INK))
        return 2
    if shape == "Star":
        els.append('<path d="%s" fill="#FFFFFF" stroke="%s" stroke-width="5" stroke-linejoin="round"/>'
                   % (star_path(cx, cy, r * 1.15), INK))
        els.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>'
                   % (f(cx), f(cy), f(r * 0.42), INK))
        els.append('<circle cx="%s" cy="%s" r="%s" fill="#FFFFFF"/>'
                   % (f(cx - r * 0.16), f(cy - r * 0.16), f(r * 0.14)))
        return 3
    if shape == "Oval":
        els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#FFFFFF" stroke="%s" stroke-width="6"/>'
                   % (f(cx), f(cy), f(r * 0.72), f(r * 1.12), INK))
        px = cx + (rng() - 0.5) * r * 0.3
        py = cy + (rng() - 0.5) * r * 0.3
        els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>'
                   % (f(px), f(py), f(r * 0.36), f(r * 0.55), INK))
        els.append('<circle cx="%s" cy="%s" r="%s" fill="#FFFFFF"/>'
                   % (f(px - r * 0.12), f(py - r * 0.2), f(r * 0.14)))
        return 3
    # Round (default)
    els.append('<circle cx="%s" cy="%s" r="%s" fill="#FFFFFF" stroke="%s" stroke-width="6"/>'
               % (f(cx), f(cy), f(r), INK))
    px = cx + (rng() - 0.5) * r * 0.35
    py = cy + (rng() - 0.5) * r * 0.35
    els.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>'
               % (f(px), f(py), f(r * 0.52), INK))
    els.append('<circle cx="%s" cy="%s" r="%s" fill="#FFFFFF"/>'
               % (f(px - r * 0.2), f(py - r * 0.2), f(r * 0.16)))
    return 3


def draw_face(els, traits, fx, fy, spread, er, mx, my, rng):
    """Eyes + brows + mouth + blush for a face centred at (fx, fy),
    mouth at (mx, my). Returns element count."""
    n = 0
    count = traits["eye_count"]
    shape = traits["eye_shape"]
    expr = traits["expression"]
    if count == 1:
        n += draw_eye(els, fx, fy, er * 1.45, shape, rng)
        eye_xs = [fx]
    elif count == 2:
        for sx in (fx - spread, fx + spread):
            n += draw_eye(els, sx, fy, er, shape, rng)
        eye_xs = [fx - spread, fx + spread]
    else:
        for sx, sy in ((fx - spread, fy - er * 0.35), (fx, fy + er * 0.55),
                       (fx + spread, fy - er * 0.35)):
            n += draw_eye(els, sx, sy, er * 0.8, shape, rng)
        eye_xs = [fx - spread, fx, fx + spread]
    # brows for Angry / Mischievous / Surprised
    if expr == "Angry":
        for ex in eye_xs:
            els.append('<path d="M %s %s L %s %s" stroke="%s" stroke-width="8" stroke-linecap="round"/>'
                       % (f(ex - er * 0.7), f(fy - er * 1.5), f(ex + er * 0.7), f(fy - er * 1.05), INK))
            n += 1
    elif expr == "Mischievous":
        els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>'
                   % (f(eye_xs[0] - er * 0.6), f(fy - er * 1.45),
                      f(eye_xs[0]), f(fy - er * 1.85), f(eye_xs[0] + er * 0.6), f(fy - er * 1.45), INK))
        n += 1
    elif expr == "Surprised":
        for ex in eye_xs:
            els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round"/>'
                       % (f(ex - er * 0.6), f(fy - er * 1.5), f(ex), f(fy - er * 1.8),
                          f(ex + er * 0.6), f(fy - er * 1.5), INK))
            n += 1
    # blush cheeks (all but Angry); keep the two cheeks apart even
    # when the eyes share one centre (spread == 0, one-eye species)
    blush_spread = spread if spread > 0 else er * 1.5
    if expr != "Angry":
        for bx in (fx - blush_spread * 1.7, fx + blush_spread * 1.7):
            els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#FF8FB0" opacity="0.55"/>'
                       % (f(bx), f(my - 18), f(er * 0.55), f(er * 0.32)))
            n += 1
    # mouths
    w = er * 1.5
    if expr == "Happy":
        els.append('<path d="M %s %s Q %s %s %s %s Q %s %s %s %s Z" fill="%s" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'
                   % (f(mx - w), f(my), f(mx - w * 0.6), f(my + w * 1.15),
                      f(mx), f(my + w * 1.15), f(mx + w * 0.6), f(my + w * 1.15),
                      f(mx + w), f(my), INK, INK))
        n += 1
        els.append('<path d="M %s %s Q %s %s %s %s L %s %s Q %s %s %s %s Z" fill="#FFFFFF"/>'
                   % (f(mx - w * 0.82), f(my + w * 0.12), f(mx), f(my + w * 0.42),
                      f(mx + w * 0.82), f(my + w * 0.12), f(mx + w * 0.82), f(my + w * 0.42),
                      f(mx), f(my + w * 0.62), f(mx - w * 0.82), f(my + w * 0.42)))
        n += 1
    elif expr == "Surprised":
        els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="6"/>'
                   % (f(mx), f(my + w * 0.3), f(w * 0.42), f(w * 0.55), INK, INK))
        n += 1
    elif expr == "Grinning":
        els.append('<path d="M %s %s Q %s %s %s %s Q %s %s %s %s Z" fill="#FFFFFF" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'
                   % (f(mx - w * 1.15), f(my), f(mx), f(my + w * 0.9),
                      f(mx + w * 1.15), f(my), f(mx), f(my + w * 0.35),
                      f(mx - w * 1.15), f(my), INK))
        n += 1
        for lx in (-0.55, 0, 0.55):
            els.append('<path d="M %s %s L %s %s" stroke="%s" stroke-width="4"/>'
                       % (f(mx + lx * w), f(my + w * 0.08), f(mx + lx * w * 0.9), f(my + w * 0.5), INK))
            n += 1
    elif expr == "Sleepy":
        els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round"/>'
                   % (f(mx - w * 0.5), f(my + w * 0.2), f(mx), f(my + w * 0.35),
                      f(mx + w * 0.5), f(my + w * 0.2), INK))
        n += 1
        els.append('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="5"/>'
                   % (f(mx + w * 1.5), f(my - w * 0.7), f(w * 0.22), "#BFE3FF", INK))
        n += 1
    elif expr == "Mischievous":
        els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>'
                   % (f(mx - w * 0.9), f(my + w * 0.25), f(mx + w * 0.1), f(my + w * 0.75),
                      f(mx + w * 1.0), f(my - w * 0.05), INK))
        n += 1
    elif expr == "Angry":
        els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>'
                   % (f(mx - w * 0.8), f(my + w * 0.7), f(mx), f(my + w * 0.1),
                      f(mx + w * 0.8), f(my + w * 0.7), INK))
        n += 1
    elif expr == "In Love":
        els.append('<path d="M %s %s Q %s %s %s %s Q %s %s %s %s Z" fill="%s" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'
                   % (f(mx - w * 0.9), f(my), f(mx - w * 0.5), f(my + w),
                      f(mx), f(my + w), f(mx + w * 0.5), f(my + w),
                      f(mx + w * 0.9), f(my), INK, INK))
        n += 1
        for hx in (mx - w * 1.6, mx + w * 1.6):
            els.append('<path d="%s" fill="#FF5C8A" stroke="%s" stroke-width="4" stroke-linejoin="round"/>'
                       % (heart_path(hx, my - w * 0.9, w * 0.34), INK))
            n += 1
    return n


def draw_antenna(els, traits, cx, top_y, colour, dark, rng):
    """Antenna / horns / spikes above head top (top_y). Returns count."""
    kind = traits["antenna"]
    n = 0
    if kind == "None":
        return 0
    if kind == "Two Ball Antennae":
        for sx in (cx - 62, cx + 62):
            els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="15" stroke-linecap="round"/>'
                       % (f(sx), f(top_y + 12), f(sx + (8 if sx > cx else -8)), f(top_y - 55), f(sx), f(top_y - 88), INK))
            els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="8" stroke-linecap="round"/>'
                       % (f(sx), f(top_y + 12), f(sx + (8 if sx > cx else -8)), f(top_y - 55), f(sx), f(top_y - 88), colour))
            els.append('<circle cx="%s" cy="%s" r="24" fill="%s" stroke="%s" stroke-width="6"/>'
                       % (f(sx), f(top_y - 100), colour, INK))
            els.append('<circle cx="%s" cy="%s" r="7" fill="#FFFFFF" opacity="0.7"/>'
                       % (f(sx - 7), f(top_y - 108)))
            n += 4
    elif kind == "Three Antenna Eyes":
        for i, sx in enumerate((cx - 78, cx, cx + 78)):
            h = 96 + (i % 2) * 14
            els.append('<path d="M %s %s L %s %s" stroke="%s" stroke-width="13" stroke-linecap="round"/>'
                       % (f(sx), f(top_y + 10), f(sx + (10 if sx > cx else -10 if sx < cx else 0)), f(top_y - h + 20), INK))
            els.append('<path d="M %s %s L %s %s" stroke="%s" stroke-width="7" stroke-linecap="round"/>'
                       % (f(sx), f(top_y + 10), f(sx + (10 if sx > cx else -10 if sx < cx else 0)), f(top_y - h + 20), colour))
            ex = sx + (10 if sx > cx else -10 if sx < cx else 0)
            els.append('<circle cx="%s" cy="%s" r="22" fill="#FFFFFF" stroke="%s" stroke-width="6"/>'
                       % (f(ex), f(top_y - h), INK))
            els.append('<circle cx="%s" cy="%s" r="10" fill="%s"/>'
                       % (f(ex), f(top_y - h), INK))
            els.append('<circle cx="%s" cy="%s" r="3.5" fill="#FFFFFF"/>'
                       % (f(ex - 3), f(top_y - h - 3)))
            n += 5
    elif kind == "Horns":
        for sx, dx in ((cx - 58, -1), (cx + 58, 1)):
            els.append('<path d="M %s %s L %s %s L %s %s Z" fill="%s" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'
                       % (f(sx - 26), f(top_y + 14), f(sx + dx * 44), f(top_y - 62),
                          f(sx + 26), f(top_y + 6), "#FFF3D6", INK))
            n += 1
    elif kind == "Spikes":
        for i, sx in enumerate((cx - 66, cx - 22, cx + 22, cx + 66)):
            h = 52 - abs(i - 1.5) * 8
            els.append('<path d="M %s %s L %s %s L %s %s Z" fill="%s" stroke="%s" stroke-width="5" stroke-linejoin="round"/>'
                       % (f(sx - 18), f(top_y + 10), f(sx), f(top_y - h),
                          f(sx + 18), f(top_y + 10), dark, INK))
            n += 1
    elif kind == "Single Stalk":
        els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="15" stroke-linecap="round"/>'
                   % (f(cx), f(top_y + 12), f(cx + 14), f(top_y - 55), f(cx + 6), f(top_y - 92), INK))
        els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="8" stroke-linecap="round"/>'
                   % (f(cx), f(top_y + 12), f(cx + 14), f(top_y - 55), f(cx + 6), f(top_y - 92), colour))
        els.append('<circle cx="%s" cy="%s" r="27" fill="%s" stroke="%s" stroke-width="6"/>'
                   % (f(cx + 6), f(top_y - 106), "#FFD23F", INK))
        els.append('<circle cx="%s" cy="%s" r="8" fill="#FFFFFF" opacity="0.7"/>'
                   % (f(cx - 1), f(top_y - 114)))
        n += 4
    return n


def draw_limbs(els, traits, geom, colour, dark, rng):
    """geom: dict with left, right, arm_y, bottom, leg_xs (optional),
    wing flag handled by caller for quadruped/jelly."""
    kind = traits["limbs"]
    n = 0
    if kind == "None":
        return 0
    if kind in ("Two Arms", "Two Arms + Two Legs"):
        wave = rng() < 0.5
        # left arm: down or waving up
        if wave:
            els.append(arm_path(geom["left"] + 8, geom["arm_y"], geom["left"] - 78, geom["arm_y"] - 92, colour))
            els.append(hand(geom["left"] - 84, geom["arm_y"] - 100, colour))
        else:
            els.append(arm_path(geom["left"] + 8, geom["arm_y"], geom["left"] - 62, geom["arm_y"] + 108, colour))
            els.append(hand(geom["left"] - 66, geom["arm_y"] + 116, colour))
        n += 2
        els.append(arm_path(geom["right"] - 8, geom["arm_y"], geom["right"] + 62, geom["arm_y"] + 108, colour))
        els.append(hand(geom["right"] + 66, geom["arm_y"] + 116, colour))
        n += 2
    if kind in ("Two Arms + Two Legs", "Four Legs"):
        for lx in geom.get("leg_xs", [390, 510]):
            els.append(leg(lx, geom["bottom"] - 18, geom["bottom"] + 62, colour))
            n += 1
    if kind == "Wings":
        for side in (-1, 1):
            wx = geom["left"] if side < 0 else geom["right"]
            els.append('<path d="M %s %s Q %s %s %s %s Q %s %s %s %s Z" fill="%s" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'
                       % (f(wx), f(geom["arm_y"] - 30),
                          f(wx + side * 110), f(geom["arm_y"] - 120),
                          f(wx + side * 150), f(geom["arm_y"] - 40),
                          f(wx + side * 105), f(geom["arm_y"] + 10),
                          f(wx), f(geom["arm_y"] + 26),
                          "#FFF3D6", INK))
            n += 1
    return n

# ------------------------------------------------------- species builders ----
# Each builder: (rng, els, traits, colour, dark, light) -> (count, geom)
# It draws antenna (behind), body + cel shade + belly, face, limbs.
# geom is only used by draw_limbs; builders call it themselves.

def _shade(els, cx, cy, rx, ry, dark):
    """Flat darker cel-shade crescent on the lower-right of a body."""
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.85"/>'
               % (f(cx + rx * 0.42), f(cy + ry * 0.38), f(rx * 0.52),
                  f(ry * 0.55), dark))
    return 1


def _shine(els, cx, cy, rx, ry):
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#FFFFFF" opacity="0.28"/>'
               % (f(cx - rx * 0.45), f(cy - ry * 0.5), f(rx * 0.28), f(ry * 0.16)))
    return 1


def species_round_blob(rng, els, t, colour, dark, light):
    cx, cy, rx, ry = 450, 600, 225, 255
    n = draw_antenna(els, t, cx, cy - ry, colour, dark, rng)
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(cy), f(rx), f(ry), colour, INK))
    n += 1
    n += _shade(els, cx, cy, rx, ry, dark)
    n += _shine(els, cx, cy, rx, ry)
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.9"/>'
               % (f(cx), f(cy + ry * 0.55), f(rx * 0.55), f(ry * 0.3), light))
    n += 1
    n += draw_face(els, t, cx, cy - 55, 82, 52, cx, cy + 105, rng)
    geom = {"left": cx - rx + 6, "right": cx + rx - 6, "arm_y": cy + 30,
            "bottom": cy + ry - 6, "leg_xs": [385, 515]}
    n += draw_limbs(els, t, geom, colour, dark, rng)
    return n


def species_tall_thin(rng, els, t, colour, dark, light):
    cx = 450
    n = draw_antenna(els, t, cx, 205, colour, dark, rng)
    # head + tall body
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(300), f(105), f(95), colour, INK))
    n += 1
    els.append('<path d="M %s %s L %s %s Q %s %s %s %s L %s %s Q %s %s %s %s Z" fill="%s" stroke="%s" stroke-width="7" stroke-linejoin="round"/>'
               % (f(cx - 78), f(380), f(cx - 95), f(830), f(cx), f(880),
                  f(cx + 95), f(830), f(cx + 78), f(380), f(cx), f(430),
                  f(cx - 78), f(380), colour, INK))
    n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.85"/>'
               % (f(cx + 52), f(640), f(34), f(190), dark))
    n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.9"/>'
               % (f(cx), f(620), f(48), f(150), light))
    n += 1
    n += draw_face(els, t, cx, 285, 48, 34, cx, 355, rng)
    geom = {"left": cx - 82, "right": cx + 82, "arm_y": 520,
            "bottom": 862, "leg_xs": [415, 485]}
    n += draw_limbs(els, t, geom, colour, dark, rng)
    return n


def species_long_neck(rng, els, t, colour, dark, light):
    cx = 450
    # neck spikes (ZEP-style) behind the neck
    n = 0
    for i, sy in enumerate((430, 500, 570)):
        els.append('<path d="M %s %s L %s %s L %s %s Z" fill="%s" stroke="%s" stroke-width="5" stroke-linejoin="round"/>'
                   % (f(cx + 52), f(sy - 26), f(cx + 108), f(sy), f(cx + 52), f(sy + 26),
                      "#FF7A2F", INK))
        n += 1
    n += draw_antenna(els, t, cx, 195, colour, dark, rng)
    # neck + body
    els.append('<path d="M %s %s L %s %s Q %s %s %s %s L %s %s Q %s %s %s %s Z" fill="%s" stroke="%s" stroke-width="7" stroke-linejoin="round"/>'
               % (f(cx - 42), f(300), f(cx - 58), f(720), f(cx), f(770),
                  f(cx + 58), f(720), f(cx + 42), f(300), f(cx), f(340),
                  f(cx - 42), f(300), colour, INK))
    n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(770), f(195), f(165), colour, INK))
    n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.85"/>'
               % (f(cx + 105), f(790), f(72), f(105), dark))
    n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.9"/>'
               % (f(cx), f(820), f(105), f(70), light))
    n += 1
    # head
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(255), f(128), f(88), colour, INK))
    n += 1
    n += _shine(els, cx, 255, 128, 88)
    n += draw_face(els, t, cx, 245, 58, 38, cx, 305, rng)
    geom = {"left": cx - 190, "right": cx + 190, "arm_y": 760,
            "bottom": 918, "leg_xs": [390, 510]}
    n += draw_limbs(els, t, geom, colour, dark, rng)
    return n


def species_spiky(rng, els, t, colour, dark, light):
    cx, cy, rx, ry = 450, 610, 215, 235
    n = draw_antenna(els, t, cx, cy - ry - 30, colour, dark, rng)
    # spikes around the body, drawn behind it
    import math
    for i in range(9):
        ang = 2 * math.pi * i / 9 - math.pi / 2 + (rng() - 0.5) * 0.2
        bx, by = cx + rx * 0.92 * math.cos(ang), cy + ry * 0.92 * math.sin(ang)
        tx, ty = cx + (rx + 62) * math.cos(ang), cy + (ry + 62) * math.sin(ang)
        px, py = -math.sin(ang) * 26, math.cos(ang) * 26
        els.append('<polygon points="%s,%s %s,%s %s,%s" fill="%s" stroke="%s" stroke-width="5" stroke-linejoin="round"/>'
                   % (f(bx + px), f(by + py), f(tx), f(ty), f(bx - px), f(by - py), dark, INK))
        n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(cy), f(rx), f(ry), colour, INK))
    n += 1
    n += _shade(els, cx, cy, rx, ry, dark)
    n += _shine(els, cx, cy, rx, ry)
    n += draw_face(els, t, cx, cy - 45, 78, 50, cx, cy + 110, rng)
    geom = {"left": cx - rx + 6, "right": cx + rx - 6, "arm_y": cy + 30,
            "bottom": cy + ry - 6, "leg_xs": [390, 510]}
    n += draw_limbs(els, t, geom, colour, dark, rng)
    return n


def species_quadruped(rng, els, t, colour, dark, light):
    cx, cy = 450, 660
    n = 0
    # tail behind
    els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="30" stroke-linecap="round"/>'
               % (f(cx - 235), f(cy - 20), f(cx - 320), f(cy - 90), f(cx - 300), f(cy - 170), INK))
    els.append('<path d="M %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="20" stroke-linecap="round"/>'
               % (f(cx - 235), f(cy - 20), f(cx - 320), f(cy - 90), f(cx - 300), f(cy - 170), colour))
    els.append('<circle cx="%s" cy="%s" r="26" fill="%s" stroke="%s" stroke-width="6"/>'
               % (f(cx - 300), f(cy - 178), dark, INK))
    n += 3
    # body + head
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(cy), f(255), f(145), colour, INK))
    n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.85"/>'
               % (f(cx + 130), f(cy + 45), f(105), f(70), dark))
    n += 1
    hx, hy = cx + 235, cy - 115
    n += draw_antenna(els, t, hx, hy - 82, colour, dark, rng)
    els.append('<circle cx="%s" cy="%s" r="108" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(hx), f(hy), colour, INK))
    n += 1
    n += _shine(els, hx, hy, 108, 108)
    # ears
    for ex in (hx - 62, hx + 62):
        els.append('<path d="M %s %s L %s %s L %s %s Z" fill="%s" stroke="%s" stroke-width="5" stroke-linejoin="round"/>'
                   % (f(ex - 24), f(hy - 82), f(ex + (10 if ex > hx else -10)), f(hy - 138),
                      f(ex + 24), f(hy - 82), light, INK))
        n += 1
    n += draw_face(els, t, hx, hy - 12, 52, 36, hx, hy + 58, rng)
    # four legs (always, this is a quadruped)
    for lx in (270, 360, 540, 630):
        els.append(leg(lx, cy + 95, cy + 195, colour))
        n += 1
    # small arms on the head end are skipped; wings if rolled
    if t["limbs"] == "Wings":
        geom = {"left": cx - 250, "right": cx + 250, "arm_y": cy - 40,
                "bottom": cy + 140, "leg_xs": [300, 600]}
        n += draw_limbs(els, t, geom, colour, dark, rng)
    return n


def species_jelly(rng, els, t, colour, dark, light):
    cx, cy, rx, ry = 450, 520, 225, 195
    n = draw_antenna(els, t, cx, cy - ry, colour, dark, rng)
    # dome
    els.append('<path d="M %s %s A %s %s 0 0 1 %s %s Q %s %s %s %s Z" fill="%s" stroke="%s" stroke-width="7" stroke-linejoin="round"/>'
               % (f(cx - rx), f(cy + 60), f(rx), f(ry), f(cx + rx), f(cy + 60),
                  f(cx + rx * 0.5), f(cy + 95), f(cx - rx * 0.5), f(cy + 95), colour, INK))
    n += 1
    els.append('<path d="M %s %s A %s %s 0 0 1 %s %s Q %s %s %s %s Z" fill="%s" opacity="0.85"/>'
               % (f(cx + rx * 0.35), f(cy + 60), f(rx * 0.6), f(ry * 0.85),
                  f(cx + rx), f(cy + 60), f(cx + rx * 0.7), f(cy + 88),
                  f(cx + rx * 0.35), f(cy + 88), dark))
    n += 1
    n += _shine(els, cx - 40, cy - 40, rx, ry)
    # tentacles: wavy lines below the dome
    for i, tx in enumerate((330, 410, 490, 570)):
        amp = 26 + rng() * 14
        ln = 150 + rng() * 60
        els.append('<path d="M %s %s Q %s %s %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="26" stroke-linecap="round"/>'
                   % (f(tx), f(cy + 78), f(tx + amp), f(cy + 78 + ln * 0.4),
                      f(tx - amp), f(cy + 78 + ln * 0.7), f(tx + amp * 0.5), f(cy + 78 + ln),
                      f(tx), f(cy + 78 + ln), INK))
        els.append('<path d="M %s %s Q %s %s %s %s Q %s %s %s %s" fill="none" stroke="%s" stroke-width="17" stroke-linecap="round"/>'
                   % (f(tx), f(cy + 78), f(tx + amp), f(cy + 78 + ln * 0.4),
                      f(tx - amp), f(cy + 78 + ln * 0.7), f(tx + amp * 0.5), f(cy + 78 + ln),
                      f(tx), f(cy + 78 + ln), colour))
        n += 2
    # inner spots
    for _ in range(3):
        els.append('<circle cx="%s" cy="%s" r="%s" fill="%s" opacity="0.5"/>'
                   % (f(cx + (rng() - 0.5) * 260), f(cy - 40 + rng() * 90),
                      f(10 + rng() * 14), light))
        n += 1
    n += draw_face(els, t, cx, cy - 25, 80, 50, cx, cy + 45, rng)
    return n


def species_wide_flat(rng, els, t, colour, dark, light):
    cx, cy, rx, ry = 450, 660, 295, 135
    n = draw_antenna(els, t, cx, cy - ry, colour, dark, rng)
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(cy), f(rx), f(ry), colour, INK))
    n += 1
    els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="0.85"/>'
               % (f(cx + rx * 0.55), f(cy + 30), f(rx * 0.4), f(ry * 0.55), dark))
    n += 1
    n += _shine(els, cx, cy, rx, ry)
    # back fin
    els.append('<path d="M %s %s Q %s %s %s %s Z" fill="%s" stroke="%s" stroke-width="6" stroke-linejoin="round"/>'
               % (f(cx - 120), f(cy - ry + 18), f(cx - 60), f(cy - ry - 74),
                  f(cx + 10), f(cy - ry + 14), dark, INK))
    n += 1
    n += draw_face(els, t, cx, cy - 18, 105, 44, cx, cy + 62, rng)
    geom = {"left": cx - rx + 8, "right": cx + rx - 8, "arm_y": cy + 10,
            "bottom": cy + ry - 4, "leg_xs": [360, 540]}
    n += draw_limbs(els, t, geom, colour, dark, rng)
    return n


def species_one_eye_orb(rng, els, t, colour, dark, light):
    cx, cy, r = 450, 560, 240
    n = draw_antenna(els, t, cx, cy - r, colour, dark, rng)
    els.append('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="7"/>'
               % (f(cx), f(cy), f(r), colour, INK))
    n += 1
    els.append('<circle cx="%s" cy="%s" r="%s" fill="%s" opacity="0.85"/>'
               % (f(cx + 105), f(cy + 95), f(115), dark))
    n += 1
    n += _shine(els, cx, cy, r, r)
    # cheek bumps on the sides
    for sx in (cx - r - 6, cx + r + 6):
        els.append('<circle cx="%s" cy="%s" r="30" fill="%s" stroke="%s" stroke-width="6"/>'
                   % (f(sx), f(cy + 60), colour, INK))
        n += 1
    t1 = dict(t)
    t1["eye_count"] = 1
    n += draw_face(els, t1, cx, cy - 45, 0, 62, cx, cy + 115, rng)
    geom = {"left": cx - r + 4, "right": cx + r - 4, "arm_y": cy + 40,
            "bottom": cy + r - 6, "leg_xs": [390, 510]}
    n += draw_limbs(els, t, geom, colour, dark, rng)
    return n


SPECIES_BUILDERS = {
    "Round Blob": species_round_blob,
    "Tall Thin": species_tall_thin,
    "Long Neck": species_long_neck,
    "Spiky": species_spiky,
    "Quadruped": species_quadruped,
    "Floating Jelly": species_jelly,
    "Wide Flat": species_wide_flat,
    "One-Eye Orb": species_one_eye_orb,
}

# ------------------------------------------------------------ token build ----
def display_limbs(species, limbs):
    """Limbs trait as actually drawn. Quadruped always draws four legs
    (its builder skips arms and only adds wings when rolled), and Floating
    Jelly always draws tentacles and never calls draw_limbs, so the rolled
    value would misdescribe the art for those two species. The raw rolled
    value still drives the drawing; only the recorded trait is remapped."""
    if species == "Quadruped":
        return "Four Legs + Wings" if limbs == "Wings" else "Four Legs"
    if species == "Floating Jelly":
        return "Tentacles"
    return limbs


def build_token(token_id, deck):
    rng = mulberry32(seed_for(token_id))
    rarity = TIER_NAMES[deck["deck"][token_id - 1]]
    # traits in a fixed draw order
    species = pick(rng, SPECIES)
    body_name = pick(rng, list(BODY_COLORS.keys()))
    body, dark, light = BODY_COLORS[body_name]
    bg_choices = [b for b in BACKGROUNDS if BACKGROUNDS[b][0] != body]
    bg_name = pick(rng, bg_choices)
    eye_count = pick(rng, [1, 2, 2, 2, 3])
    if species == "One-Eye Orb":
        eye_count = 1
    eye_shape = pick(rng, EYE_SHAPES)
    expression = pick(rng, EXPRESSIONS)
    antenna = pick(rng, ANTENNAS)
    limbs = pick(rng, LIMBS)
    if species == "Floating Jelly":
        limbs = "None"
    traits = {"eye_count": eye_count, "eye_shape": eye_shape,
              "expression": expression, "antenna": antenna, "limbs": limbs}
    eyes_value = "%d %s" % (eye_count, eye_shape)

    els = []
    n = draw_background(rng, els, bg_name)
    n += SPECIES_BUILDERS[species](rng, els, traits, body, dark, light)

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1125" '
           'width="900" height="1125">%s</svg>' % "".join(els))
    rec = {
        "id": token_id,
        "species": species,
        "rarity": rarity,
        "bodyColor": body_name,
        "eyes": eyes_value,
        "expression": expression,
        "antenna": antenna,
        "limbs": display_limbs(species, limbs),
        "background": bg_name,
        "elements": n,
        "svg": svg,
    }
    return rec


def metadata_for(rec):
    return {
        "name": "OOBIX — Alien #%04d" % rec["id"],
        "description": DESCRIPTION % rec["id"],
        "image": IMAGE_BASE + "%d.svg" % rec["id"],
        "attributes": [
            {"trait_type": "Species", "value": rec["species"]},
            {"trait_type": "Rarity", "value": rec["rarity"]},
            {"trait_type": "Body Color", "value": rec["bodyColor"]},
            {"trait_type": "Eyes", "value": rec["eyes"]},
            {"trait_type": "Expression", "value": rec["expression"]},
            {"trait_type": "Antenna", "value": rec["antenna"]},
            {"trait_type": "Limbs", "value": rec["limbs"]},
            {"trait_type": "Background", "value": rec["background"]},
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="",
                    help="comma-separated token ids: preview mode, SVGs only")
    ap.add_argument("--out", default="",
                    help="preview output dir for --only (default: ./preview)")
    args = ap.parse_args()
    deck = load_deck()
    if args.only:
        ids = [int(s) for s in args.only.split(",") if s.strip()]
        out_dir = args.out or os.path.join(BASE, "preview")
        os.makedirs(out_dir, exist_ok=True)
        for token_id in ids:
            rec = build_token(token_id, deck)
            path = os.path.join(out_dir, "%d.svg" % token_id)
            with open(path, "w") as fh:
                fh.write(rec["svg"])
            try:
                ET.fromstring(rec["svg"])
                xml_ok = "XML ok"
            except ET.ParseError as e:
                xml_ok = "XML FAIL: %s" % e
            print("#%d %s / %s / %s / %s / %s eyes / %d elements / %d bytes / %s"
                  % (token_id, rec["species"], rec["rarity"], rec["bodyColor"],
                     rec["background"], rec["eyes"], rec["elements"],
                     len(rec["svg"]), xml_ok))
        print("Preview SVGs in %s" % out_dir)
        return
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)
    tokens = []
    for token_id in range(1, TOTAL + 1):
        rec = build_token(token_id, deck)
        sha = hashlib.sha256(rec["svg"].encode("utf-8")).hexdigest()
        with open(os.path.join(IMG_DIR, "%d.svg" % token_id), "w") as fh:
            fh.write(rec["svg"])
        with open(os.path.join(META_DIR, "%d.json" % token_id), "w") as fh:
            json.dump(metadata_for(rec), fh, indent=2)
            fh.write("\n")
        tokens.append({
            "id": rec["id"],
            "species": rec["species"],
            "rarity": rec["rarity"],
            "bodyColor": rec["bodyColor"],
            "eyes": rec["eyes"],
            "expression": rec["expression"],
            "antenna": rec["antenna"],
            "limbs": rec["limbs"],
            "background": rec["background"],
            "elements": rec["elements"],
            "sha256": sha,
        })
    with open(os.path.join(OUT, "all-tokens.json"), "w") as fh:
        json.dump(tokens, fh, indent=2)
        fh.write("\n")
    summary = {
        "total": TOTAL,
        "rarities": dict(Counter(t["rarity"] for t in tokens)),
        "species": dict(Counter(t["species"] for t in tokens)),
        "backgrounds": dict(Counter(t["background"] for t in tokens)),
        "bodyColors": dict(Counter(t["bodyColor"] for t in tokens)),
        "imageBase": IMAGE_BASE,
        "metadataBase": META_BASE,
        "generator": "art/generate.py",
        "deckHash": deck["deckHash"],
        "seed": deck["seed"],
        "contract": {"status": "not deployed", "address": ""},
    }
    with open(os.path.join(OUT, "collection.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    print("Generated %d tokens." % TOTAL)
    print("rarities:", summary["rarities"])
    print("species:", summary["species"])
    print("backgrounds:", summary["backgrounds"])
    print("bodyColors:", summary["bodyColors"])
    print("distinct SVG hashes:", len({t["sha256"] for t in tokens}))


if __name__ == "__main__":
    main()
