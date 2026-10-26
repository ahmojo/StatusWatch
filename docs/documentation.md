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

## D1: Automatisierter Integrationsprozess

GitHub Actions führt bei Pull Requests die gleichen pre-commit-Prüfungen wie
lokal aus, einschliesslich Ruff und pytest mit mindestens 85 % Zeilenabdeckung.
Die Tests prüfen unter anderem Anmeldung, Zugriffsschutz und Monitorverwaltung.
Lokal habe ich mit Python 3.14 und SQLite geprüft:

- `.venv\Scripts\python.exe -m pytest`: 137 Tests bestanden.
- `.venv\Scripts\python.exe -m ruff check .`: keine Fehler.
- `python -m pre_commit run --all-files` in der aktivierten `.venv`: bestanden.
- Zeilenabdeckung: 98,99 %; die Mindestgrenze von 85 % ist erfüllt.

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
