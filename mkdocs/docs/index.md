**Willkommen im Benutzerhandbuch !**
## Allgemeines zu Odoo
### Beriffsdefinition
**Quelle** ist die Internet-Plattform, Marketingpartner, Flyer, Anzeige o.ä. wie der Teilnehmer auf uns aufmerksam geworden ist bzw. gebucht hat.<br>
**Teilnehmer** ist immer die Person die an einer Veranstaltung teilnimmt.<br>
**Kunde** kann der Teilnehmer selbst sein oder die Plattform über die gebucht wurde.<br>
**Ticket** ist eine "Eintrittskarte" die detaillierte Anweisungen zu Veranstaltungsort und -zeit sowie eine Wegbeschreibung  enthält.<br>
**Angebot** ist eine Preisauskunft nach der ein Kunde bestellen soll. Es kann ein für eine Standard-Veranstaltung sein oder individuell zusammengestellt.
**Verkaufsauftrag** ist ein bestätigtes, also durch den Kunden angenommenes Angebot.

### Ticketverfügbarkeit
Bei Buchungen und Stornos in Odoo wird die Verfügbarkeit automatisch durch das Systen in Echtzeit aktualisiertt.

Tickets sind nicht mehr für andere verfügbar wenn ein **Angebot bestägt** wurde (=Verkaufsauftrag).<br>
Das sind alle Tickets für die manuell ein Angebot angelegt und **bestätigt** wurde.
Angebot können entweder automatisch durch Bezahlung (über Stripe) oder manuell durch Klicken von **\[Bestätigen]** bestätigt werden.<br>
Normalerweise werden alle Buchungen über Plattformen die wir per Email bekommen direkt manuell bestätigt. Bei Self-Service Buchungen wird das Angebot in dem Moment automatisch bestätigt in dem über Stripe bezahlt wurde.
Wenn wir nur ein Angebot erstellt haben und dies per Email verschickt haben sollte durch Annahme und Bezahlung automatisch bestätigt werden . Altenativ kann es manuell bestätigt werden durch Email, Anruf, etc.

Die Verfügabrkeit von Veranstaltungen auf anderen Plattformem muss ggf. dort manuell geändert werden. Das sind: GYG, (wo muss noch gepflegt werden ?)