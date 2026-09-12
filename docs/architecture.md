# Architektur

## Aufbau

```text
Browser
  │ HTTPS
  ▼
Azure App Service: ein StatusWatch-Container
  ├─ Flask und Gunicorn
  ├─ Fünf-Minuten-Scheduler
  ├─ HTTP-Prüfdienst ──▶ öffentliche Ziele
  └─ SQLAlchemy ──TLS──▶ Azure PostgreSQL

GitHub Actions ──OIDC──▶ Azure
  ├─ pytest und Docker-Build
  ├─ SHA-Image ──▶ Azure Container Registry
  └─ Deployment ──▶ App Service
```

Ich verwende eine Flask Application Factory mit Einstellungen für Test, lokal und Produktion. Blueprints trennen Anmeldung, Ziele, Status und Health-Endpunkte. Flask beschreibt dieses Muster unter https://flask.palletsprojects.com/en/stable/patterns/appfactories/.

## Datenmodell

| Tabelle | Felder | Regeln |
|---|---|---|
| `monitors` | ID, Name, URL, Aktivstatus, Intervall, Erstellungs- und Änderungszeit | URL eindeutig, Name 1–80 Zeichen, Intervall mindestens 60 Sekunden |
| `check_results` | ID, Monitor-ID, Prüfzeit, Statuscode, Antwortzeit, Erfolg, Fehlerkategorie | Cascade beim Löschen; Fehlerkategorie bei erfolgloser Prüfung erforderlich |

Ein Index auf Monitor-ID und Prüfzeit beschleunigt die Historie. PostgreSQL wird
über `DATABASE_URL` konfiguriert. Tests erhalten jeweils eine neue
SQLite-In-Memory-Datenbank. `flask --app statuswatch:create_app init-db` erzeugt
das Schema reproduzierbar. Der Schutz vor doppelten Scheduler-Einträgen folgt
mit der Scheduler-Umsetzung.

Prüfergebnisse werden unbegrenzt aufbewahrt. Beim Löschen eines Monitors löscht
die Fremdschlüsselbeziehung seine Ergebnisse mit.

## Scheduler

Der MVP läuft mit einer App-Service-Instanz und einem Gunicorn-Worker. Der Scheduler prüft alle fünf Minuten. Der Datenbankschlüssel schützt vor Doppelläufen. Hochverfügbarkeit gehört nicht zum MVP.

## Lokal, CI und Deployment

Docker Compose startet Webanwendung und PostgreSQL. Der Webdienst wartet auf die Datenbank, führt Migrationen aus und startet Gunicorn.

Pull Requests führen pytest und den Docker-Build aus. Auf `main` veröffentlicht GitHub Actions ein SHA-Image in Azure Container Registry, aktualisiert App Service und prüft `/health/ready`. OIDC liefert ein kurzlebiges Azure-Token und gilt nur für Repository, `main` und Deployment-Environment.

Quellen:

- https://learn.microsoft.com/en-us/azure/app-service/quickstart-custom-container
- https://learn.microsoft.com/en-us/azure/postgresql/development/webapp-server-vnet
- https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure

## Rollback und Grenzen

Bei einem Fehler wird App Service auf das vorherige SHA-Image zurückgestellt. Migrationen müssen mit der vorherigen Version funktionieren. Destruktive Migrationen gehören nicht zum MVP.

Der MVP umfasst eine Instanz und höchstens zehn Ziele. Während eines App-Ausfalls gibt es keine Prüfungen. GitHub Actions automatisiert die Anwendungsauslieferung; die Azure-Ressourcen werden einmalig eingerichtet und dokumentiert.
