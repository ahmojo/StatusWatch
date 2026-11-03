# Dokumentation Modul 324

Stand: 2. November 2026.

## Inhaltsverzeichnis

- [A1: Anforderungsverwaltung](#a1-anforderungsverwaltung)
- [B1: Lokale Entwicklungsumgebung](#b1-lokale-entwicklungsumgebung)
- [C1: Sourcecode- und Artefaktverwaltung](#c1-sourcecode--und-artefaktverwaltung)
- [D1: Automatisierter Integrationsprozess](#d1-automatisierter-integrationsprozess)
- [E1: Automatisierter Deploymentprozess](#e1-automatisierter-deploymentprozess)

## A1: Anforderungsverwaltung

DevOps verbindet Entwicklung und Betrieb durch gemeinsame Abläufe und
automatisierte Prüfungen. Bei StatusWatch führt der Weg von einer Anforderung
über Code und Tests bis zur Auslieferung. Dadurch fallen Fehler vor einer
Veröffentlichung auf; ein Versionsstand lässt sich gezielt wieder ausliefern.

Eine Anforderung beschreibt, was die Anwendung leisten soll. Eine User Story
formuliert Rolle, Ziel und Nutzen. Akzeptanzkriterien legen fest, woran die
Erfüllung erkannt wird. Ein Issue hält die Aufgabe fest, der Pull Request
verknüpft sie mit der Umsetzung. Commits dokumentieren einzelne Änderungen.

Der Umfang von StatusWatch ist bewusst klein: eine Betreiberperson, höchstens
zehn Monitore, HTTP-/HTTPS-Prüfungen alle fünf Minuten und die letzten zehn
Ergebnisse. Anmeldung und Monitorverwaltung sind funktionale Anforderungen;
Zugriffsschutz, Eingabeprüfung und automatisierte Tests sichern die Qualität.

Beispiel: Als Betreiberperson möchte ich Websites verwalten, damit ich deren
Erreichbarkeit prüfen kann. [Issue #7](https://github.com/ahmojo/StatusWatch/issues/7)
nennt dafür unter anderem Anmeldung, CSRF-Schutz und das Limit von zehn Monitoren.
Ein prüfbares Akzeptanzkriterium lautet: Sind zehn Monitore gespeichert, wird
ein weiterer abgelehnt. [PR #8](https://github.com/ahmojo/StatusWatch/pull/8)
enthält die Umsetzung; der Test `test_ten_monitor_limit_and_creation_after_deletion`
prüft dieses Verhalten. Die [User-Story-Vorlage](../.github/ISSUE_TEMPLATE/user_story.md)
nutzt das Schema «Gegeben – Wenn – Dann» für Akzeptanzkriterien.

Für dieses Projekt lassen sich die Werkzeuge so vergleichen:

| Werkzeug | Eignung für StatusWatch |
|---|---|
| GitHub Issues | Anforderungen und Pull Requests liegen beim Code. Für den kleinen Umfang reicht ein gemeinsames Repository. |
| Trello | Karten bieten eine übersichtliche Aufgabenplanung. Für die direkte Verbindung mit dem Code wäre eine zusätzliche Integration sinnvoll. |
| Jira | Für umfangreiche Teamabläufe geeignet; die zusätzliche Konfiguration bringt bei diesem kleinen Projekt wenig Nutzen. |

**Eigenleistung:** Ich habe den Funktionsumfang festgelegt und die Anforderungen
an die KI vorgegeben. Ich habe Änderungen reviewt, die Anwendung im Browser
getestet und Korrekturen veranlasst. Die Arbeit bleibt über Issues und Pull
Requests nachvollziehbar; GitHub dient als gemeinsame Ablage für Planung und Code.

## B1: Lokale Entwicklungsumgebung

Die Entwicklung erfolgt unter Windows mit PowerShell, Git und einer lokalen
Python-Umgebung. `.venv` trennt die Projektabhängigkeiten von anderen Projekten.
[requirements.txt](../requirements.txt) enthält die Laufzeitpakete;
[requirements-dev.txt](../requirements-dev.txt) ergänzt pytest, Coverage,
Ruff und pre-commit. Die lokale Umgebung verwendet Python 3.14, CI und
Container verwenden Python 3.11.

Für die Einrichtung werden die virtuelle Umgebung angelegt, die Abhängigkeiten
installiert und die Commit-Hooks aktiviert:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pre_commit install
```

Die lokale `.env` enthält eigene Konfigurationswerte und bleibt durch
`.gitignore` ausserhalb des Repositories. Die README erklärt Datenbankeinrichtung
und Start. Für einen vollständigen lokalen Betrieb steht zusätzlich Docker
Compose mit Webdienst und PostgreSQL bereit. Die virtuelle Umgebung eignet
sich für schnelle Codeprüfungen; Compose bildet die Laufzeit mit Datenbank ab.

Die Umgebung wurde um automatische Commit-Prüfungen erweitert:
[Issue #15](https://github.com/ahmojo/StatusWatch/issues/15) und
[PR #16](https://github.com/ahmojo/StatusWatch/pull/16) dokumentieren diesen Schritt.
Die [pre-commit-Konfiguration](../.pre-commit-config.yaml) führt Ruff, pytest
mit Coverage und Dateiprüfungen aus. GitHub Actions ruft dieselben Prüfungen
auf. Dadurch gelten lokal und beim Pull Request dieselben Qualitätsregeln.

`python -m pip check` bestätigt konsistente Abhängigkeiten.
Die Ergebnisse der lokalen Tests stehen unter D1.

**Eigenleistung:** Die technischen Einrichtungsschritte habe ich mit KI
durchführen lassen. Ich habe die vorgeschlagenen Änderungen reviewt und
freigegeben sowie die Anwendung im Browser geprüft. Meine Verantwortung lag
bei den Anforderungen, der Beurteilung der Ergebnisse und der Entscheidung,
welche Änderungen übernommen werden.

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
| `python -m pytest -p no:cacheprovider` | 158 Tests bestanden, 98,57 % Coverage |
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
