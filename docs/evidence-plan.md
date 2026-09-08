# Nachweisplan für C1, D1 und E1

Phase 1 plant die Nachweise, behauptet aber noch keine Umsetzung. Zu jedem Beleg halte ich Ausgangslage, eigene Entscheidung, ausgeführte Arbeit, Ergebnis und Grenze fest. Erfahrungen und Eigenleistungen dürfen nicht erfunden werden. Eine verlangte Hilfsmittel-Offenlegung erfolgt wahrheitsgemäss.

## C1: Sourcecode- und Artefaktverwaltung

| Nachweis | Messbares Kriterium |
|---|---|
| GitHub-Issues mit Kriterien | Jeder PR verweist auf ein Issue |
| Branches, Commits und Pull Requests | Der Diff enthält nur den Issue-Umfang |
| Story, PR und Test | Jede umgesetzte Story ist zurückverfolgbar |
| Docker-Image in ACR | Commit-SHA und Image-Digest passen zusammen |
| Git-Tag oder Release | Der Tag zeigt auf den dokumentierten Commit |

Ich sichere Links, `git log`, erfolgreiche Checks, SHA-Tag und Digest. Die Commit-Grenzen begründe ich in eigenen Worten.

## D1: Automatisierter Integrationsprozess

| Nachweis | Messbares Kriterium |
|---|---|
| pytest-Zuordnung | US-01 bis US-06 sind abgedeckt oder manuell begründet |
| CI auf Pull Requests | pytest und Docker-Build starten automatisch |
| blockierender Fehler | Ein roter Check verhindert Merge und Deployment |
| PostgreSQL-Integration | Migration, Transaktion und Scheduler-Schlüssel getestet |
| geprüftes Image | Bei Testfehler wird kein Image veröffentlicht |

Ich sichere Testbefehl, Exit-Code und Workflow-Links. Falls ein echter Fehler auftritt, dokumentiere ich den Regressionstest. Ohne beobachteten Fehler erfinde ich keinen.

## E1: Automatisierter Deploymentprozess

| Nachweis | Messbares Kriterium |
|---|---|
| Ablauf bis Azure | Jeder Schritt nennt Eingang, Ergebnis und Fehlerwirkung |
| Deployment auf `main` | SHA-Image wird ohne manuellen Upload ausgerollt |
| OIDC | Kein Publishing-Profil oder Azure-Passwort in GitHub |
| Readiness | SHA, Digest, Zeitpunkt und HTTP 200 belegt |
| Rollback | App Service läuft wieder mit dem vorherigen Digest |

Ich sichere Workflow-Run, aktiven Digest, Readiness und einen sicheren Rollback. Die einmalige Azure-Einrichtung bleibt manuell; der Nachweis gilt für die Anwendungsauslieferung.

## Zuordnung

| Artefakt | C1 | D1 | E1 |
|---|:---:|:---:|:---:|
| Anforderungen, Entscheidungen, Issues | ✓ |  |  |
| Commits und Pull Requests | ✓ | ✓ |  |
| pytest und CI |  | ✓ |  |
| SHA-Image und Digest | ✓ | ✓ | ✓ |
| OIDC-Deployment |  |  | ✓ |
| Readiness und Rollback |  |  | ✓ |

Vor der Abgabe prüfe ich, ob jeder Beleg auffindbar ist, Eigenleistung klar bleibt, SHA und Digest übereinstimmen und keine Geheimnisse erscheinen.
