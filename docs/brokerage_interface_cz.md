# 🏦 Rozhraní Brokera (Brokerage Interface)

## 📝 Přehled

`BrokerageInterface` (`src/interfaces/brokerage.py`) definuje standardní kontrakt pro interakci s platformou finančního brokera. Abstrahuje specifická volání API a datové formáty konkrétního brokera (jako Alpaca, Interactive Brokers atd.), což umožňuje `ExecutionService` a potenciálně dalším službám provádět akce související s obchodováním způsobem nezávislým na brokerovi.

## 🎯 Účel

*   Abstrahovat složitost specifických API brokerů.
*   Umožnit přepínání mezi různými brokery jednoduchou změnou použité konkrétní implementace, aniž by se měnila základní obchodní logika.
*   Usnadnit testování povolením mock (falešných) implementací brokera.

## 🔑 Klíčové Metody (Koncepční)

Typická implementace `BrokerageInterface` by definovala metody pro základní operace brokera. Přesné názvy metod a parametry se mohou lišit v závislosti na skutečném souboru `brokerage.py`, ale běžné funkcionality zahrnují:

*   **`get_account_info()`:** Načte aktuální detaily účtu, jako je kupní síla, hotovostní zůstatek, hodnota portfolia a stav účtu. Vrací objekt `Portfolio` nebo podobnou strukturu.
*   **`get_market_data(symbols: List[str])`:** Získá aktuální tržní data (např. poslední kotace, bary) pro seznam specifikovaných obchodních symbolů. Vrací seznam objektů `MarketData` nebo slovník mapující symboly na data.
*   **`submit_order(order: Order)`:** Zadá obchodní příkaz u brokera na základě detailů poskytnutých v objektu `Order`. Vrací potvrzení příkazu nebo identifikátor.
*   **`get_order_status(order_id: str)`:** Zkontroluje stav (např. čekající, vyplněný, zrušený, zamítnutý) dříve zadaného příkazu pomocí jeho unikátního identifikátoru. Vrací aktualizovaný objekt `Order` nebo informace o stavu.
*   **`cancel_order(order_id: str)`:** Pokusí se zrušit otevřený příkaz.
*   **`list_positions()`:** Načte seznam aktuálně držených pozic na účtu.
*   **`is_market_open()`:** Zkontroluje, zda je relevantní trh (např. americké akcie) aktuálně otevřený pro obchodování.

## ⚙️ Implementace

Systém `trading_system` může obsahovat jednu nebo více konkrétních implementací tohoto rozhraní, například:

*   `AlpacaBrokerage`: Interaguje s Alpaca Trade API.
*   `MockBrokerage`: Simulovaný broker používaný pro účely testování, vrací předdefinovaná data a simuluje vyplnění příkazů bez připojení k živému trhu.

Konkrétní implementace použitá za běhu je typicky určena nastavením konfigurace v `.env` a instanciována `OrchestrationDaemon`.

## ⚙️ Konfigurace

Konkrétní implementace budou vyžadovat specifické API přihlašovací údaje a URL adresy endpointů, nakonfigurované v souboru `.env`:

*   `APCA_API_KEY_ID` (V našem `.env` jako `ALPACA_API_KEY`)
*   `APCA_API_SECRET_KEY` (V našem `.env` jako `ALPACA_SECRET_KEY`)
*   `APCA_API_BASE_URL` (V našem `.env` jako `ALPACA_BASE_URL`) (např. endpoint pro paper nebo live trading)

## 🔗 Klíčové Interakce

*   **`ExecutionService` 💼:** Primárně používá toto rozhraní k zadávání příkazů, kontrole stavů a získávání informací o portfoliu pro řízení rizika a dimenzování příkazů.
*   **`OrchestrationDaemon` 🕰️:** Může používat toto rozhraní k načtení počátečního stavu portfolia nebo kontrole tržních hodin.
*   **Modely `Order`, `Portfolio`, `MarketData` 🧱:** Metody rozhraní často konzumují nebo vracejí instance těchto datových modelů.
*   **`config.py` ⚙️:** Čte potřebné API přihlašovací údaje pro zvolenou implementaci.
