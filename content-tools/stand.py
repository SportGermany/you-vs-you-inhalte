#!/usr/bin/env python3
"""Zeigt, wie viele Lektionen es pro Unterthema gibt und wo noch am meisten fehlt.

Ziel: 3500 Lektionen. Verteilung nach KONZEPT.md, hochgerechnet von 2000 auf 3500:
Gesundheit 1050, Geschichte und Politik 790, Psychologie und Gehirn 610,
Finanzen und Alltag 525, Natur und Wissenschaft 525.

Aufruf:  python3 content-tools/stand.py [--naechste N]
  --naechste N  listet die N Unterthemen mit der größten Lücke (für den nächsten Batch)
"""
import argparse
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL_GESAMT = 3500
ZIEL_WELT = {
    "gesundheit": 1050,
    "geschichte-politik": 790,
    "psychologie-gehirn": 610,
    "finanzen-alltag": 525,
    "natur-wissenschaft": 525,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--naechste", type=int, default=0)
    args = ap.parse_args()

    themen = json.load(open(os.path.join(ROOT, "content", "themen.json"), encoding="utf-8"))
    anzahl = {}
    titel = []
    for pfad in glob.glob(os.path.join(ROOT, "content", "lektionen", "**", "*.json"), recursive=True):
        l = json.load(open(pfad, encoding="utf-8"))
        anzahl[l["unterthema"]] = anzahl.get(l["unterthema"], 0) + 1
        titel.append((l["unterthema"], l["titel"]))
    gesamt = sum(anzahl.values())

    luecken = []
    for w in themen["themenwelten"]:
        ziel_u = ZIEL_WELT[w["id"]] / len(w["unterthemen"])
        for u in w["unterthemen"]:
            n = anzahl.get(u["id"], 0)
            luecken.append((ziel_u - n, w["id"], u["id"], u["name"], n, round(ziel_u)))

    print(f"Gesamt: {gesamt} von {ZIEL_GESAMT} Lektionen ({ZIEL_GESAMT - gesamt} fehlen).")
    if args.naechste:
        print(f"\nDie {args.naechste} Unterthemen mit der größten Lücke:")
        for luecke, welt, uid, name, n, ziel in sorted(luecken, reverse=True)[:args.naechste]:
            print(f"  {welt}/{uid} ({name}): {n} von {ziel}")
            vorhanden = sorted(t for u, t in titel if u == uid)
            if vorhanden:
                print("    vorhandene Titel: " + " | ".join(vorhanden))
    else:
        for luecke, welt, uid, name, n, ziel in sorted(luecken, key=lambda x: (x[1], x[2])):
            print(f"  {welt}/{uid}: {n} von {ziel}")


if __name__ == "__main__":
    main()
