# Automatische Lektionen-Erstellung

Diese Anleitung ist für die Arbeits-Sitzung, die stündlich neue Lektionen schreibt.
Alles passiert in diesem Repository (`SportGermany/you-vs-you-inhalte`, Branch `claude/new-session-12ebf4`).
Hier liegen nur Lerninhalte. Niemals App-Code, Schlüssel oder persönliche Daten hierher kopieren.

Die App lädt `index.json` und die `paket-*.json` aus dem Hauptverzeichnis automatisch im WLAN.

## Ziel

3500 Lektionen insgesamt. Den aktuellen Stand zeigt `python3 content-tools/stand.py`.
Ist das Ziel erreicht, schreibt der Lauf nichts mehr.

## Ablauf eines Laufs

1. Neuesten Stand holen: `git fetch origin claude/new-session-12ebf4 && git checkout -B claude/new-session-12ebf4 origin/claude/new-session-12ebf4`
2. `python3 content-tools/stand.py --naechste 7` zeigt die Unterthemen mit der größten Lücke und die vorhandenen Titel.
3. Neue Datei `content-tools/batches/batchNNN.py` anlegen (NNN = nächste freie Nummer, dreistellig, zum Beispiel `batch002.py`).
   Vorbild ist `batch01.py`, Hilfsfunktionen stehen in `werkzeug.py`.
   - Etwa 21 Lektionen, verteilt auf die Unterthemen mit der größten Lücke.
   - IDs eindeutig: `<kürzel>-b<NNN>-<laufende Nummer>`, zum Beispiel `schlaf-b007-03`.
   - Keine Titel wiederholen, auch nicht sinngemäß. Titel immer als Frage.
4. `python3 content-tools/batches/batchNNN.py` ausführen.
5. `python3 content-tools/validate.py` muss **0 Fehler** melden. Fehler beheben, Warnungen sind erlaubt.
6. `python3 content-tools/build_pack.py --entwuerfe` baut die Pakete im Hauptverzeichnis neu.
7. Alles committen („Batch NNN: X neue Lektionen“) und pushen: `git push origin claude/new-session-12ebf4`.
   Bei Konflikt: `git pull --rebase origin claude/new-session-12ebf4`, Pakete mit Schritt 6 neu bauen, erneut committen und pushen.

## Inhaltsregeln (aus dem Konzept)

- Deutsch, Anrede du, kurze Sätze unter 25 Wörtern, Fachbegriffe beim ersten Auftreten erklären.
- Aufbau: Einstieg (zwei kurze Absätze, Alltagsszene), 2 bis 4 Wissenskarten, optional Mythos- und Schritt-Karte, 3 bis 5 Quizfragen, Zusammenfassung mit 3 bis 5 Punkten.
- Wissenskarten möglichst 40 bis 90 Wörter.
- Multiple Choice immer mit vier Optionen. Wahr oder falsch mit `"tf"`.
- Sachlich, keine Panikmache, keine Heilversprechen, keine Superlative.
- Nur Fakten, bei denen du sicher bist. Im Zweifel weglassen.
- Gesundheit:
  - `studienlage` (1 bis 3) ist Pflicht. Schwache Studienlage nur als Hinweis formulieren („deutet darauf hin“).
  - Keine individuellen Dosierungen, keine Aufforderung, etwas einzunehmen. Mengen nur als offizielle Richtwerte mit Quelle.
  - Supplements: Parameter `beachten=[...]` für die Karte „Das solltest du beachten“ (Risiken, Wechselwirkungen).
  - Abnehmen: keine Kalorienziele, keine Crash-Diäten. Der Hinweis auf Essstörungen wird automatisch ergänzt.
- Zeitgebundene Inhalte (Amtsinhaber, Preise, Gesetze, aktuelle Zahlen, Geopolitik): `zeitlos=False` und `gueltig_bis` setzen.
- Quellen: offizielle Stellen oder Fachgesellschaften (zum Beispiel DGE, BfR, EFSA, WHO, bpb, Destatis, Verbraucherzentrale, NASA, ESA, Umweltbundesamt).
  Nur Adressen, bei denen du sicher bist, dass es sie gibt. Im Zweifel die Startseite der Stelle. `abgerufen` bleibt leer.
- `pruefstatus` bleibt `entwurf`.
