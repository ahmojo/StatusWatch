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
Tests getrennt nachvollziehbar sind. Ein Container-Artefakt gibt es noch nicht.

## D1: Automatisierter Integrationsprozess

GitHub Actions soll bei Pull Requests pytest und Ruff ausführen. Die Tests
prüfen unter anderem Anmeldung, Zugriffsschutz und Monitorverwaltung.
Lokal habe ich mit Python 3.14 und SQLite geprüft:

- `.venv\Scripts\python.exe -m pytest`: 137 Tests bestanden.
- `.venv\Scripts\python.exe -m ruff check .`: keine Fehler.

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

Der [CI-Lauf zu PR #8](https://github.com/ahmojo/StatusWatch/actions/runs/38459979902)
wurde wegen einer Zahlungs- oder Ausgabenlimit-Sperre nicht gestartet.
Ein erfolgreicher CI-Nachweis fehlt deshalb noch.

## E1: Automatisierter Deploymentprozess

Ein Deployment ist noch nicht umgesetzt und wurde nicht geprüft.
