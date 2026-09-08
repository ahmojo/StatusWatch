# Anforderungen

## Ziel und MVP

Ich entwickle eine kleine Statusseite für eine Betreiberperson. StatusWatch prüft höchstens zehn öffentliche HTTP-/HTTPS-Ziele automatisch alle fünf Minuten oder auf Knopfdruck.

Der MVP für ungefähr zehn Lektionen umfasst:

- Anmeldung für eine Betreiberperson
- Ziele erfassen, anzeigen und löschen
- HTTP 200–399 als `up`, alle Fehler als `down`
- aktuellen Zustand und zehn letzte Prüfungen
- PostgreSQL mit SQLAlchemy und Tests mit pytest
- Docker, GitHub Actions und Azure App Service

Die Schätzung gilt bei vorhandenem GitHub-, Docker- und Azure-Zugang. Einrichtungsprobleme können ungefähr zwei weitere Lektionen benötigen.

## Nicht-Ziele

- mehrere Nutzer, Rollen oder Registrierung
- Benachrichtigungen, Diagramme und Verfügbarkeitsberichte
- private Netze, andere Protokolle oder Ports ausser 80/443
- Weiterleitungen verfolgen oder eigene Erfolgsstatus festlegen
- öffentliche API, Mobile App oder Single-Page-Anwendung
- Hochverfügbarkeit und vollständige Automatisierung der Azure-Infrastruktur

## User Stories

### US-01: Anmeldung

Als Betreiberperson möchte ich mich anmelden, damit niemand sonst Ziele verändert oder Prüfungen auslöst.

1. Geschützte Seiten verlangen eine Anmeldung.
2. Nur das konfigurierte Passwort eröffnet eine Sitzung.
3. Abmelden beendet den Zugriff.
4. Registrierung und Passwort-Wiederherstellung existieren nicht.

### US-02: Ziele verwalten

Als Betreiberperson möchte ich Prüfziele verwalten.

1. Ein Ziel braucht einen Namen mit 1–80 Zeichen und eine erlaubte URL.
2. Normalisierte URLs sind eindeutig.
3. Nach zehn Zielen wird ein weiteres Ziel abgelehnt.
4. Beim Löschen verschwinden Ziel und Ergebnisse gemeinsam.
5. Abgelehnte URLs lösen keinen Netzwerkzugriff aus.

### US-03: Automatisch prüfen

Als Betreiberperson möchte ich aktive Ziele alle fünf Minuten prüfen lassen.

1. Eine fällige Prüfung startet im laufenden System innerhalb von 60 Sekunden.
2. Pro Ziel und Fälligkeitszeitpunkt entsteht höchstens ein Ergebnis.
3. Ein fehlerhaftes Ziel blockiert andere Ziele nicht.
4. Gespeichert werden Zeitpunkt, Zustand, Statuscode, Antwortzeit und Fehlercode.

### US-04: Manuell prüfen

Als Betreiberperson möchte ich ein Ziel sofort prüfen.

1. Der Klick erzeugt genau ein Ergebnis.
2. Pro Ziel gilt eine Pause von 30 Sekunden.
3. HTTP 200–399 ergibt `up`; HTTP 400–599 oder technische Fehler ergeben `down`.
4. Die Seite zeigt das neue Ergebnis.

### US-05: Status ansehen

Als Betreiberperson möchte ich den aktuellen Zustand und Verlauf sehen.

1. Die Übersicht zeigt Name, URL, Zustand, Prüfzeit und Antwortzeit.
2. Ein neues Ziel erscheint als „noch nicht geprüft“.
3. Pro Ziel erscheinen höchstens zehn Ergebnisse, neuestes zuerst.
4. Interne Ausnahmen und Geheimnisse werden nicht angezeigt.

### US-06: Betriebszustand

Als Betreiber möchte ich das Deployment prüfen können.

1. `/health/live` liefert HTTP 200, solange der Webprozess läuft.
2. `/health/ready` liefert bei erreichbarer Datenbank HTTP 200, sonst HTTP 503.
3. Beide Antworten enthalten keine Konfiguration oder Geheimnisse.

### US-07: Auslieferung

Als Betreiber möchte ich nur getestete Versionen ausliefern.

1. Pull Requests führen pytest und einen Docker-Build aus.
2. Ein Fehler verhindert das Deployment.
3. `main` veröffentlicht ein Image mit vollständigem Commit-SHA.
4. GitHub Actions nutzt OIDC statt eines Azure-Passworts.
5. Nach dem Deployment muss `/health/ready` erfolgreich sein.

## Erfolgskriterium

Der MVP ist erreicht, wenn alle User Stories erfüllt sind, ein erreichbares und ein nicht erreichbares Ziel korrekt erscheinen und das Azure-Image einem Commit und Image-Digest zugeordnet werden kann. Phase 1 erfüllt diese Kriterien noch nicht.
