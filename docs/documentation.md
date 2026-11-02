# Dokumentation Modul 324

Stand: 2. November 2026.

## Inhaltsverzeichnis

- [C1: Sourcecode- und Artefaktverwaltung](#c1-sourcecode--und-artefaktverwaltung)
- [D1: Automatisierter Integrationsprozess](#d1-automatisierter-integrationsprozess)
- [E1: Automatisierter Deploymentprozess](#e1-automatisierter-deploymentprozess)

## C1: Sourcecode- und Artefaktverwaltung

Die Entwicklung folgt dem Ablauf Issue → Branch → Commits → Pull Request → Merge.
Beispiel: [Issue #7](https://github.com/ahmojo/StatusWatch/issues/7) beschreibt die
Anmeldung und Monitorverwaltung; [PR #8](https://github.com/ahmojo/StatusWatch/pull/8)
enthält Umsetzung und Tests.

Das ausführbare Artefakt ist ein Container unter `ghcr.io/ahmojo/statuswatch`.
Versions-Tag, Commit-SHA und Image-Digest ordnen eine Veröffentlichung dem Code zu.
Azure verwendet den Digest, damit genau das veröffentlichte Image läuft.
Der [Release v0.1.4](https://github.com/ahmojo/StatusWatch/actions/runs/41453995111)
vom 2. November 2026 gehört zu Commit
`a942b90c73e38e2a034a8147f760fd265576f7a7`.

**Eigenleistung:** Ich habe die Anforderungen für StatusWatch festgelegt und
die Entwicklung über Issues, Branches und Pull Requests gesteuert. Den Code
habe ich mit KI erstellt, die Änderungen reviewt und zur Übernahme freigegeben.

## D1: Automatisierter Integrationsprozess

GitHub Actions führt bei Pull Requests pre-commit mit Ruff und pytest aus.
Vor einem Release laufen pytest und Ruff erneut. Fehler oder eine
Zeilenabdeckung unter 85 % verhindern die Veröffentlichung.

Der Test `test_manual_check_uses_checker_and_displays_one_saved_result` in
[tests/test_results.py](../tests/test_results.py) prüft eine konkrete Anforderung:
Eine manuelle Prüfung muss ein Ergebnis speichern und anzeigen. Der Test
verbindet Formular, Prüfer, SQLite-Datenbank und Template. DNS und Zielverbindung
sind ersetzt.

Der [CI-Lauf zu PR #23](https://github.com/ahmojo/StatusWatch/actions/runs/40531514956)
war erfolgreich. Lokale Ergebnisse vom 2. November 2026 mit Python 3.14:

| Prüfung | Ergebnis |
|---|---|
| `python -m pytest -p no:cacheprovider` | 157 Tests bestanden, 98,57 % Coverage |
| `python -m ruff check . --no-cache` | bestanden |
| `python -m pre_commit run --all-files` | bestanden |
| actionlint 1.7.12, ohne ShellCheck/Pyflakes | vier Workflow-Dateien bestanden |

Neun Deploymenttests prüfen Release-Auflösung und Fehlerfälle mit simulierten
Git- und Registry-Antworten. Den Azure-Ablauf haben wir zusätzlich live geprüft
(siehe E1).

**Eigenleistung:** Ich habe den mit KI erstellten Code reviewt, die
Testergebnisse geprüft und die Anwendung im Browser getestet. Trotz
erfolgreicher GitHub-Läufe habe ich festgestellt, dass die Monitorprüfungen
nicht alle fünf Minuten liefen. Ich habe die Ursache mit KI untersucht,
die Korrektur veranlasst und das Verhalten anschliessend erneut überprüft.

## E1: Automatisierter Deploymentprozess

StatusWatch läuft als Container in Azure App Service mit PostgreSQL.
Der Container prüft die Monitore alle fünf Minuten. Der
[Deployment-Lauf für v0.1.4](https://github.com/ahmojo/StatusWatch/actions/runs/41454140471)
startete am 2. November 2026 nach dem erfolgreichen Release automatisch über
`workflow_run` und war erfolgreich.

Der Ablauf bei einem neuen Versions-Tag:

1. Versions-Tag pushen: Tests und Container-Veröffentlichung starten.
2. Erfolgreicher Release: `workflow_run` startet das Deployment.
3. Der Workflow prüft Release-Commit, main-Zugehörigkeit und Image-Digest.
4. Azure übernimmt das Image; Healthchecks prüfen Commit und Datenbank.

Azure-Zugriff erfolgt über OIDC; Secrets bleiben ausserhalb des Repositories.
Für einen Rollback wird eine frühere getestete Version erneut ausgeliefert.

Am 2. November 2026 antworteten [Loginseite](https://lb-324.ahmet-ilhan.tech/),
[/health/live](https://lb-324.ahmet-ilhan.tech/health/live) und
[/health/ready](https://lb-324.ahmet-ilhan.tech/health/ready) mit HTTP 200.
Nach dem Deployment entsprach der laufende Commit `v0.1.4`;
die Datenbankabfrage war erfolgreich.

Am 2. November 2026 wurde die Azure-Web-App neu gestartet. Alle drei Monitore
und ihre vor dem Neustart zuletzt gespeicherten Ergebnisse blieben erhalten.
Anschliessend waren der [Rollback auf v0.1.3](https://github.com/ahmojo/StatusWatch/actions/runs/41458256143)
und die [Wiederherstellung von v0.1.4](https://github.com/ahmojo/StatusWatch/actions/runs/41458583933)
erfolgreich. Nach beiden Wechseln stimmte der laufende Commit; Anmeldung,
Datenbank und der Vergleich mit den zuvor gespeicherten Daten waren erfolgreich.

**Eigenleistung:** Ich habe die Azure-Lösung unter Berücksichtigung der Kosten
ausgewählt und Einrichtung sowie Deployment mit KI umgesetzt. Wegen des
unregelmässigen GitHub-Zeitplans habe ich entschieden, den Scheduler im
Anwendungscontainer auszuführen. Für Veröffentlichungen habe ich den Ablauf
über Versions-Tags gewählt: Tests, Container-Veröffentlichung und anschliessend
automatisches Deployment nach Azure. Den vollständigen Ablauf haben wir mit
`v0.1.4` erfolgreich überprüft.
