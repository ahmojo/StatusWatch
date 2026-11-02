# StatusWatch

Projekt für Modul 324: Bis zu zehn öffentliche Websites alle fünf Minuten
prüfen, Status und Antwortzeit speichern und die zehn letzten Ergebnisse anzeigen.
Die Verwaltung ist passwortgeschützt.

[Live-App](https://lb-324.ahmet-ilhan.tech/) ·
[Dokumentation C1, D1 und E1](docs/documentation.md)

## Lokal mit Docker starten

Voraussetzung: Docker mit Compose.

```powershell
Copy-Item .env.example .env
```

In `.env` eigene Werte für `SECRET_KEY`, `OPERATOR_PASSWORD`, `SCHEDULER_TOKEN`
und `POSTGRES_PASSWORD` setzen. `DATABASE_URL` muss auf Host `db` zeigen und
zum Datenbankpasswort passen. Standard für Datenbank und Benutzer: `statuswatch`.
Sonderzeichen im URL-Passwort müssen URL-kodiert sein. `.env` bleibt lokal.

```powershell
docker compose up --build -d --wait
Invoke-RestMethod http://127.0.0.1:8000/health
docker compose ps
```

Die App läuft unter `http://127.0.0.1:8000/`. `WEB_PORT` ändert den lokalen Port.
Das Volume `database` erhält Daten bei Neustart und Container-Neuerstellung.
`docker compose down` behält es; `docker compose down -v` löscht die Daten.

## Entwicklung ohne Docker

Voraussetzungen: Python ab 3.11, PowerShell und eine laufende PostgreSQL-Datenbank.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

`SECRET_KEY` und `OPERATOR_PASSWORD` setzen; `DATABASE_URL` auf die eigene
PostgreSQL-Datenbank ausrichten. Danach:

```powershell
flask --app statuswatch:create_app init-db
flask --app statuswatch:create_app run
```

Die App läuft unter `http://127.0.0.1:5000/`. `flask run` startet keinen Scheduler.
`init-db` legt fehlende Tabellen an. Für bestehende Datenbanken ohne
`scheduled_period` zuerst [die Migration](migrations/001_scheduled_period.sql)
ausführen; `init-db` aktualisiert bestehende Tabellen nicht.

## Bedienung und Prüfungen

Nach der Anmeldung lassen sich Monitore erstellen, prüfen und löschen.
Die Detailseite zeigt die zehn letzten Ergebnisse mit UTC-Zeit und Antwortzeit.
Zwischen manuellen Prüfungen gelten 30 Sekunden Pause. Löschen entfernt auch
die Ergebnisse des Monitors. Formulare sind durch CSRF-Token geschützt.

Ziele müssen HTTP/HTTPS auf Port 80 oder 443 verwenden. Doppelte URLs und
private Netzwerkadressen werden abgelehnt. Der Prüfer arbeitet nacheinander,
mit fünf Sekunden Socket-Timeout und ohne Weiterleitungen oder Wiederholungen.
HTTP 200–399 gilt als erfolgreich; technische Fehler werden als Kategorie gespeichert.

Im Container startet `python -m statuswatch.server` einen Gunicorn-Worker und
prüft aktive Monitore an den UTC-Fünf-Minuten-Grenzen. Verpasste Zeiträume
werden nicht nachgeholt. Endet der Webprozess, endet auch der Container.

`POST /internal/checks` verlangt `Authorization: Bearer <SCHEDULER_TOKEN>`.
Fehlende Token-Konfiguration ergibt 503, ein falsches Token 401. Eine
Datenbankregel verhindert doppelte automatische Ergebnisse im selben Zeitraum.

Für den optionalen GitHub-Workflow `Manual monitor checks` braucht es das
Secret `SCHEDULER_TOKEN` und die Variable `STATUSWATCH_URL` mit der HTTPS-Basisadresse.
Der Container-Scheduler liest sein Token aus der Anwendungsumgebung.

## Release und Deployment

Ein stabiler Versions-Tag wie `v0.1.4` startet:

1. pytest und Ruff.
2. Build und Veröffentlichung unter `ghcr.io/ahmojo/statuswatch`.
3. Nach erfolgreichem Release: Deployment des Images nach Azure.

Das Image erhält Versions- und SHA-Tag; die Workflow-Summary nennt den Digest.
Der Deployment-Workflow prüft Commit, main-Zugehörigkeit und übereinstimmende
Digests. Anschliessend prüft er den laufenden Commit und die Datenbank.
Branch-Pushes lösen kein Deployment aus.

Am 2. November 2026 lief die ganze Kette für `v0.1.4` erfolgreich:
[Release](https://github.com/ahmojo/StatusWatch/actions/runs/41453995111)
und [automatisches Azure-Deployment](https://github.com/ahmojo/StatusWatch/actions/runs/41454140471).

Azure-Zugriff erfolgt über OIDC und die GitHub-Umgebung `production`.
Dort liegen `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`,
`AZURE_RESOURCE_GROUP` und `AZURE_WEBAPP_NAME` als Variablen.
Anwendungs-Secrets bleiben in Azure. Bestehende Umgebungsfreigaben gelten weiter.

Für Rollbacks bleibt der manuelle Start mit einem älteren getesteten Tag.
Er setzt nur das Image zurück, nicht das Datenbankschema. Ein fehlgeschlagener
Healthcheck löst keinen automatischen Rollback aus.

## Tests

In der aktivierten virtuellen Umgebung:

```powershell
python -m pre_commit install
python -m pre_commit run --all-files
python -m pytest
python -m ruff check .
```

GitHub Actions führt dieselben pre-commit-Prüfungen bei Pull Requests aus.
pytest verlangt mindestens 85 % Zeilenabdeckung. Tests verwenden SQLite und
ersetzen externe Dienste; sie belegen keinen vollständigen Azure-Browserablauf.
Die Leerzeichen- und Dateiende-Hooks können Dateien korrigieren: Diff kontrollieren.

`/health/live` meldet Webprozess und Image-Commit, `/health/ready` prüft die
Datenbank mit `SELECT 1` (503 bei Fehler). `/health` bleibt als einfacher Status verfügbar.
