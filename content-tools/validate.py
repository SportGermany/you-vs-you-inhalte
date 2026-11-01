#!/usr/bin/env python3
"""Inhaltsprüfung für You vs You.

Prüft alle Lektionen in content/lektionen/**.json:
Schema, Pflichtfelder, Textlängen, Anrede mit du, Hinweis bei Gesundheit,
keine Dosierungen ohne Quelle, gueltig_bis bei zeitgebundenen Inhalten, doppelte Titel.

Aufruf:  python3 content-tools/validate.py [--streng]
  --streng  Warnungen zählen als Fehler (für die Freigabe).
Rückgabewert 1, wenn Fehler gefunden wurden.
"""
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEKTIONEN = os.path.join(ROOT, "content", "lektionen")
THEMEN = os.path.join(ROOT, "content", "themen.json")
LERNPFADE = os.path.join(ROOT, "content", "lernpfade.json")

HINWEIS = ("Dies ist Bildung, keine medizinische Beratung. "
           "Sprich bei Beschwerden oder Medikamenten mit Ärztin oder Arzt.")
PRUEFSTATUS = {"entwurf", "geprueft", "freigegeben"}
URTEILE = {"mythos", "wahrheit", "teils"}
KARTENTYPEN = {"einstieg", "wissen", "mythos", "schritte", "quiz", "zusammenfassung"}

# Textlängen laut Stilguide
WISSEN_WOERTER = (40, 90)
MYTHOS_WOERTER = (25, 60)
SCHRITTE = (3, 6)
QUIZ = (3, 5)
PUNKTE = (3, 5)
WISSEN_KARTEN = (2, 10)
SATZ_MAX_WOERTER = 25

# Zeitgebundene Inhalte brauchen gueltig_bis
ZEITGEBUNDENE_UNTERTHEMEN = {"geopolitik"}
ZEITGEBUNDENE_TAGS = {"amtsinhaber", "preise", "gesetze", "aktuell", "wahlen", "steuersaetze"}

# Siezen erkennen (Großschreibung mitten im Satz)
SIEZEN = re.compile(r"(?<![.!?:]\s)(?<!^)\b(Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihrer)\b")
# Mengenangaben, die nach Dosierung aussehen
DOSIS = re.compile(r"\b\d+[.,]?\d*\s?(mg|µg|mcg|ug|g|IE|I\.E\.|IU|ml|Milligramm|Mikrogramm|Gramm)\b", re.I)
# Aufforderungen zur Einnahme
EINNAHME = re.compile(r"\b(nimm|nehmen Sie|schluck|einnehmen solltest|solltest .{0,20}einnehmen)\b", re.I)
# Superlative und Heilversprechen
VERBOTEN = re.compile(r"\b(heilt|garantiert|Wundermittel|Geheimtipp|der beste|die beste|das beste|100 ?%)\b", re.I)


def woerter(text):
    return len(re.findall(r"\w+", text))


def saetze(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def parse_datum(s):
    if s is None:
        return None
    return dt.date.fromisoformat(s)


class Pruefer:
    def __init__(self, streng):
        self.streng = streng
        self.fehler = []
        self.warnungen = []

    def f(self, datei, msg):
        self.fehler.append(f"FEHLER   {datei}: {msg}")

    def w(self, datei, msg):
        self.warnungen.append(f"WARNUNG  {datei}: {msg}")

    def texte(self, lektion):
        """Alle sichtbaren Texte einer Lektion."""
        out = [lektion.get("titel", "")]
        for k in lektion.get("karten", []):
            out += k.get("absaetze", []) or []
            for feld in ("titel", "merke", "behauptung", "erklaerung", "frage"):
                if k.get(feld):
                    out.append(k[feld])
            out += [s.get("titel", "") + " " + s.get("text", "") for s in k.get("schritte", []) or []]
            out += k.get("optionen", []) or []
            out += k.get("punkte", []) or []
        return [t for t in out if t]


def pruefe(streng=False, verbose=True):
    p = Pruefer(streng)
    themen = json.load(open(THEMEN, encoding="utf-8"))
    welten = {w["id"]: w for w in themen["themenwelten"]}
    unterthemen = {u["id"]: w["id"] for w in themen["themenwelten"] for u in w["unterthemen"]}

    dateien = sorted(glob.glob(os.path.join(LEKTIONEN, "**", "*.json"), recursive=True))
    titel_gesehen = {}
    ids = {}
    for pfad in dateien:
        datei = os.path.relpath(pfad, ROOT)
        try:
            l = json.load(open(pfad, encoding="utf-8"))
        except json.JSONDecodeError as e:
            p.f(datei, f"kein gültiges JSON: {e}")
            continue

        # Pflichtfelder
        pflicht = {"id": str, "version": int, "themenwelt": str, "unterthema": str, "titel": str,
                   "minuten": int, "zeitlos": bool, "stand": str, "pruefstatus": str,
                   "quellen": list, "tags": list, "karten": list}
        for feld, typ in pflicht.items():
            if feld not in l:
                p.f(datei, f"Pflichtfeld '{feld}' fehlt")
            elif not isinstance(l[feld], typ) or (typ is int and isinstance(l[feld], bool)):
                p.f(datei, f"Feld '{feld}' hat falschen Typ")
        if p.fehler and p.fehler[-1].startswith(f"FEHLER   {datei}") and any(f not in l for f in pflicht):
            continue

        lid, version = l["id"], l["version"]
        if not re.fullmatch(r"[a-z0-9-]+", lid):
            p.f(datei, "id darf nur a-z, 0-9 und - enthalten")
        if version < 1:
            p.f(datei, "version beginnt bei 1")
        if (lid, version) in ids:
            p.f(datei, f"id {lid} Version {version} doppelt (auch in {ids[(lid, version)]})")
        ids[(lid, version)] = datei

        if l["themenwelt"] not in welten:
            p.f(datei, f"unbekannte themenwelt '{l['themenwelt']}'")
        if l["unterthema"] not in unterthemen:
            p.f(datei, f"unbekanntes unterthema '{l['unterthema']}'")
        elif unterthemen[l["unterthema"]] != l["themenwelt"]:
            p.f(datei, "unterthema gehört nicht zur themenwelt")
        if l["pruefstatus"] not in PRUEFSTATUS:
            p.f(datei, f"pruefstatus muss {sorted(PRUEFSTATUS)} sein")
        if not re.fullmatch(r"\d{4}-\d{2}", l["stand"]):
            p.f(datei, "stand muss JJJJ-MM sein")
        if not 1 <= l["minuten"] <= 20:
            p.w(datei, "minuten außerhalb von 1 bis 20")
        sl = l.get("studienlage")
        if sl is not None and sl not in (1, 2, 3):
            p.f(datei, "studienlage muss 1, 2, 3 oder null sein")

        # Titel
        if not l["titel"].endswith("?"):
            p.w(datei, "Titel sollte als Frage formuliert sein")
        key = l["titel"].strip().lower()
        if key in titel_gesehen and titel_gesehen[key][0] != lid:
            p.f(datei, f"doppelter Titel (auch in {titel_gesehen[key][1]})")
        titel_gesehen.setdefault(key, (lid, datei))

        # Gültigkeit
        try:
            von, bis = parse_datum(l.get("gueltig_von")), parse_datum(l.get("gueltig_bis"))
            if von and bis and bis < von:
                p.f(datei, "gueltig_bis liegt vor gueltig_von")
        except ValueError:
            p.f(datei, "gueltig_von/gueltig_bis müssen JJJJ-MM-TT sein")
            bis = None
        zeitgebunden = (not l["zeitlos"]) or l["unterthema"] in ZEITGEBUNDENE_UNTERTHEMEN \
            or bool(ZEITGEBUNDENE_TAGS & set(l["tags"]))
        if zeitgebunden and not l.get("gueltig_bis"):
            p.f(datei, "zeitgebundener Inhalt ohne gueltig_bis")
        if zeitgebunden and l["zeitlos"]:
            p.f(datei, "zeitgebundener Inhalt ist als zeitlos markiert")

        # Quellen
        if not l["quellen"]:
            p.f(datei, "mindestens eine Quelle nötig")
        for i, q in enumerate(l["quellen"]):
            for feld in ("titel", "herausgeber", "url", "abgerufen"):
                if feld not in q:
                    p.f(datei, f"Quelle {i + 1}: Feld '{feld}' fehlt")
            if q.get("url") and not q["url"].startswith("https://"):
                p.f(datei, f"Quelle {i + 1}: url muss mit https:// beginnen")
            if not q.get("titel") or not q.get("herausgeber") or not q.get("url"):
                p.f(datei, f"Quelle {i + 1}: titel, herausgeber und url dürfen nicht leer sein")
            if not q.get("abgerufen"):
                (p.f if l["pruefstatus"] == "freigegeben" else p.w)(
                    datei, f"Quelle {i + 1}: Abrufdatum fehlt, Quelle noch nicht geprüft")
            else:
                try:
                    dt.date.fromisoformat(q["abgerufen"])
                except ValueError:
                    p.f(datei, f"Quelle {i + 1}: abgerufen muss JJJJ-MM-TT sein")

        # Gesundheit
        gesundheit = welten.get(l["themenwelt"], {}).get("gesundheit", False)
        if gesundheit:
            if sl is None:
                p.f(datei, "Gesundheitslektion braucht studienlage (1 bis 3)")
            if l.get("hinweis") != HINWEIS:
                p.f(datei, "Gesundheitslektion braucht den festen Hinweistext im Feld 'hinweis'")
            if l["unterthema"] == "supplements":
                if not any(k.get("typ") == "wissen" and k.get("titel") == "Das solltest du beachten"
                           for k in l["karten"]):
                    p.f(datei, "Supplement-Lektion braucht die Karte 'Das solltest du beachten'")
            if l["unterthema"] == "stoffwechsel-abnehmen":
                alle = " ".join(p.texte(l)).lower()
                if "essstörung" not in alle:
                    p.f(datei, "Abnehmen-Lektion braucht einen Hinweis zu Essstörungen")

        # Texte allgemein
        for t in p.texte(l):
            if SIEZEN.search(t):
                p.f(datei, f"Anrede mit Sie gefunden: \"{t[:60]}\"")
            if VERBOTEN.search(t):
                p.w(datei, f"Superlativ oder Heilversprechen: \"{t[:60]}\"")
            if gesundheit and EINNAHME.search(t):
                p.f(datei, f"Aufforderung zur Einnahme: \"{t[:60]}\"")
            if DOSIS.search(t):
                if not gesundheit or not l["quellen"]:
                    p.w(datei, f"Mengenangabe gefunden, bitte prüfen: \"{t[:60]}\"")
                else:
                    p.w(datei, f"Mengenangabe: nur offizielle Bereiche mit Quelle erlaubt (Fachprüfung): \"{t[:60]}\"")
            for s in saetze(t):
                if woerter(s) > SATZ_MAX_WOERTER:
                    p.w(datei, f"Satz mit mehr als {SATZ_MAX_WOERTER} Wörtern: \"{s[:60]}\"")

        # Karten
        karten = l["karten"]
        typen = [k.get("typ") for k in karten]
        if not karten:
            p.f(datei, "keine Karten")
            continue
        if typen[0] != "einstieg":
            p.f(datei, "erste Karte muss 'einstieg' sein")
        if typen[-1] != "zusammenfassung":
            p.f(datei, "letzte Karte muss 'zusammenfassung' sein")
        if typen.count("einstieg") != 1 or typen.count("zusammenfassung") != 1:
            p.f(datei, "genau ein Einstieg und eine Zusammenfassung")
        nq = typen.count("quiz")
        if not QUIZ[0] <= nq <= QUIZ[1]:
            p.f(datei, f"Quiz braucht {QUIZ[0]} bis {QUIZ[1]} Fragen, gefunden {nq}")
        nw = typen.count("wissen")
        if not WISSEN_KARTEN[0] <= nw <= WISSEN_KARTEN[1]:
            p.w(datei, f"ungewöhnlich viele oder wenige Wissenskarten: {nw}")
        # Quiz am Ende vor der Zusammenfassung
        if nq:
            erstes = typen.index("quiz")
            if any(t != "quiz" for t in typen[erstes:-1]):
                p.f(datei, "Quizfragen müssen am Ende vor der Zusammenfassung stehen")

        for i, k in enumerate(karten, 1):
            typ = k.get("typ")
            ort = f"Karte {i} ({typ})"
            if typ not in KARTENTYPEN:
                p.f(datei, f"{ort}: unbekannter Typ")
                continue
            if k.get("gueltig_bis"):
                try:
                    dt.date.fromisoformat(k["gueltig_bis"])
                except ValueError:
                    p.f(datei, f"{ort}: gueltig_bis muss JJJJ-MM-TT sein")
            if typ == "einstieg":
                a = k.get("absaetze") or []
                if len(a) != 2 or not all(x.strip() for x in a):
                    p.f(datei, f"{ort}: genau zwei Absätze")
            elif typ == "wissen":
                a = k.get("absaetze") or []
                if not k.get("titel"):
                    p.f(datei, f"{ort}: titel fehlt")
                if not 1 <= len(a) <= 4:
                    p.f(datei, f"{ort}: ein bis vier Absätze")
                n = sum(woerter(x) for x in a)
                if not WISSEN_WOERTER[0] <= n <= WISSEN_WOERTER[1]:
                    p.w(datei, f"{ort}: {n} Wörter, Ziel {WISSEN_WOERTER[0]} bis {WISSEN_WOERTER[1]}")
                if k.get("studienlage") is not None and k["studienlage"] not in (1, 2, 3):
                    p.f(datei, f"{ort}: studienlage muss 1, 2 oder 3 sein")
                if k.get("studienlage") == 1:
                    txt = " ".join(a).lower()
                    if not re.search(r"deute|hinweis|könnte|möglicherweise|vermut|nicht sicher|unklar", txt):
                        p.w(datei, f"{ort}: Ampel schwach, Aussage als Hinweis formulieren (deutet darauf hin)")
            elif typ == "mythos":
                if not k.get("behauptung") or not k.get("erklaerung"):
                    p.f(datei, f"{ort}: behauptung und erklaerung nötig")
                if k.get("urteil") not in URTEILE:
                    p.f(datei, f"{ort}: urteil muss {sorted(URTEILE)} sein")
                n = woerter(k.get("erklaerung", ""))
                if not MYTHOS_WOERTER[0] <= n <= MYTHOS_WOERTER[1]:
                    p.w(datei, f"{ort}: Erklärung hat {n} Wörter, Ziel {MYTHOS_WOERTER[0]} bis {MYTHOS_WOERTER[1]}")
            elif typ == "schritte":
                s = k.get("schritte") or []
                if not k.get("titel"):
                    p.f(datei, f"{ort}: titel fehlt")
                if not SCHRITTE[0] <= len(s) <= SCHRITTE[1]:
                    p.f(datei, f"{ort}: {SCHRITTE[0]} bis {SCHRITTE[1]} Schritte")
                if any(not x.get("titel") or not x.get("text") for x in s):
                    p.f(datei, f"{ort}: jeder Schritt braucht titel und text")
            elif typ == "quiz":
                art, opt, r = k.get("art"), k.get("optionen") or [], k.get("richtig")
                if not k.get("frage") or not k.get("erklaerung"):
                    p.f(datei, f"{ort}: frage und erklaerung nötig")
                if art == "mc" and len(opt) != 4:
                    p.f(datei, f"{ort}: Multiple Choice braucht vier Optionen")
                elif art == "tf" and opt != ["Wahr", "Falsch"]:
                    p.f(datei, f"{ort}: Wahr oder falsch braucht die Optionen [\"Wahr\", \"Falsch\"]")
                elif art not in ("mc", "tf"):
                    p.f(datei, f"{ort}: art muss mc oder tf sein")
                if not isinstance(r, int) or isinstance(r, bool) or not 0 <= r < max(len(opt), 1):
                    p.f(datei, f"{ort}: richtig muss ein gültiger Index sein")
                if len(set(opt)) != len(opt):
                    p.f(datei, f"{ort}: doppelte Optionen")
            elif typ == "zusammenfassung":
                pk = k.get("punkte") or []
                if not PUNKTE[0] <= len(pk) <= PUNKTE[1]:
                    p.f(datei, f"{ort}: {PUNKTE[0]} bis {PUNKTE[1]} Punkte")

    # Nachfolger müssen existieren
    alle_ids = {i for i, _ in ids}
    for (lid, version), datei in ids.items():
        l = json.load(open(os.path.join(ROOT, datei), encoding="utf-8"))
        nach = l.get("ersetzt_durch")
        if nach and nach not in alle_ids:
            p.f(datei, f"ersetzt_durch verweist auf unbekannte id '{nach}'")

    # Lernpfade
    if os.path.exists(LERNPFADE):
        ziele = {z["id"] for z in themen["ziele"]}
        for lp in json.load(open(LERNPFADE, encoding="utf-8")):
            for lid in lp.get("lektionen", []):
                if lid not in alle_ids:
                    p.f("content/lernpfade.json", f"{lp['id']}: unbekannte Lektion '{lid}'")
            for z in lp.get("ziele", []):
                if z not in ziele:
                    p.f("content/lernpfade.json", f"{lp['id']}: unbekanntes Ziel '{z}'")

    if verbose:
        for m in p.fehler + p.warnungen:
            print(m)
        print(f"\n{len(dateien)} Lektionen geprüft: {len(p.fehler)} Fehler, {len(p.warnungen)} Warnungen.")
    return p


def main():
    streng = "--streng" in sys.argv
    p = pruefe(streng)
    if p.fehler or (streng and p.warnungen):
        sys.exit(1)


if __name__ == "__main__":
    main()
