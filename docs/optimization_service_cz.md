# 🛠️ Optimalizační Služba (Optimization Service)

## 📝 Přehled

Optimalizační Služba, potenciálně implementovaná napříč třídami jako `OptimizationEngine` (`src/services/optimization_service/engine.py`) a `FrequencyAnalyzer` (`src/services/optimization_service/frequency_analyzer.py`), je navržena k analýze výkonu obchodního systému a navrhování nebo automatické aplikaci úprav jeho parametrů za účelem zlepšení výsledků. Jedná se o pokročilou funkci, jejímž cílem je učinit systém adaptivním.

## 🎯 Odpovědnosti

*   **Analýza Výkonu 📊:** Analyzuje historická data o obchodním výkonu uložená v `MemoryService`. To může zahrnovat výpočet metrik jako:
    *   Poměr ziskových/ztrátových obchodů (Win/loss ratio)
    *   Faktor zisku (Profit factor)
    *   Sharpe ratio
    *   Maximální pokles (Maximum drawdown)
    *   Frekvence obchodování vs. ziskovost
*   **Ladění Parametrů ⚙️:** Na základě analýzy výkonu identifikuje parametry, které by mohly být upraveny pro potenciální zlepšení. Příklady zahrnují:
    *   `TRADING_FREQUENCY_MINUTES`: Nalezení optimální frekvence pro analýzu a obchodování.
    *   `TRADE_RISK_PER_TRADE`: Úprava úrovní rizika na základě volatility trhu nebo výkonu.
    *   Parametry v rámci promptů nebo logiky AI Služby.
    *   Specifické prahové hodnoty používané při generování signálů nebo exekuci.
*   **Návrh/Aplikace ✨:** Buď navrhuje změny parametrů uživateli (prostřednictvím notifikací), nebo, pokud je nakonfigurováno, automaticky aktualizuje konfiguraci systému nebo interní stav novými hodnotami parametrů.
*   **Analýza Frekvence (`FrequencyAnalyzer`) ⏱️:** Specifická komponenta pravděpodobně zaměřená na určení nejefektivnější `TRADING_FREQUENCY_MINUTES` analýzou korelace ziskovosti s tím, jak často systém obchoduje.

## 🔄 Pracovní Postup (Workflow)

1.  **Spouštěč:** `OrchestrationDaemon` periodicky spouští `OptimizationEngine` (např. denně, týdně).
2.  **Načtení Dat:** `OptimizationEngine` dotazuje `MemoryService` k načtení historických obchodních dat, tržních podmínek a potenciálně hodnot systémových parametrů použitých během těchto obchodů.
3.  **Analýza:** Provádí výpočty a analýzu historických dat. To může zahrnovat specifické komponenty jako `FrequencyAnalyzer`.
4.  **Identifikace Zlepšení:** Určuje, zda by změna určitých parametrů (jako frekvence obchodování) mohla vést k lepšímu výkonu na základě analýzy.
5.  **Generování Doporučení:** Formuluje doporučení pro nové hodnoty parametrů.
6.  **Hlášení/Aplikace:**
    *   Odesílá doporučení prostřednictvím `NotificationInterface`.
    *   NEBO, pokud je povoleno automatické ladění, aktualizuje konfiguraci systému nebo stav za běhu (to vyžaduje pečlivou implementaci, aby se zabránilo nestabilitě).

## ⚙️ Konfigurace

*   **Plán Optimalizace:** Jak často běží optimalizační analýza (pravděpodobně spravováno v rámci `OrchestrationDaemon`).
*   **Parametry Analýzy:** Specifické metriky nebo prahové hodnoty používané optimalizační logikou.
*   **Příznak Auto-Ladění:** Booleovská konfigurace (`OPTIMIZATION_AUTO_APPLY`?) pro povolení/zakázání automatických aktualizací parametrů.

## 🔗 Klíčové Interakce

*   **`OrchestrationDaemon` 🕰️:** Spouští optimalizační proces. Může přijímat aktualizované parametry, pokud je povoleno automatické ladění.
*   **`MemoryService` 💾:** Načítá historická data o výkonu.
*   **`NotificationInterface` 📢:** Odesílá zprávy nebo doporučení.
*   **`config.py` ⚙️:** Může číst nastavení specifická pro optimalizaci nebo potenciálně aktualizovat konfiguraci, pokud automatické ladění upravuje `.env` nebo proměnné za běhu.
*   **`logger.py` 📝:** Loguje výsledky analýzy a změny parametrů.
*   **Potenciálně další Služby:** Pokud ladí parametry specifické pro AI nebo Exekuci, může s těmito službami interagovat nebo je ovlivňovat nepřímo.
