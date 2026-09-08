# Backlog

Diese kleinen GitHub-Issues sind geplant, aber noch nicht auf GitHub angelegt.

| ID | Issue | Lektionen | Abhängigkeit | Abnahme |
|---|---|---:|---|---|
| SW-01 | Anforderungen und Entscheidungen dokumentieren | 1.00 | – | Phase-1-Dokumente geprüft, kein Anwendungscode |
| SW-02 | Flask-Grundstruktur und Datenbankschema erstellen | 1.00 | SW-01 | App Factory, Migration und Health-Endpunkte getestet |
| SW-03 | Betreiber-Anmeldung umsetzen | 0.75 | SW-02 | US-01 und CSRF-Schutz getestet |
| SW-04 | Ziele verwalten | 1.00 | SW-02, SW-03 | US-02 erfüllt |
| SW-05 | SSRF-Schutz umsetzen | 1.00 | SW-02 | Pflichtfälle aus `security.md` getestet |
| SW-06 | HTTP-Prüfung und Speicherung umsetzen | 1.00 | SW-04, SW-05 | US-04 erfüllt, kein Antwortkörper gespeichert |
| SW-07 | Fünf-Minuten-Scheduler umsetzen | 0.75 | SW-06 | US-03 erfüllt, Doppellauf verhindert |
| SW-08 | Status und Verlauf anzeigen | 0.75 | SW-06 | US-05 erfüllt, ohne JavaScript nutzbar |
| SW-09 | pytest-Suite abschliessen | 1.00 | SW-03–SW-08 | US-01–US-06 Tests zugeordnet |
| SW-10 | Docker-Betrieb mit PostgreSQL erstellen | 0.75 | SW-09 | Neustart erhält Daten, Readiness erfolgreich |
| SW-11 | CI und Container-Artefakt erstellen | 0.50 | SW-10 | pytest, Build und SHA-Image automatisch |
| SW-12 | Azure-Deployment nachweisen | 0.50 | SW-11 | OIDC, Deployment, Readiness und Rollback belegt |
|  | **Summe** | **10.00** |  |  |

Jedes Issue erhält messbare Kriterien, einen passenden Branch und einen kleinen Pull Request. Ein fehlgeschlagener Test oder Build blockiert Merge und Deployment.

```text
SW-01 → SW-02 ─┬→ SW-03 → SW-04 ─┐
                └→ SW-05 ─────────┼→ SW-06 ─┬→ SW-07 ─┐
                                   │         └→ SW-08 ─┼→ SW-09 → SW-10 → SW-11 → SW-12
                                   └───────────────────┘
```

Die Schutzgrenzen stehen vor dem ersten HTTP-Aufruf. Die vollständigen Tests folgen vor Containerbau und Deployment.
