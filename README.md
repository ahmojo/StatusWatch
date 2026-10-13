# StatusWatch

StatusWatch ist mein Projekt für Modul 324. Die Anwendung soll bis zu zehn öffentliche Websites alle fünf Minuten prüfen. Eine angemeldete Betreiberperson kann Ziele verwalten, Prüfungen starten und die zehn letzten Ergebnisse ansehen.

Die [Dokumentation zu C1, D1 und E1](docs/documentation.md) liegt unter `docs`.

Flask-Grundgerüst, Datenbankmodelle, Anmeldung, Monitorverwaltung, Tests und
PR-Prüfungen sind umgesetzt. HTTP-Prüfungen, Statusanzeige, Docker und Azure
sind noch nicht umgesetzt.

## Lokal starten

Voraussetzungen: Python 3.11 oder neuer und PowerShell.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Vor dem Start muss `SECRET_KEY` in der lokalen `.env` durch einen zufälligen Wert
ersetzt und `OPERATOR_PASSWORD` mit einem eigenen Passwort gesetzt werden.
Ohne diese Werte ist die Anmeldung nicht verfügbar. Die Datei `.env` wird nicht
versioniert.
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

## Anmeldung und Monitorverwaltung

Unter `http://127.0.0.1:5000/` melde ich mich mit dem Betreiberpasswort an.
Ein Passwort reicht, weil ich keine Benutzerverwaltung benötige. Die
Flask-Session speichert die Anmeldung. Abmelden leert die Session.
Die Verwaltung verlangt eine Anmeldung. Flask-WTF prüft den CSRF-Token
bei jedem Formularversand.

Nach der Anmeldung kann ich bis zu zehn Monitore anzeigen, erstellen und
löschen. Namen müssen 1–80 Zeichen lang sein. URLs müssen HTTP oder HTTPS
verwenden. Nur Ports 80 und 443 sind erlaubt. Gleiche URLs werden nach der
Vereinheitlichung abgelehnt. Beim Löschen werden zugehörige Prüfergebnisse
mitgelöscht.

Die Tests prüfen Anmeldung, Zugriffsschutz, CSRF und Monitorverwaltung mit
SQLite. Dabei sind Netzwerkzugriffe gesperrt. Die Verwaltung prüft keine
Websites. PostgreSQL und Deployment habe ich für diese Änderung nicht geprüft.

## Tests und Qualitätskontrolle

Die Entwicklungsabhängigkeiten und lokalen Prüfungen werden so ausgeführt:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
```
