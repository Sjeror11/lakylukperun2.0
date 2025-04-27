# 🕰️ Orchestrační Služba (Orchestration Service)

## 📝 Přehled

Orchestrační Služba, implementovaná primárně ve třídě `OrchestrationDaemon` (`src/services/orchestration_service/daemon.py`), funguje jako centrální nervový systém Perun Trading System. Je zodpovědná za koordinaci akcí všech ostatních služeb, správu hlavního životního cyklu aplikace a zajištění, že úkoly jsou prováděny ve správném pořadí a ve vhodných časech.

## 🎯 Odpovědnosti

*   **Inicializace:** Instanciuje a inicializuje všechny ostatní základní služby (AI, Exekuční, Paměťová, Optimalizační, Notifikační, rozhraní Brokera, LLM) při spuštění.
*   **Hlavní Smyčka:** Spouští primární řídicí smyčku aplikace. Tato smyčka typicky zahrnuje periodické kontroly a provádění obchodního cyklu.
*   **Plánování:** Určuje, kdy provádět klíčové akce, jako je získávání tržních dat, spouštění AI analýzy, kontrola obchodních signálů a provádění příkazů. To často zahrnuje:
    *   Kontrolu, zda je trh otevřený (pomocí utilit jako `scripts/check_market_hours.py` nebo dat z API brokera).
    *   Dodržování nakonfigurované `TRADING_FREQUENCY_MINUTES`.
*   **Koordinace:** Předává data mezi službami. Například bere tržní data, poskytuje je AI Službě, přijímá zpět signály a předává tyto signály Exekuční Službě.
*   **Správa Stavu:** Sleduje celkový stav systému (např. běží, ukončuje se).
*   **Zpracování Chyb:** Implementuje zpracování chyb na nejvyšší úrovni a pokouší se o řádné ukončení nebo notifikace v případě kritických selhání v rámci služeb.
*   **Zpracování Signálů:** Naslouchá systémovým signálům (jako `SIGINT` z Ctrl+C) k zahájení procesu řádného ukončení, zajišťující bezpečné dokončení nebo zrušení probíhajících operací.

## 🔄 Pracovní Postup (Workflow)

Typický cyklus spravovaný Orchestračním Démonem může vypadat takto:

1.  **Čekání/Plánování:** Démon čeká do dalšího naplánovaného obchodního cyklu na základě `TRADING_FREQUENCY_MINUTES`.
2.  **Kontrola Trhu:** Ověří, zda je relevantní trh otevřený. Pokud ne, čeká na další cyklus.
3.  **Získání Dat:** Spustí `BrokerageInterface` k získání aktuálních tržních dat (ceny, objem) a stavu portfolia (hotovost, pozice).
4.  **Načtení Paměti:** Dotáže se `MemoryService` na relevantní nedávný kontext (minulé obchody, nedávná tržní pozorování, předchozí poznatky LLM).
5.  **AI Zpracování:** Předá získaná tržní data a kontext paměti `AIService`. AI Služba interaguje s LLM k analýze informací a generování potenciálních obchodních signálů (objekty `Signal`).
6.  **Vyhodnocení Signálu:** Přijme signály od `AIService`. Potenciálně aplikuje základní filtrování nebo validaci.
7.  **Exekuce:** Pokud jsou vygenerovány platné signály k nákupu/prodeji, předá je `ExecutionService` k zadání příkazů prostřednictvím `BrokerageInterface`.
8.  **Aktualizace Paměti:** Uloží události cyklu (získaná data, generované signály, zadané příkazy, zaznamenané chyby) do `MemoryService`.
9.  **Notifikace:** Odešle stavové aktualizace nebo upozornění prostřednictvím `NotificationInterface`, pokud je nakonfigurováno.
10. **Kontrola Optimalizace (Volitelné):** Periodicky spouští `OptimizationService` k analýze výkonu a potenciálnímu navržení nebo aplikaci úprav parametrů.
11. **Smyčka:** Opakuje cyklus.

## ⚙️ Konfigurace

Chování Orchestrační Služby je ovlivněno proměnnými prostředí definovanými v `.env`, jako jsou:

*   `TRADING_FREQUENCY_MINUTES`: Ovládá, jak často běží hlavní obchodní cyklus.
*   `MARKET_OPEN_CHECK_ENABLED`: Přepíná kontrolu tržních hodin.
*   `TRADING_SYMBOLS`: Určuje, na která aktiva se systém zaměřuje.

## 🔗 Klíčové Interakce

*   **`main.py` ▶️:** Instanciuje a spouští `OrchestrationDaemon`.
*   **Všechny ostatní Služby:** Démon drží reference na a volá metody AI, Exekuční, Paměťové a Optimalizační služby.
*   **Rozhraní 🔌:** Používá rozhraní Brokera, LLM a Notifikací (často nepřímo prostřednictvím služeb).
*   **`config.py` ⚙️:** Čte nastavení konfigurace.
*   **`logger.py` 📝:** Používá centrální logger pro záznam událostí.
