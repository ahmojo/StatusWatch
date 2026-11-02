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
Der [Release v0.1.3](https://github.com/ahmojo/StatusWatch/actions/runs/40531933574)
vom 27. Oktober 2026 gehört zu Commit
`b775b00c7cc06d8c1b7d7c2555ae9e1380c25366`.

**Eigenleistung selbst ergänzen:** Eigene Arbeit am Beispiel-PR, Verantwortung
und Entscheidung für den Entwicklungsablauf beschreiben.

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

Neun neue Deploymenttests prüfen Release-Auflösung und Fehlerfälle mit ersetzten
Git-/Registry-Befehlen. Die Tests belegen keinen echten Azure-Ablauf.

**Eigenleistung selbst ergänzen:** Eigenen Beitrag zu Tests und CI benennen;
einen Test und den damit erkannten Fehler erklären.

## E1: Automatisierter Deploymentprozess

StatusWatch läuft als Container in Azure App Service mit PostgreSQL.
Der Container prüft die Monitore alle fünf Minuten. Der
[Deployment-Lauf für v0.1.3](https://github.com/ahmojo/StatusWatch/actions/runs/40532169194)
war am 27. Oktober 2026 erfolgreich.

Der Ablauf bei einem neuen Versions-Tag:

1. Versions-Tag pushen: Tests und Container-Veröffentlichung starten.
2. Erfolgreicher Release: `workflow_run` startet das Deployment.
3. Der Workflow prüft Release-Commit, main-Zugehörigkeit und Image-Digest.
4. Azure übernimmt das Image; Healthchecks prüfen Commit und Datenbank.

Azure-Zugriff erfolgt über OIDC; Secrets bleiben ausserhalb des Repositories.
Ein manueller Start mit einem älteren getesteten Tag ermöglicht den Rollback
des Images. Er setzt keine Datenbankänderungen zurück.

Am 2. November 2026 antworteten [Loginseite](https://lb-324.ahmet-ilhan.tech/),
[/health/live](https://lb-324.ahmet-ilhan.tech/health/live) und
[/health/ready](https://lb-324.ahmet-ilhan.tech/health/ready) mit HTTP 200.
Der laufende Commit entsprach `v0.1.3`; die Datenbankabfrage war erfolgreich.

Offen bleiben der erste echte Lauf des neuen automatischen Auslösers sowie
Azure-Nachweise für Neustart-Persistenz und Rollback. Die bisherigen erfolgreichen
Deployments wurden manuell gestartet.

**Eigenleistung selbst ergänzen:** Eigene Azure-/Workflow-Arbeit und eine
Entscheidung anhand eines tatsächlich gelösten Problems beschreiben.
