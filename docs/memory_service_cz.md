# 💾 Paměťová Služba (Memory Service)

## 📝 Přehled

Paměťová Služba je zodpovědná za perzistentní ukládání a načítání informací relevantních pro provoz a rozhodovací proces obchodního systému. Funguje jako dlouhodobá paměť systému, což mu umožňuje učit se z minulých událostí a udržovat kontext v průběhu času. Tato služba se typicky skládá ze dvou hlavních částí: úložiště a organizace, implementovaných v `MemoryStorage` (`src/services/memory_service/storage.py`) a `MemoryOrganizer` (`src/services/memory_service/organizer.py`).

## 🎯 Odpovědnosti

*   **Perzistence Dat (`MemoryStorage`):**
    *   Zpracovává nízkoúrovňové čtení a zápis dat na perzistentní úložné médium (např. soubory na disku v adresáři `data/memdir/`, databáze).
    *   Ukládá různé typy informací jako objekty `MemoryEntry` nebo podobné struktury, včetně:
        *   Snímků tržních dat.
        *   Generovaných signálů.
        *   Zadaných a provedených příkazů.
        *   Promptů a odpovědí LLM.
        *   Systémových událostí a chyb.
        *   Snímků portfolia.
    *   Zajišťuje spolehlivé uložení dat.
*   **Organizace & Načítání Dat (`MemoryOrganizer`):**
    *   Poskytuje funkce vyšší úrovně pro dotazování a strukturování uložené paměti.
    *   Může používat techniky jako sémantické vyhledávání (např. pomocí sentence transformers, jak je naznačeno v `requirements.txt`) k nalezení relevantních minulých záznamů na základě aktuálního kontextu.
    *   Organizovává paměť, potenciálně ji shrnuje nebo kategorizuje.
    *   Poskytuje relevantní kontext službě `OrchestrationDaemon` nebo `AIService` na vyžádání (např. "načti posledních 5 obchodů pro AAPL", "najdi nedávné tržní komentáře týkající se GOOG").
*   **Poskytování Kontextu:** Dodává historická data a kontext ostatním službám, zejména `AIService`, pro informování její analýzy a generování signálů.

## 🔄 Pracovní Postup (Workflow)

**Ukládání:**

1.  **Přijetí Dat:** Jiná služba (např. Orchestration, AI, Execution) generuje data k uložení (např. nový příkaz, odpověď LLM).
2.  **Formátování Dat:** Data jsou naformátována do `MemoryEntry` nebo vhodné struktury.
3.  **Uložení Dat:** Komponenta `MemoryStorage` zapíše naformátovaná data do perzistentního úložiště (např. připojí k log souboru, uloží nový soubor, vloží do databázové tabulky).

**Načítání:**

1.  **Přijetí Dotazu:** `OrchestrationDaemon` nebo `AIService` požaduje specifické historické informace nebo kontext od `MemoryOrganizer`. Dotaz může být založen na čase, události nebo sémantice.
2.  **Dotaz do Úložiště:** `MemoryOrganizer` interaguje s `MemoryStorage` k načtení potenciálně relevantních syrových dat.
3.  **Zpracování & Filtrování:** `MemoryOrganizer` zpracuje syrová data, potenciálně pomocí embedding modelů nebo jiné logiky k filtrování, řazení nebo shrnutí informací na základě dotazu.
4.  **Vrácení Kontextu:** Organizovaný a relevantní kontext je vrácen žádající službě.

## ⚙️ Konfigurace

*   **Cesta k Úložišti:** Umístění pro perzistentní úložiště (např. `data/memdir/`) může být konfigurovatelné.
*   **Model Organizátoru (pokud je relevantní):** Pokud se používají embedding modely jako sentence-transformers, může být konfigurovatelný specifický použitý model.

## 🔗 Klíčové Interakce

*   **`OrchestrationDaemon` 🕰️:** Spouští ukládání událostí cyklu a požaduje kontext pro `AIService`.
*   **`AIService` 🤖:** Přijímá kontext od Paměťové Služby pro informování svých promptů a analýz. Může také spouštět ukládání vlastních interakcí (prompty/odpovědi).
*   **`ExecutionService` 💼:** Spouští ukládání zadání a provedení příkazů.
*   **Model `MemoryEntry` 🧱:** Používá tento datový model (nebo podobný) ke strukturování uložených informací.
*   **`config.py` ⚙️:** Může číst konfiguraci související s cestami k úložišti nebo modely organizátoru.
*   **`logger.py` 📝:** Loguje operace ukládání a načítání.
*   **Externí Knihovny:** Může používat knihovny jako `sentence-transformers`, `torch`, `transformers` pro komponentu `MemoryOrganizer`.
