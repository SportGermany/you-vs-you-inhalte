"""Hilfen, um Lektionen kompakt in Python zu schreiben und als JSON abzulegen."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HINWEIS = ("Dies ist Bildung, keine medizinische Beratung. "
           "Sprich bei Beschwerden oder Medikamenten mit Ärztin oder Arzt.")
STAND = "2026-10"


def Q(titel, herausgeber, url, abgerufen=""):
    return {"titel": titel, "herausgeber": herausgeber, "url": url, "abgerufen": abgerufen}


def lektion(id, welt, unterthema, titel, minuten, studienlage, quellen, tags, einstieg, wissen,
            mythos, schritte, quiz, punkte, beachten=None, zeitlos=True, gueltig_von=None, gueltig_bis=None,
            essstoerung=False):
    """
    wissen: Liste von (titel, [absaetze], merke|None, studienlage|None)
    mythos: (behauptung, urteil, erklaerung) oder None
    schritte: (titel, [(titel, text), ...]) oder None
    quiz: Liste von (frage, "mc"|"tf", optionen|None, richtig, erklaerung)
    beachten: Absätze für die Karte "Das solltest du beachten" (Supplements)
    """
    karten = [{"typ": "einstieg", "absaetze": einstieg}]
    for t, a, m, s in wissen:
        k = {"typ": "wissen", "titel": t, "absaetze": a}
        if m:
            k["merke"] = m
        if s:
            k["studienlage"] = s
        karten.append(k)
    if beachten:
        karten.append({"typ": "wissen", "titel": "Das solltest du beachten", "absaetze": beachten})
    if mythos:
        karten.append({"typ": "mythos", "behauptung": mythos[0], "urteil": mythos[1], "erklaerung": mythos[2]})
    if schritte:
        karten.append({"typ": "schritte", "titel": schritte[0],
                       "schritte": [{"titel": a, "text": b} for a, b in schritte[1]]})
    for frage, art, opt, richtig, erkl in quiz:
        karten.append({"typ": "quiz", "frage": frage, "art": art,
                       "optionen": ["Wahr", "Falsch"] if art == "tf" else opt,
                       "richtig": richtig, "erklaerung": erkl})
    if unterthema == "stoffwechsel-abnehmen":
        punkte = punkte + ["Bei Verdacht auf eine Essstörung hol dir ärztliche Hilfe."]
    karten.append({"typ": "zusammenfassung", "punkte": punkte})

    l = {
        "id": id, "version": 1, "themenwelt": welt, "unterthema": unterthema, "titel": titel,
        "minuten": minuten, "studienlage": studienlage, "zeitlos": zeitlos,
        "gueltig_von": gueltig_von, "gueltig_bis": gueltig_bis, "ersetzt_durch": None,
        "stand": STAND, "pruefstatus": "entwurf", "quellen": quellen,
    }
    if welt == "gesundheit":
        l["hinweis"] = HINWEIS
    l["tags"] = tags
    l["karten"] = karten
    return l


def schreibe(lektionen):
    for l in lektionen:
        ordner = os.path.join(ROOT, "content", "lektionen", l["themenwelt"])
        os.makedirs(ordner, exist_ok=True)
        pfad = os.path.join(ordner, l["id"] + ".json")
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(json.dumps(l, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(lektionen)} Lektionen geschrieben.")
