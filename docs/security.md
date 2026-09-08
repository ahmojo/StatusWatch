# Sicherheitsanforderungen

## Schutzbereich

Ich schütze Betreiberzugang, Datenbank, Azure-Berechtigungen und interne Netze. Formulare, Ziel-URLs, DNS-Antworten und fremde Websites gelten als nicht vertrauenswürdig.

Ein schwerer Fehler liegt vor, wenn eine fremde Person Daten verändert, eine Prüfung eine interne Adresse erreicht, ein Geheimnis erscheint oder ein ungeprüfter Commit ausgeliefert wird.

## SSRF-Schutz

1. Erlaubt sind nur absolute HTTP-/HTTPS-URLs mit Port 80 oder 443.
2. Zugangsdaten, Query, Fragment und ungültige Hostnamen werden abgelehnt.
3. Vor jeder Prüfung werden alle A- und AAAA-Adressen neu aufgelöst.
4. Sobald eine Adresse nicht öffentlich routbar ist, wird das Ziel abgelehnt.
5. Das gilt auch für direkte IP-Adressen und IPv4-in-IPv6-Schreibweisen.
6. Der Client verbindet sich mit einer geprüften IP. Hostheader, TLS-SNI und Zertifikatsprüfung verwenden den ursprünglichen Hostnamen.
7. Weiterleitungen werden nicht verfolgt.
8. Umgebungs-Proxys sind deaktiviert; TLS-Prüfung bleibt aktiv.
9. Eine Prüfung endet spätestens nach zehn Sekunden.
10. Antwortkörper und vollständige URLs werden nicht gespeichert oder geloggt.
11. Eine abgelehnte Eingabe erzeugt keinen HTTP-Aufruf.

| Pflichttest | Erwartung |
|---|---|
| `file:`, `ftp:`, `gopher:` oder relative URL | abgelehnt |
| Loopback, private oder Link-Local-Adresse | abgelehnt |
| gemischte öffentliche und private DNS-Antwort | abgelehnt |
| DNS-Wechsel nach Vorprüfung | keine Verbindung zur ungeprüften IP |
| 302 auf interne URL | 302 als `up`, Weiterleitung nicht aufgerufen |
| Timeout oder TLS-Fehler | `down` mit begrenztem Fehlercode |

Grundlage: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html

## Anmeldung und Eingaben

- Passwort-Hash und Sitzungsschlüssel kommen aus Laufzeitvariablen.
- Änderungsformulare verwenden CSRF-Tokens.
- Produktionscookies sind `Secure`, `HttpOnly` und `SameSite=Lax`.
- HTML-Ausgaben werden escaped; SQLAlchemy bindet Datenbankparameter.
- Eine manuelle Prüfung pro Ziel ist nur alle 30 Sekunden möglich.
- Health-Endpunkte und Fehlerseiten zeigen keine Konfiguration oder Stacktraces.

## Deployment

- `.env`, Token, Passwörter und Datenbankwerte werden nicht versioniert.
- Nur der Deployment-Job erhält `id-token: write`.
- OIDC ist auf Repository, `main` und Environment beschränkt.
- Actions werden auf vollständige Commit-SHAs festgelegt.
- PostgreSQL nutzt TLS; Logs enthalten keine Geheimnisse.

## Grenzen und Abnahme

Der einzelne Prozess kann während eines Ausfalls keine Ziele prüfen. Die Betreiberperson muss öffentliche Health-URLs ohne Geheimnisse wählen. Die Azure-Infrastruktur wird im MVP nicht vollständig als Code geprüft.

Die Abnahme verlangt alle SSRF-Pflichttests, identische geprüfte und verbundene IPs, geschützte Änderungen, einen Scan ohne Geheimnisse und ein Deployment ohne Publishing-Profil oder Azure-Passwort.
