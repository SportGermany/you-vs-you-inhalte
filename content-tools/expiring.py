#!/usr/bin/env python3
"""Meldet alle Lektionen und Karten, die in den nächsten 30 Tagen ablaufen.

Aufruf:  python3 content-tools/expiring.py [--tage 30] [--datum JJJJ-MM-TT]
Eine Lektion gilt als versorgt, wenn ein Nachfolger (ersetzt_durch oder höhere Version) existiert.
Rückgabewert 1, wenn eine ablaufende Lektion noch keinen Nachfolger hat.
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEKTIONEN = os.path.join(ROOT, "content", "lektionen")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tage", type=int, default=30)
    ap.add_argument("--datum", help="Stichtag, Standard heute")
    args = ap.parse_args()
    heute = dt.date.fromisoformat(args.datum) if args.datum else dt.date.today()
    grenze = heute + dt.timedelta(days=args.tage)

    lektionen = []
    for pfad in sorted(glob.glob(os.path.join(LEKTIONEN, "**", "*.json"), recursive=True)):
        l = json.load(open(pfad, encoding="utf-8"))
        l["_datei"] = os.path.relpath(pfad, ROOT)
        lektionen.append(l)
    versionen = {}
    for l in lektionen:
        versionen.setdefault(l["id"], []).append(l["version"])
    ids = set(versionen)

    offen = 0
    treffer = 0
    for l in sorted(lektionen, key=lambda x: x.get("gueltig_bis") or "9999"):
        bis = l.get("gueltig_bis")
        if bis:
            d = dt.date.fromisoformat(bis)
            if d <= grenze:
                treffer += 1
                nachfolger = (l.get("ersetzt_durch") in ids) or max(versionen[l["id"]]) > l["version"]
                status = "Nachfolger vorhanden" if nachfolger else "KEIN NACHFOLGER"
                if not nachfolger:
                    offen += 1
                schon = " (bereits abgelaufen)" if d < heute else ""
                print(f"{bis}  {l['id']} v{l['version']}  \"{l['titel']}\"  {status}{schon}  [{l['_datei']}]")
        for i, k in enumerate(l.get("karten", []), 1):
            kb = k.get("gueltig_bis")
            if kb and dt.date.fromisoformat(kb) <= grenze:
                treffer += 1
                print(f"{kb}  {l['id']} v{l['version']} Karte {i} ({k.get('typ')})  [{l['_datei']}]")

    if not treffer:
        print(f"Nichts läuft bis {grenze.isoformat()} ab.")
    else:
        print(f"\n{treffer} Einträge laufen bis {grenze.isoformat()} ab, {offen} Lektionen ohne Nachfolger.")
    sys.exit(1 if offen else 0)


if __name__ == "__main__":
    main()
