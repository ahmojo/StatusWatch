# StatusWatch

StatusWatch ist mein Projekt für Modul 324. Die Anwendung soll bis zu zehn öffentliche Websites alle fünf Minuten prüfen. Eine angemeldete Betreiberperson kann Ziele verwalten, Prüfungen starten und die zehn letzten Ergebnisse ansehen.

Die Planungsunterlagen liegen unter `docs`:

- [Anforderungen](docs/requirements.md)
- [Entscheidungen](docs/decisions.md)
- [Backlog](docs/backlog.md)
- [Architektur](docs/architecture.md)
- [Nachweisplan C1, D1 und E1](docs/evidence-plan.md)

Flask-Grundgerüst, Datenbankmodelle, Tests und PR-Prüfungen sind umgesetzt.
Oberfläche, Monitoring, Docker und Azure folgen in späteren Phasen.

## Lokal starten

Voraussetzungen: Python 3.11 oder neuer und PowerShell.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Vor dem Start muss `SECRET_KEY` in der lokalen `.env` durch einen zufälligen Wert ersetzt werden. Die Datei `.env` wird nicht versioniert.
`DATABASE_URL` muss auf die lokale PostgreSQL-Datenbank zeigen. Danach werden die
Tabellen reproduzierbar initialisiert und die Anwendung gestartet:

```powershell
flask --app statuswatch:create_app init-db
flask --app statuswatch:create_app run
```

Die laufende Anwendung lässt sich lokal prüfen:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Erwartete Antwort:

```json
{"status":"ok"}
```

## Tests und Qualitätskontrolle

Die Entwicklungsabhängigkeiten und lokalen Prüfungen werden so ausgeführt:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
```
