# StatusWatch

StatusWatch ist mein Projekt für Modul 324. Die Anwendung soll bis zu zehn öffentliche Websites alle fünf Minuten prüfen. Eine angemeldete Betreiberperson kann Ziele verwalten, Prüfungen starten und die zehn letzten Ergebnisse ansehen.

Die [Dokumentation zu C1, D1 und E1](docs/documentation.md) liegt unter `docs`.

Flask-Grundgerüst, Datenbankmodelle, Anmeldung, Monitorverwaltung, Tests und
PR-Prüfungen, synchrone HTTP-Prüfung, Ergebnisanzeige und der Aufruf durch GitHub Actions
sind umgesetzt. Docker und Azure sind noch nicht umgesetzt.

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
SQLite. Netzwerkzugriffe werden in Tests gesperrt oder ersetzt.
PostgreSQL und Deployment habe ich für diese Änderung nicht geprüft.

Die Übersicht zeigt pro Monitor den letzten Zustand, die Prüfzeit in UTC und die
Antwortzeit in Millisekunden. Ohne Ergebnis erscheint «Noch nicht geprüft».
Ein Klick auf den Namen öffnet höchstens zehn Ergebnisse, neuestes zuerst.
Mit «Jetzt prüfen» starte ich dort den vorhandenen synchronen Prüfer.
Nach der Prüfung wird die Detailseite mit dem neuen Ergebnis angezeigt.
Pro Monitor gelten 30 Sekunden Pause ab der letzten Prüfzeit, auch nach Fehlern.
Während der Pause startet keine neue Prüfung; die Seite zeigt einen Hinweis.

## Automatische Prüfung

`POST /internal/checks` verlangt `Authorization: Bearer <SCHEDULER_TOKEN>`.
Das separate Token wird in der Anwendungsumgebung als `SCHEDULER_TOKEN` gesetzt.
Ohne Konfiguration antwortet der Endpunkt mit 503, bei falschem oder fehlendem
Token mit 401. Er verwendet keine Anmeldung per Browser-Session und ist vom
CSRF-Schutz ausgenommen; die übrigen Formulare behalten ihren CSRF-Schutz.

Der Aufruf prüft alle aktiven Monitore nacheinander mit dem vorhandenen Prüfer.
Zielfehler werden gespeichert und stoppen die übrigen Prüfungen nicht.
Der UTC-Zeitpunkt beim Eingang des Aufrufs bestimmt den Fünf-Minuten-Zeitraum
für alle Ergebnisse dieses Aufrufs. Bereits gespeicherte automatische Ergebnisse
dieses Zeitraums werden übersprungen. `UNIQUE (monitor_id, scheduled_period)`
verhindert doppelte Speicherung auch bei gleichzeitigen Aufrufen.
Manuelle Ergebnisse haben `scheduled_period = NULL` und bleiben unabhängig.

Für eine neue Datenbank genügt weiterhin `flask --app statuswatch:create_app init-db`.
Bei einer bestehenden PostgreSQL-Datenbank muss vor dem Start dieser Version
einmalig [migrations/001_scheduled_period.sql](migrations/001_scheduled_period.sql)
ausgeführt werden. `init-db` aktualisiert vorhandene Tabellen nicht.

Im GitHub-Repository unter **Settings → Secrets and variables → Actions** werden
das Secret `SCHEDULER_TOKEN` mit demselben Wert wie in der Anwendung und die
Variable `STATUSWATCH_URL` mit der öffentlich erreichbaren HTTPS-Basisadresse
ohne Endpunktpfad benötigt. Tokenwerte gehören nicht ins Repository.
Der Workflow `Scheduled monitor checks` ruft den Endpunkt alle fünf Minuten auf
und lässt sich auch über `workflow_dispatch` starten. Seine gemeinsame
`concurrency`-Gruppe verhindert parallele Workflow-Läufe; laufende Aufrufe werden
nicht abgebrochen. Der Workflow muss dafür auf `main` liegen.

GitHub-Zeitpläne sind nicht sekundengenau garantiert. Läufe können sich verzögern
oder bei hoher Last ausfallen; versäumte Zeiträume werden nicht nachgeholt.
Siehe [GitHub-Dokumentation zum schedule-Auslöser](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
Ein erreichbares Deployment und eingerichtete Secrets sind Voraussetzung;
einen echten zeitgesteuerten Lauf habe ich noch nicht geprüft.

## Tests und Qualitätskontrolle

`statuswatch.checks.check_monitor(monitor)` prüft einen gespeicherten Monitor und
speichert ein `CheckResult`. Die Funktion benötigt einen Flask-Anwendungskontext.
Sie erlaubt HTTP/HTTPS auf Ports 80/443 und verbindet erst, wenn alle aufgelösten
IP-Adressen öffentlich sind. Der Socket-Timeout beträgt fünf Sekunden.
Weiterleitungen und Wiederholungen werden nicht ausgeführt; der Antwortkörper
wird nicht gelesen. Statuscodes 200–399 gelten als erfolgreich.
Fehler werden nur als `invalid_url`, `blocked_address`, `dns`, `timeout`, `tls`,
`connection` oder `http_status` gespeichert und in der Oberfläche mit einer
kurzen Fehlermeldung angezeigt.

Die Entwicklungsabhängigkeiten und lokalen Prüfungen werden so ausgeführt:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
```
