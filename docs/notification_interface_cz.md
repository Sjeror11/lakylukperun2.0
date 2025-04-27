# 📢 Notifikační Rozhraní (Notification Interface)

## 📝 Přehled

`NotificationInterface` (`src/interfaces/notification.py`) definuje standardní kontrakt pro odesílání zpráv, upozornění nebo stavových aktualizací z obchodního systému do externích kanálů. Abstrahuje specifická API nebo protokoly používané různými notifikačními platformami (jako Mattermost, Slack, email, SMS atd.).

## 🎯 Účel

*   Abstrahovat detaily specifických API notifikačních služeb (např. Mattermost webhooks vs. email SMTP).
*   Umožnit systému (primárně `OrchestrationDaemon` nebo jiným službám) odesílat notifikace bez nutnosti znát specifika zvoleného kanálu.
*   Umožnit snadnou konfiguraci různých metod notifikace nebo přidání nových vytvořením nových implementací.
*   Usnadnit testování povolením mock (falešných) implementací notifikací, které jednoduše logují zprávy nebo je ukládají pro ověření místo jejich externího odeslání.

## 🔑 Klíčové Metody (Koncepční)

`NotificationInterface` typicky definuje primární metodu pro odesílání zpráv:

*   **`send_notification(message: str, subject: Optional[str] = None, **kwargs)`:** Odešle poskytnutý řetězec `message` do nakonfigurovaného notifikačního kanálu. Může přijímat volitelný `subject` (užitečný pro emaily) a potenciálně další parametry specifické pro kanál prostřednictvím `kwargs`.

## ⚙️ Implementace

Systém může obsahovat konkrétní implementace jako:

*   `MattermostNotifier`: Odesílá zprávy do specifikovaného Mattermost kanálu pomocí knihovny `mattermostdriver`.
*   `EmailNotifier`: Odesílá zprávy emailem pomocí SMTP.
*   `ConsoleNotifier`: Jednoduše vypisuje zprávy do konzole (užitečné pro ladění nebo jednoduchá nastavení).
*   `MockNotifier`: Simulovaný notifikátor pro testování, který zaznamenává zprávy, které mu byly odeslány.

`OrchestrationDaemon` vybírá a instanciuje příslušnou implementaci na základě konfigurace.

## ⚙️ Konfigurace

Konkrétní implementace vyžadují specifické konfigurační detaily v souboru `.env`:

*   **Mattermost:** `MATTERMOST_URL`, `MATTERMOST_TOKEN`, `MATTERMOST_CHANNEL_ID`
*   **Email:** Detaily SMTP serveru, adresy odesílatele/příjemce, přihlašovací údaje.

## 🔗 Klíčové Interakce

*   **`OrchestrationDaemon` 🕰️:** Nejpravděpodobnější služba, která používá toto rozhraní pro odesílání zpráv o spuštění/vypnutí, kritických chybách nebo periodických stavových aktualizacích.
*   **Ostatní Služby (Potenciálně):** Služby jako `ExecutionService` nebo `OptimizationService` jej mohou používat k hlášení významných událostí (např. provedení velkého obchodu, doporučení optimalizace).
*   **`config.py` ⚙️:** Čte potřebné přihlašovací údaje a detaily endpointů pro zvolenou implementaci notifikace.
*   **Externí Knihovny:** Implementace používají knihovny specifické pro poskytovatele (`mattermostdriver`, `smtplib`).
*   **`logger.py` 📝:** Může logovat pokusy o odeslání notifikací a jejich úspěch/neúspěch.
