# Produktentscheidungen

Bestätigt am 4. September 2026.

## D-001: Prüfungen

Ich habe automatische Prüfungen alle fünf Minuten und einen manuellen Start gewählt. Die Automatik erfüllt den Zweck einer Überwachung; der manuelle Start hilft beim Einrichten und Vorführen.

## D-002: Zugang

StatusWatch erhält eine Anmeldung für eine Betreiberperson. Damit bleiben Zielverwaltung und Netzwerkaufrufe geschützt, ohne eine Benutzerverwaltung zu bauen.

## D-003: Oberfläche

Die Oberfläche zeigt Zielverwaltung, aktuellen Zustand und zehn letzte Prüfungen. Das reicht zur Fehlersuche. Diagramme und Langzeitauswertungen würden den MVP vergrössern.

## D-004: Statusregel

HTTP 200–399 gilt als erreichbar. HTTP 400–599 und technische Fehler gelten als nicht erreichbar. Weiterleitungen werden angezeigt, aber nicht verfolgt.

## D-005: Azure

Ich habe Docker auf Azure App Service, Azure Database for PostgreSQL und GitHub Actions mit OIDC gewählt. Diese Lösung zeigt Container, Artefakte und Deployment, ohne eine Container-Orchestrierung einzuführen.
