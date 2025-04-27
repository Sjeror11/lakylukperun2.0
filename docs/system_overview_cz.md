# 🌌 Perun Trading System: Koncepční Přehled

Vítejte u koncepčního přehledu Perun Trading System! Tento dokument si klade za cíl vysvětlit *proč* a *jak* za systémem Perun způsobem, který je přístupný, i když jste nováčkem v automatizovaném obchodování, programování nebo AI.

---

## 🎯 Jaký je Cíl Peruna?

V srdci je Perun **experimentální automatizovaný obchodní asistent**. Jeho primárním cílem je:

1.  **Analyzovat Finanční Trhy:** 📈 Neustále monitorovat tržní data (jako ceny akcií).
2.  **Generovat Obchodní Nápady:** 💡 Používat umělou inteligenci (konkrétně velké jazykové modely - LLM) v kombinaci s průzkumem trhu (jako Perplexity AI) k formování názorů nebo "signálů" o tom, zda koupit nebo prodat konkrétní aktiva (jako akcie).
3.  **Provádět Obchody:** 🤖 Automaticky zadávat nákupní nebo prodejní příkazy u připojeného brokera (jako Alpaca) na základě generovaných signálů.
4.  **Řídit Riziko:** 🛡️ Fungovat v rámci předdefinovaných limitů rizika k ochraně kapitálu.
5.  **Učit se & Adaptovat:** 🧠 Používat paměťový systém k zaznamenávání svých akcí a výsledků a potenciálně využívat tyto informace k optimalizaci svých strategií v průběhu času.

Myslete na Peruna ne jako na zaručený stroj na vydělávání peněz, ale jako na framework pro zkoumání, jak lze moderní AI aplikovat na komplexní výzvu obchodování na finančních trzích.

---

## 🤔 Jak Perun Rozhoduje, Co Obchodovat? (Obchodní Logika)

Perun se nespoléhá na tradiční, pevná obchodní pravidla (jako "kup, když klouzavý průměr X překříží klouzavý průměr Y"). Místo toho používá dynamičtější přístup řízený AI:

**Základní Cyklus:**

```ascii
+-------------------+      +---------------------+      +--------------------+      +----------------------+      +---------------------+
| 1. Sběr Dat       | ---> | 2. AI Analýza       | ---> | 3. Generování Sign.| ---> | 4. Posouzení Rizika  | ---> | 5. Provedení Přík.  |
| (Ceny, Portfolio) |      | (LLM + Perplexity)  |      | (Koupit/Prodat?)   |      | (Velikost Pozice)    |      | (Přes API Brokera)  |
+-------------------+      +---------------------+      +--------------------+      +----------------------+      +---------------------+
        ^                                                                                                                  |
        |-----------------------------------< Smyčka >---------------------------------------------------------------------+
```

1.  **Sběr Dat 📊:** Systém získává nejnovější tržní ceny pro akcie, které má sledovat (např. AAPL, MSFT). Také kontroluje aktuální stav vlastního obchodního účtu (hotovost, existující pozice) prostřednictvím **Rozhraní Brokera** (Alpaca).
2.  **AI Analýza 🧠:** Zde se děje kouzlo!
    *   **Průzkum Trhu (Volitelné):** Může se nejprve zeptat **Perplexity AI** na nedávné zprávy nebo sentiment ohledně cílových akcií (`"Jaké jsou poslední zprávy o akciích MSFT?"`).
    *   **Promptování LLM:** Všechna shromážděná data (tržní ceny, stav portfolia, nedávná historie z paměti, poznatky z Perplexity) jsou naformátována do podrobného textového promptu. Tento prompt je odeslán výkonnému **Velkému Jazykovému Modelu (LLM)** jako OpenAI GPT-4 nebo Google Gemini prostřednictvím **LLM Rozhraní**. Prompt se v podstatě ptá LLM: *"Vzhledem ke všem těmto informacím, jakou obchodní akci (pokud vůbec nějakou) doporučuješ pro kterou akcii a proč?"*
3.  **Generování Signálu 💡:** LLM zpracuje prompt a (doufejme) vrátí strukturovanou odpověď, typicky ve formátu JSON, udávající:
    *   `action`: BUY (koupit), SELL (prodat), nebo HOLD (držet).
    *   `symbol`: Ticker akcie (např. AAPL).
    *   `confidence`: Jak jistý si LLM je (např. 0.8 pro 80% jistotu).
    *   `rationale`: Odůvodnění LLM.
    **AI Služba** tuto odpověď zpracuje. Pokud je to platný signál BUY nebo SELL s dostatečnou jistotou, stane se formálním `TradingSignal`.
4.  **Posouzení Rizika 🛡️:** Před provedením akce na základě signálu **Exekuční Služba** zkontroluje přednastavená pravidla definovaná v konfiguraci (soubor `.env`):
    *   *Je dostatečná kupní síla?*
    *   *Překračuje tento obchod maximální povolenou velikost pro jednu pozici?*
    *   *Máme již maximální počet otevřených pozic?*
    *   *Vejde se potenciální ztráta do limitu rizika na obchod?*
    Pokud je obchod podle pravidel příliš riskantní, je zamítnut.
5.  **Provedení Příkazu 🤖:** Pokud je signál platný a projde posouzením rizika, **Exekuční Služba** odešle příkaz (např. "Kup 10 akcií AAPL") **Rozhraní Brokera** (Alpaca) k zadání na reálný trh.

Celý tento cyklus se opakuje v nakonfigurovaném intervalu (např. každých pár minut nebo hodin) během otevíracích hodin trhu.

---

## 💾 Jak si Perun Pamatuje? (Správa Paměti)

Obchodní rozhodnutí jsou často lepší, když jsou informována minulými událostmi. Perun má **Paměťovou Službu** navrženou k ukládání a načítání důležitých informací:

**Co se Ukládá?**

*   **Obchody:** Záznamy každého zadaného nákupního a prodejního příkazu.
*   **Signály:** Obchodní signály generované AI Službou.
*   **Analýzy:** Prompty odeslané LLM a přijaté syrové odpovědi.
*   **Snímky Trhu:** Periodické snímky tržních dat.
*   **Snímky Portfolia:** Periodické snímky stavu účtu.
*   **Chyby:** Jakékoli chyby, na které systém narazil.
*   **Log Zprávy:** Důležité události logované různými službami.

**Jak se Ukládá?**

*   Každá informace je uložena jako objekt `MemoryEntry`.
*   Tyto záznamy jsou typicky uloženy jako jednotlivé soubory (např. JSON soubory) ve vyhrazeném adresáři (`data/memdir/`). Jedná se o jednoduchý, ale pro tento systém efektivní přístup.

**Jak se Používá?**

*   **Kontext pro AI:** Když **AI Služba** připravuje svůj prompt pro LLM, může se dotázat **Paměťové Služby** na nedávnou relevantní historii (např. "Ukaž mi posledních 5 obchodů a signálů pro AAPL"). To dává LLM kontext nad rámec okamžitého snímku trhu.
*   **Optimalizace:** **Optimalizační Služba** může analyzovat dlouhodobou paměť (např. týdny nebo měsíce obchodů a signálů) k vyhodnocení výkonu strategie.
*   **Ladění (Debugging):** Vývojáři mohou prozkoumat paměťové soubory, aby pochopili, proč systém učinil určitá rozhodnutí nebo narazil na chyby.

**Organizace:**

*   Komponenta `MemoryOrganizer` (potenciálně využívající jednodušší modely jako `sentence-transformers`) může pomoci tagovat nebo kategorizovat paměťové záznamy, což usnadňuje pozdější nalezení relevantních informací.

```ascii
+---------------------+      +-------------------------+      +---------------------+
|   Ostatní Služby    | ---> |   Paměťová Služba       | <--- |   Ostatní Služby    |
| (AI, Exekuce atd.)  |      |   (Úložiště/Organiz.)   |      | (AI, Optimalizace)  |
|   [Uložit Paměť]    |      +-------------------------+      |   [Dotaz na Paměť]  |
+---------------------+      | - Ukládá Obchody        |      +---------------------+
                           | - Ukládá Signály        |
                           | - Ukládá Analýzy        |
                           | - Ukládá Chyby          |
                           | - Organizuje/Taguje Data|
                           +-------------------------+
```

---

## 🚀 Jak se Perun Snaží Zlepšovat? (Samooptimalizace)

Perun zahrnuje **Optimalizační Službu** navrženou k periodickému přezkoumávání vlastního výkonu a potenciální úpravě své strategie. Jedná se o pokročilou funkci, která může zahrnovat:

1.  **Přezkoumání Výkonu:** 📊 Pravidelně (např. denně nebo týdně, na základě `OPTIMIZATION_SCHEDULE`) služba analyzuje historická data z **Paměťové Služby**. Zkoumá ziskovost minulých obchodů generovaných specifickými prompty nebo konfiguracemi.
2.  **Hodnocení Strategie:** 🤔 Může porovnávat výkon aktuálního obchodního promptu s alternativními prompty (potenciálně generovanými jiným LLM nebo předdefinovanými uživatelem).
3.  **Ladění Parametrů:** ⚙️ Mohlo by analyzovat, zda změna parametrů jako `RISK_LIMIT_PERCENT` nebo seznamu `DEFAULT_SYMBOLS` mohla historicky vést k lepším výsledkům. Může také analyzovat ideální frekvenci obchodování pomocí `FrequencyAnalyzer`.
4.  **Provádění Úprav:** ✨ Pokud analýza naznačuje jasné zlepšení (např. nový prompt konzistentně překonává starý o více než `OPTIMIZATION_PROMPT_THRESHOLD`), služba může automaticky:
    *   Aktualizovat systém, aby používal lépe fungující prompt.
    *   Navrhnout změny konfiguračních parametrů (ačkoli automatické změny v `.env` jsou složité a mohou vyžadovat manuální zásah).

**Důležitá Poznámka:** Skutečná samooptimalizace je velmi komplexní. Optimalizační schopnosti Peruna jsou pravděpodobně zaměřeny na specifické oblasti, jako je výkon promptů nebo analýza frekvence obchodování, spíše než na kompletní přepracování jeho základní logiky.

```ascii
+---------------------+      +---------------------+      +---------------------+
|   Paměťová Služba   | ---> | Optimalizační Sl.   | ---> | Konfigurace/Stav    |
| (Historická Data)   |      | (Analýza Výkonu,    |      | (Aktual. Promptů,   |
+---------------------+      |  Hodnocení Strat.)  |      |  Návrh Param.)      |
                           +---------------------+      +---------------------+
```

---

## 🏁 Závěr

Perun je sofistikovaný systém integrující tržní data, interakce s brokerem, více nástrojů AI (LLM, Perplexity), paměť a koncepty optimalizace. Jeho modulární design umožňuje experimentování a rozšíření. Pochopením těchto základních konceptů – obchodního cyklu řízeného AI, důležitosti paměti a potenciálu pro optimalizaci – můžete lépe pochopit, jak Perun funguje a jak jej můžete konfigurovat, spouštět nebo dokonce přispívat k jeho vývoji. Nezapomeňte začít s paper tradingem a pochopit související rizika!
