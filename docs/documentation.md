# Dokumentation Modul 324

## Inhaltsverzeichnis

- [C1: Sourcecode- und Artefaktverwaltung](#c1-sourcecode--und-artefaktverwaltung)
- [D1: Automatisierter Integrationsprozess](#d1-automatisierter-integrationsprozess)
- [E1: Automatisierter Deploymentprozess](#e1-automatisierter-deploymentprozess)

## C1: Sourcecode- und Artefaktverwaltung

Ich verwalte den Code mit Git und GitHub. Für die Anmeldung und Monitorverwaltung
habe ich [Issue #7](https://github.com/ahmojo/StatusWatch/issues/7), einen Branch
und [PR #8](https://github.com/ahmojo/StatusWatch/pull/8) erstellt. Ich habe die
Änderungen auf drei Commits verteilt, damit Anmeldung, Monitorverwaltung und
Tests getrennt nachvollziehbar sind. Ein veröffentlichtes Container-Artefakt
gibt es noch nicht.

Für die lokalen Qualitätsprüfungen und die PR-/User-Story-Vorlagen habe ich
[Issue #15](https://github.com/ahmojo/StatusWatch/issues/15) erstellt.

Für Docker und das Container-Artefakt habe ich
[Issue #17](https://github.com/ahmojo/StatusWatch/issues/17) erstellt.
Der Release-Workflow veröffentlicht ein Image ausschliesslich nach GHCR.
Versions-Tag und vollständiger Commit-SHA verweisen auf dasselbe Image;
der Registry-Digest wird in der Actions-Summary festgehalten.
Ein Release-Tag und ein veröffentlichtes Image für diese Änderung fehlen noch.

Für die Azure-Auslieferung habe ich
[Issue #19](https://github.com/ahmojo/StatusWatch/issues/19) erstellt.
Der Release-Build hinterlegt den vollständigen Commit im Image und im
OCI-Label `org.opencontainers.image.revision`.

## D1: Automatisierter Integrationsprozess

GitHub Actions führt bei Pull Requests die gleichen pre-commit-Prüfungen wie
lokal aus, einschliesslich Ruff und pytest mit mindestens 85 % Zeilenabdeckung.
Die Tests prüfen unter anderem Anmeldung, Zugriffsschutz und Monitorverwaltung.
Lokal habe ich mit Python 3.14 und SQLite geprüft:

- `.venv\Scripts\python.exe -m pytest`: 141 Tests bestanden.
- `.venv\Scripts\python.exe -m ruff check .`: keine Fehler.
- `python -m pre_commit run --all-files` in der aktivierten `.venv`: bestanden.
- Zeilenabdeckung: 99,03 %; die Mindestgrenze von 85 % ist erfüllt.

Ich habe die Ablehnung von Leerzeichenfehlern, fehlendem abschliessendem
Zeilenumbruch, Konfliktmarkern und unerwünschten Dateiendungen separat geprüft.
Im Testaufbau werden die SQLite-Verbindungen jetzt nach jedem Test geschlossen.

Für den synchronen HTTP-Prüfer habe ich
[Issue #9](https://github.com/ahmojo/StatusWatch/issues/9) erstellt.
Die Tests ersetzen DNS und Verbindungen und prüfen Adressschutz,
HTTP-Statuscodes, technische Fehler und die Speicherung ohne Antwortkörper.

Für die Ergebnisanzeige und manuelle Prüfung habe ich
[Issue #11](https://github.com/ahmojo/StatusWatch/issues/11) erstellt.
Ich habe Anzeige, die zehn letzten Ergebnisse, UTC-Zeiten, manuelle Prüfungen,
die 30-Sekunden-Pause, Zugriffsschutz und Fehlerdarstellung mit ersetzten
Netzwerkzugriffen geprüft. PostgreSQL und Browserbedienung habe ich nicht geprüft.

Für den geschützten automatischen Aufruf habe ich
[Issue #13](https://github.com/ahmojo/StatusWatch/issues/13) erstellt.
Ich habe Token-Schutz, aktive Monitore, Reihenfolge, Fortsetzung nach Zielfehlern,
den Duplikatschutz und die Workflow-Auslöser lokal geprüft.
Ein echter GitHub-Zeitplanlauf und die PostgreSQL-Schemaänderung sind nicht geprüft.

Der [CI-Lauf zu PR #14](https://github.com/ahmojo/StatusWatch/actions/runs/40287716816)
hat pytest und Ruff erfolgreich ausgeführt. Die neuen pre-commit-Prüfungen
sind bisher nur lokal ausgeführt; ein CI-Nachweis für diese Änderung fehlt noch.

## E1: Automatisierter Deploymentprozess

Ich habe den lokalen Compose-Stack mit Python 3.11 und PostgreSQL 16 gestartet.
Webdienst und Datenbank meldeten `healthy`; `/health` antwortete mit HTTP 200.
Die Anwendung lief als UID 10001 mit genau einem Gunicorn-Worker.

Über die Anmeldung und das Formular habe ich einen Test-Monitor angelegt.
Der geschützte Prüfaufruf speicherte ein Ergebnis für eine blockierte lokale
Adresse; es wurde keine externe Zielseite aufgerufen. Nach Neustart und
Container-Neuerstellung waren Monitor und Ergebnis unverändert und weiterhin
in der Oberfläche sichtbar. Auch nach dem Neubau des finalen Images blieben
die Daten erhalten.

Release-YAML, Shellsyntax und gültige/ungültige Versionsbeispiele habe ich lokal
geprüft. Ein echter GHCR-Push und ein Azure-Deployment wurden nicht ausgeführt.

Ich habe das geänderte Image lokal mit PostgreSQL gestartet. Die Initialisierung
beim Containerstart, Anmeldung, Speicherung, Neustart und Container-Neuerstellung
waren erfolgreich. Bei gestoppter Datenbank antwortete `/health/live` mit 200
und `/health/ready` mit 503. Nach dem Datenbank-Neustart antwortete die
Bereitschaftsprüfung wieder mit 200; Monitor und Ergebnis blieben erhalten.
Der Container lief als UID 10001 mit einem Gunicorn-Worker.

Der vorbereitete Workflow `Deploy tested release` hat einen manuellen Auslöser
auf `main` mit einem stabilen SemVer-Tag. Er verlangt einen erfolgreichen
Release-Lauf für genau diesen Tag und Commit, vergleicht die Digests von
Versions- und SHA-Tag und setzt das vorhandene GHCR-Image per Digest.
Er baut kein Image. Die Prüfung wartet auf den erwarteten laufenden Commit
und eine erfolgreiche Datenbankabfrage. Vorherige Image-Konfiguration, Version,
Commit, Digest und Prüfzeit in UTC stehen in der Actions-Summary.
Ein manueller Rollback verwendet denselben Workflow mit dem vorherigen
getesteten Tag; die Datenbank wird dabei nicht zurückgesetzt.

Die GitHub-Umgebung `production` benötigt die Variablen `AZURE_CLIENT_ID`,
`AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP` und
`AZURE_WEBAPP_NAME`. Für die noch einzurichtende OIDC-Verbindung ist das Vertrauen
auf diese Umgebung dieses Repositories und die Rolle auf die Web-App begrenzt.
Datenbankzugang und
Anwendungs-Secrets bleiben in der Azure-Konfiguration. Für den einzelnen
Container ist `WEBSITES_PORT=8000` erforderlich; das GHCR-Paket muss öffentlich
lesbar sein. Es werden keine Azure-Passwörter oder Publishing-Profile in GitHub
benötigt.

YAML und Shellsyntax habe ich geprüft. Mit ersetzten externen Aufrufen habe ich
acht Workflow-Fälle ausgeführt: Erfolg, ungültige Version, fehlender Release-Lauf,
abweichender Digest, abweichende Azure-Konfiguration, falscher laufender Commit,
Datenbankausfall und verzögerter Start. Die erwartete Annahme oder Ablehnung
trat jeweils ein. Das ersetzt keinen echten Azure-Deploymentlauf.

Noch offen sind OIDC-Konfiguration, Veröffentlichung der Images und der echte
Azure-Nachweis mit öffentlichem Testziel, Neustart-Persistenz und Rollback.
Die abschliessende Prüfung gegen C1, D1 und E1 ist deshalb noch nicht erfüllt.
