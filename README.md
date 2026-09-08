# StatusWatch

StatusWatch ist mein Projekt für Modul 324. Die Anwendung soll bis zu zehn öffentliche Websites alle fünf Minuten prüfen. Eine angemeldete Betreiberperson kann Ziele verwalten, Prüfungen starten und die zehn letzten Ergebnisse ansehen.

Phase 1 enthält nur die Planung:

- [Anforderungen](docs/requirements.md)
- [Entscheidungen](docs/decisions.md)
- [Backlog](docs/backlog.md)
- [Architektur](docs/architecture.md)
- [Sicherheit](docs/security.md)
- [Nachweisplan C1, D1 und E1](docs/evidence-plan.md)

Anwendungscode, Tests, GitHub Actions und Azure-Ressourcen folgen.

## Lokal starten

Voraussetzungen: Python 3.11 oder neuer und PowerShell.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
flask --app statuswatch:create_app run
```

Vor dem Start muss `SECRET_KEY` in der lokalen `.env` durch einen zufälligen Wert ersetzt werden. Die Datei `.env` wird nicht versioniert.

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
