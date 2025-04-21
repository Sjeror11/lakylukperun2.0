# 🤖 AI Služba

## 📝 Přehled

AI Služba, primárně implementovaná ve třídě `AIProcessor` (`src/services/ai_service/processor.py`), je klíčovou komponentou zodpovědnou za využití velkých jazykových modelů (LLM) k analýze tržních podmínek a generování obchodních signálů. Funguje jako most mezi syrovými tržními daty/kontextem a akčními obchodními rozhodnutími.

## 🎯 Odpovědnosti

*   **Interakce s LLM 💬:** Spravuje komunikaci s nakonfigurovaným LLM prostřednictvím `LLMInterface`. To zahrnuje formátování promptů, odesílání požadavků a parsování odpovědí.
*   **Kontextuální Analýza 📊:** Přijímá vstupní data poskytnutá `OrchestrationDaemon`, která typicky zahrnují:
    *   Aktuální tržní data (objekty `MarketData`) pro relevantní symboly.
    *   Nedávný stav portfolia (objekt `Portfolio`).
    *   Relevantní historický kontext získaný z `MemoryService` (např. nedávné obchody, minulá tržní pozorování, předchozí poznatky LLM).
    *   Potenciálně externí data jako titulky zpráv (pokud je implementováno a používáno `WebDataInterface`).
*   **Prompt Engineering ✍️:** Konstruuje efektivní prompty pro LLM na základě dostupného kontextu a specifického cíle (např. "Analyzuj sentiment pro AAPL na základě nedávných zpráv a cenové akce", "Generuj signál koupit/prodat/držet pro MSFT"). Prompty jsou pravděpodobně uloženy a spravovány v adresáři `prompts/`.
*   **Generování Signálů 💡:** Interpretuje odpověď LLM k identifikaci potenciálních obchodních příležitostí. Překládá analýzu LLM (která může být textová) do strukturovaných objektů `Signal` (např. KOUPIT AAPL za tržní cenu, PRODAT MSFT s limitní cenou X).
*   **Posouzení Rizika (Potenciální) 🛡️:** Může zahrnovat základní parametry rizika (jako `TRADE_RISK_PER_TRADE` z konfigurace) při formulování signálů, ačkoli konečné řízení rizika může sídlit v `ExecutionService`.
*   **Zpracování Chyb ❌:** Spravuje potenciální chyby během interakce s LLM (např. chyby API, time-outy, špatně formátované odpovědi).

## 🔄 Pracovní Postup (Workflow)

1.  **Přijetí Požadavku:** `OrchestrationDaemon` zavolá metodu na `AIProcessor` (např. `process_data_and_generate_signals`), poskytující potřebná tržní data a kontext.
2.  **Příprava Kontextu:** `AIProcessor` uspořádá přijatá data a načte relevantní prompty.
3.  **Sestavení Promptu:** Vytvoří finální řetězec(e) promptu, který(é) bude(ou) odeslán(y) LLM.
4.  **Volání LLM:** Použije `LLMInterface` k odeslání promptu(ů) na nakonfigurované LLM API (např. OpenAI, Google Gemini).
5.  **Přijetí & Parsování Odpovědi:** Získá odpověď od LLM. Zpracuje odpověď k extrakci smysluplných informací a potenciálních obchodních instrukcí.
6.  **Generování Signálů:** Přeloží zpracované informace do jednoho nebo více objektů `Signal`, včetně symbolu, akce (koupit/prodat), množství/rizika, typu příkazu atd.
7.  **Vrácení Signálů:** Vrátí seznam vygenerovaných objektů `Signal` službě `OrchestrationDaemon`.

## ⚙️ Konfigurace

Chování AI Služby závisí na:

*   **API Klíčích LLM 🔑:** (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, atd.) definovaných v `.env`.
*   **Vybraném LLM:** Konkrétní implementaci `LLMInterface` (např. `OpenAILLM`, `GoogleLLM`).
*   **Promptech 📜:** Obsahu a struktuře souborů v adresáři `prompts/`.
*   **Obchodních Symbolech:** (`TRADING_SYMBOLS`) pro zaměření analýzy.

## 🔗 Klíčové Interakce

*   **`OrchestrationDaemon` 🕰️:** Přijímá data od a vrací signály démonovi.
*   **`LLMInterface` 💬:** Používá toto rozhraní ke komunikaci se skutečným LLM API.
*   **`MemoryService` 💾:** Může dotazovat paměťovou službu (přímo nebo nepřímo přes démona) na historický kontext.
*   **Model `Signal` 💡:** Vytváří instance datového modelu `Signal`.
*   **Modely `MarketData`, `Portfolio` 📈💼:** Konzumuje tyto datové modely jako vstup.
*   **`config.py` ⚙️:** Čte API klíče LLM a potenciálně další související konfigurace.
*   **`logger.py` 📝:** Loguje aktivity, prompty a odpovědi.
