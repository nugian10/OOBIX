#!/usr/bin/env python3
"""Rewrite OOBIX metadata image URLs to a new base URL.

Rewrites the `image` field of every collection/metadata/<id>.json to
<base>/<id>.svg and updates collection.json `imageBase` (and
`metadataBase` when the base looks like an images base — it does not
touch metadataBase otherwise). Local only: no upload, no network.

USAGE:
    python3 scripts/rewrite-image-urls.py --base https://example.com/images/
    python3 scripts/rewrite-image-urls.py --dry-run
    python3 scripts/rewrite-image-urls.py   # default: GitHub raw images base
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "collection")
META_DIR = os.path.join(OUT, "metadata")
DEFAULT_BASE = "https://raw.githubusercontent.com/nugian10/OOBIX/main/collection/images/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE,
                    help="new images base URL (default: GitHub raw images base)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change, write nothing")
    args = ap.parse_args()
    base = args.base
    if not base.endswith("/"):
        base += "/"

    changed, unchanged = 0, 0
    for fn in sorted(os.listdir(META_DIR), key=lambda s: int(s[:-5])):
        path = os.path.join(META_DIR, fn)
        with open(path) as fh:
            meta = json.load(fh)
        token_id = int(fn[:-5])
        new_image = base + "%d.svg" % token_id
        if meta.get("image") == new_image:
            unchanged += 1
            continue
        changed += 1
        if not args.dry_run:
            meta["image"] = new_image
            with open(path, "w") as fh:
                json.dump(meta, fh, indent=2)
                fh.write("\n")

    coll_path = os.path.join(OUT, "collection.json")
    coll_changed = False
    with open(coll_path) as fh:
        coll = json.load(fh)
    if coll.get("imageBase") != base:
        coll_changed = True
        if not args.dry_run:
            coll["imageBase"] = base
            with open(coll_path, "w") as fh:
                json.dump(coll, fh, indent=2)
                fh.write("\n")

    print("metadata files changed: %d" % changed)
    print("metadata files already correct: %d" % unchanged)
    print("collection.json imageBase %s: %s"
          % ("would change to " + base if (coll_changed and args.dry_run)
             else "updated to " + base if coll_changed
             else "already " + base, ""))
    if args.dry_run:
        print("DRY RUN — nothing written.")
    else:
        print("Done. New image base: %s" % base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
