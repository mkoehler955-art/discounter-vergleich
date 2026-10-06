# Discounter-Vergleich – Live-Version

## Architektur
- Android-App (Kotlin)
- FastAPI-Backend
- SQLite für zwischengespeicherte Angebote
- Händler-Adapter/Quellen für ALDI Nord, Lidl, PENNY, Netto und NORMA
- `/refresh` aktualisiert die Daten
- `/offers?q=milch` liefert die Suchergebnisse

## Backend lokal starten
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Android
Das Projekt unter `android/` in Android Studio öffnen.
Für einen echten physischen Samsung muss `apiBase` in MainActivity.kt auf die erreichbare
HTTPS-Adresse des eigenen Backends geändert werden. `10.0.2.2` funktioniert nur für den
Android-Emulator.

## Produktionshinweis
Die Händlerseiten sind dynamisch und ändern ihre Struktur. Die mitgelieferten Parser sind
eine robuste erste Grundlage, aber vor einem öffentlichen Release müssen die fünf Adapter
gegen die jeweils aktuelle Datenstruktur getestet und ggf. angepasst werden. Regional-,
App- und Filialpreise müssen getrennt behandelt werden. Das Backend sollte mit HTTPS,
Rate-Limits und einem Scheduler (z.B. Cron) betrieben werden.

## Aktuelle Quellen
ALDI Nord: https://www.aldi-nord.de/prospekte/aldi-aktuell.html
Lidl: https://www.lidl.de/c/online-prospekte/s10005610
PENNY: https://www.penny.de/angebote
Netto: https://netto.de/angebote/
NORMA: https://www.norma-online.de/de/angebote/
