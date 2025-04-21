# 💼 Exekuční Služba (Execution Service)

## 📝 Přehled

Exekuční Služba, implementovaná ve třídě `ExecutionManager` (`src/services/execution_service/manager.py`), je zodpovědná za překlad obchodních signálů generovaných AI Službou do skutečných příkazů zadaných u brokera. Spravuje životní cyklus příkazů a zajišťuje, aby obchody odpovídaly předdefinovaným parametrům rizika.

## 🎯 Odpovědnosti

*   **Zpracování Signálů 💡:** Přijímá objekty `Signal` od `OrchestrationDaemon`.
*   **Řízení Rizika & Dimenzování (Sizing) 🛡️:** Vypočítává vhodnou velikost příkazu (množství) na základě signálu, aktuální hodnoty portfolia, dostupné kupní síly a nakonfigurovaných parametrů rizika (např. `TRADE_RISK_PER_TRADE`). Toto je kritický krok k zabránění nadměrným ztrátám.
*   **Generování Příkazů 🛒:** Vytváří strukturované objekty `Order` na základě signálu a vypočtené velikosti, specifikující detaily jako symbol, stranu (nákup/prodej), množství, typ příkazu (market, limit) a potenciálně dobu platnosti (time-in-force).
*   **Interakce s Brokerem 🏦:** Používá `BrokerageInterface` k:
    *   Zadání vygenerovaných příkazů u brokera.
    *   Sledování stavu otevřených příkazů (např. čekající, vyplněný, zrušený).
    *   Získání aktuálních informací o portfoliu (pozice, hotovostní zůstatek) potřebných pro dimenzování a validaci.
    *   Zrušení příkazů v případě potřeby (např. na základě časových limitů nebo nových signálů).
*   **Aktualizace Portfolia (Koordinace) 🔄:** Zatímco `BrokerageInterface` získává data portfolia, Exekuční Služba může být zodpovědná za spouštění aktualizací nebo zajištění, že interní reprezentace portfolia systému zůstane synchronizovaná po provedení obchodů.
*   **Zpracování Chyb ❌:** Spravuje chyby související se zadáváním nebo sledováním příkazů (např. nedostatečné prostředky, neplatný symbol, chyby API, zamítnuté příkazy).

## 🔄 Pracovní Postup (Workflow)

1.  **Přijetí Signálu:** `OrchestrationDaemon` předá objekt `Signal` službě `ExecutionManager` (např. přes metodu `execute_signal`).
2.  **Získání Dat Portfolia:** Manažer použije `BrokerageInterface` k získání nejnovějšího stavu portfolia (hotovost, existující pozice, kupní síla).
3.  **Validace Signálu:** Zkontroluje, zda je signál proveditelný (např. dostatečná kupní síla pro nákup, držení aktiva pro prodej).
4.  **Výpočet Velikosti Příkazu:** Určí počet akcií/kontraktů k obchodování na základě konfigurace rizika (`TRADE_RISK_PER_TRADE`), hodnoty účtu a potenciálně úrovní stop-loss implikovaných signálem nebo strategií.
5.  **Vytvoření Objektu Příkazu:** Sestaví objekt `Order` se všemi potřebnými detaily.
6.  **Zadání Příkazu:** Použije metodu `submit_order` rozhraní `BrokerageInterface` k odeslání příkazu brokerovi.
7.  **Sledování Stavu Příkazu:** Periodicky kontroluje stav zadaného příkazu pomocí `BrokerageInterface` (např. `get_order_status`). To se může stát okamžitě nebo být řešeno samostatnou monitorovací smyčkou v rámci služby nebo démona.
8.  **Záznam Exekuce:** Jakmile je příkaz potvrzen jako vyplněný, zaloguje detaily exekuce a aktualizuje interní stav nebo upozorní `OrchestrationDaemon`.
9.  **Aktualizace Paměti:** Zajistí, že detaily provedení obchodu jsou zaznamenány `MemoryService`.

## ⚙️ Konfigurace

Exekuční Služba závisí na:

*   **API Přihlašovacích Údajích Brokera 🔑:** (`APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, `APCA_API_BASE_URL`) definovaných v `.env`.
*   **Parametrech Rizika 🛡️:** (`TRADE_RISK_PER_TRADE`) definovaných v `.env`.
*   **Obchodních Symbolech:** (`TRADING_SYMBOLS`) pro validaci signálů.

## 🔗 Klíčové Interakce

*   **`OrchestrationDaemon` 🕰️:** Přijímá signály od démona a hlásí stav exekuce zpět.
*   **`BrokerageInterface` 🏦:** Silně závisí na tomto rozhraní pro veškeré interakce s obchodní platformou (zadávání příkazů, získávání stavu, načítání portfolia).
*   **Model `Signal` 💡:** Konzumuje objekty `Signal` jako vstup.
*   **Model `Order` 🛒:** Vytváří a spravuje objekty `Order`.
*   **Model `Portfolio` 💼:** Čte data portfolia pro rozhodování.
*   **`MemoryService` 💾:** Ukládá záznamy o zadaných a provedených příkazech.
*   **`config.py` ⚙️:** Čte přihlašovací údaje brokera a nastavení rizika.
*   **`logger.py` 📝:** Loguje pokusy o zadání příkazu, vyplnění a chyby.
