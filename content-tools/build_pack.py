#!/usr/bin/env python3
"""Baut die Inhaltspakete für die App.

Schreibt standardmäßig ins Hauptverzeichnis dieses Repositorys (dort lädt die App die Pakete):
  themen.json, lernpfade.json und je Themenwelt ein Paket <themenwelt>.json
  sowie index.json mit Paketversion.

Nur Lektionen mit pruefstatus "freigegeben" werden aufgenommen.
Mit --entwuerfe werden auch Entwürfe und geprüfte Lektionen aufgenommen (nur für Tests und die Beta).

Aufruf:  python3 content-tools/build_pack.py [--entwuerfe] [--ziel PFAD]
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402

ROOT = validate.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entwuerfe", action="store_true")
    ap.add_argument("--ziel", default=ROOT)
    args = ap.parse_args()

    p = validate.pruefe(verbose=False)
    if p.fehler:
        for m in p.fehler:
            print(m)
        sys.exit("Inhaltsprüfung fehlgeschlagen. Paket wurde nicht gebaut.")

    erlaubt = {"freigegeben"} | ({"entwurf", "geprueft"} if args.entwuerfe else set())
    themen = json.load(open(validate.THEMEN, encoding="utf-8"))
    lernpfade = json.load(open(validate.LERNPFADE, encoding="utf-8")) if os.path.exists(validate.LERNPFADE) else []

    # Ein Paket pro Unterthema. So muss die App bei neuen Lektionen nur die geänderten Pakete laden.
    welt_von = {u["id"]: w["id"] for w in themen["themenwelten"] for u in w["unterthemen"]}
    pakete = {u: [] for u in welt_von}
    for pfad in sorted(glob.glob(os.path.join(validate.LEKTIONEN, "**", "*.json"), recursive=True)):
        l = json.load(open(pfad, encoding="utf-8"))
        if l["pruefstatus"] in erlaubt:
            pakete[l["unterthema"]].append(l)

    os.makedirs(args.ziel, exist_ok=True)
    for alt in glob.glob(os.path.join(args.ziel, "*.json")):
        os.remove(alt)

    hashes = {}

    def schreibe(name, daten):
        text = json.dumps(daten, ensure_ascii=False, separators=(",", ":"))
        open(os.path.join(args.ziel, name), "w", encoding="utf-8").write(text)
        hashes[name] = hashlib.sha256(text.encode()).hexdigest()[:16]

    schreibe("themen.json", themen)
    schreibe("lernpfade.json", lernpfade)
    dateien = []
    for unterthema, lektionen in pakete.items():
        name = f"paket-{unterthema}.json"
        schreibe(name, {"themenwelt": welt_von[unterthema], "unterthema": unterthema, "lektionen": lektionen})
        dateien.append(name)
    gesamt = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(hashes.items())).encode()).hexdigest()[:16]
    index = {
        "paketversion": gesamt,
        "erstellt": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "anzahl": sum(len(v) for v in pakete.values()),
        "pakete": dateien,
        "hashes": hashes,
    }
    text = json.dumps(index, ensure_ascii=False, indent=1)
    open(os.path.join(args.ziel, "index.json"), "w", encoding="utf-8").write(text)
    print(f"{index['anzahl']} Lektionen in {len(dateien)} Paketen nach {args.ziel} geschrieben "
          f"(Version {index['paketversion']}).")


if __name__ == "__main__":
    main()
