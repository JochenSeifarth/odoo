# Buchungen


## Plattformen: Teilnehmer zahlt komplett und nur an Plattform
#### Beispiele
- GetYourGuide
- Segelreisen Hering
- Click&Boat
- SamBoat

Unsere Rechnung geht an die Plattform als Kunde - **nicht** an Teilnehmer.<br>
Teilnehmer bekommen von uns nur Tickets.

#### Auslöser
Email mit Buchungsdaten kommt.

### Vorgehen
+ In Odoo als Benutzer anmelden, <a href="https://www.real-yachting-alicante.com/odoo/sales" target="_blank">Menü Verkauf</a>
+ Auf **\[+Neu]** klicken um ein Angebot zu erstellen:

![angebot1](images/angebot1.png)

1. **Kunde** ist immer die Platform, z.B. GetYourGuide. Diese sollte bereits in Odoo existieren.
2. ***Produkt hinzufügen*** klicken, Veranstaltung auswahlen, Zeitfenster und Anzahl Tickets auswählen
3. ggf. Preis überschreiben
4. auf Tab "Weitere Informationen" erfassen:
    
![angebot2](images/angebot2.png)

1. Kundenreferenz: GYG????????? - die Auftragsnummer der Platform. Das ist wichtig damit später danan gesucht werden kann.
2. Quelle: Die Platform auswählen, z.B. "GetYourGuide. Diese sollte bereits in Odoo existieren.

Das Angebot braucht nicht per Email versendet zu werden, es wurde ja bereits schon gebucht. Deshalb 
am Angebot **\[Bestätigen]** klicken, das Popup "Veranstlatunsgregistrierungen erscheint:

![angebot3](images/angebot3.png)

- **Teilnehmer**-Namen, -E-Mail und -Telefon eintragen
- **\[Registrierungen_erstellen/aktualisieren]**  klicken
  
!!! warning "Teilnehmer erhält automatisch Tickets (Achtung: Email ist in der Sprache des aktuell angemeldeten Benutzers! - solange der Kunde (die Platform) keine Sprache voreingestellt hat). Das Zeitfenster der Veranstaltung ist damit belegt und kann nicht mehr von anderen gebucht werden."

Am Angebot **\[Rechnung erstellen]** klicken, "reguläre Rechnung" auswählen, ggf. Fälligkeitsdatum anpassen, **\[Bestätigen]** klicken

Bei Zahlungseingang von der Platform die Rechnung mit **\[Zahlen]** als bezahlt markieren

## Plattformen: Teilnehmer zahlt nur Provision an Plattform und an uns den Rest
#### Beispiele
- FishingBooker

**Rechnung** über den Restbetrag (also ohne Provision) und **Tickets** gehen an **Kunde/Teilnehmer**

#### Auslöser

Email mit Buchungsdaten kommt.

### Vorgehen
Anonym die Website aufrufen. Mit diesen Links wird man automatisch anonym und die Quelle wird automatisch richtig erfasst.

- <a href="https://www.fishing-alicante.com/web/session/logout?redirect=/event&utm_source=FishingBooker"
   target="_blank"
   rel="noopener noreferrer">
   https://www.fishing-alicante.com/web/session/logout?redirect=/event&utm_source=<strong>FishingBooker</strong>
</a>

Sprache **des Kunden** auswählen ![Sprachauswahl](images/sprachauswahl.png)

Veranstaltung auswählen, **\[Buchen]** klicken, Datum auswählen, Ticket(s) auswählen, Teilnehmer-Name, -Email, -Telefon ausfüllen,  **\[Zur Zahlung]** klicken

Rechnungsadresse ausfüllen, **\[Bestätigen]** klicken
!!! info "Wenn keine postalische Adresse vorliegt: Email und/oder Telefon-Nummer als Straße verwenden und als Stadt 03001 Alicante, Spanien"

Damit ist die Auftragserfassung abgeschlossen, jetzt in Odoo als regulärer Benutzer anmelden, <a href="https://www.real-yachting-alicante.com/odoo/sales"
   target="_blank"
   rel="noopener noreferrer">Menü Verkauf</a>

Die eben erfasste Buching sollte das oberste Angebot sein, dieses aufrufen. (Optional: Durch Klick auf den  Kundennamen die Kundendetails aufrufen und die Sprache überprüfen, es sollte die oben ausgewählte sein)

![angebot11](images/angebot11.png)

1. Preis überschreiben
2. auf Tab "Weitere Informationen" erfassen: Kundenreferenz: FB?????????, Quelle sollte schon ausgefüllt sein

**\[Senden]** klicken, ggf. Email Text im Popup modifizieren und **\[Senden]** klicken, dann wird das Angebot per Email verschickt.

Der Kunde erhält folgende Email:

![angebot13](images/angebot13-email.png)
In der Email hat der Kunde einen Button **\[Angebot akzeptieren & bezahlen]** womit er jederzeit und ohne spezielle Anmeldung auf folgende Bezahlseite kommt:
![angebot13-payment](images/angebot13-payment.png)


!!!warning "Erst bei Bezahlung wird der Platz für die Veranstaltung reserviert und das Ticket sowie Rechnungen verschickt. Das passiert alles automatisch und in der oben ausgewählten Sprache des Kunden."
