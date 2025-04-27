# ✨ Perun Trading System ✨

Vítejte v **Perun**, automatizovaném obchodním systému navrženém k využití síly velkých jazykových modelů (LLM) pro analýzu trhu a provádění obchodů. Perun analyzuje tržní data, generuje obchodní signály, spravuje portfolio a interaguje s API brokera, vše řízeno v rámci modulárního a konfigurovatelného frameworku. Pro hlubší pochopení konceptů a fungování systému si přečtěte [🌌 Koncepční Přehled](./docs/system_overview_cz.md).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Příklad odznaku -->

---

## 🚀 Funkce

*   🧠 **Analýza pomocí LLM:** Využívá LLM (OpenAI, Gemini) pro hlubokou analýzu trhu a generování signálů.
*   🔍 **Průzkum trhu:** Integruje Perplexity AI pro zprávy a analýzu sentimentu v reálném čase.
*   🤖 **Automatizovaný obchodní cyklus:** Plná automatizace od získávání dat po provedení příkazu a sledování portfolia.
*   🏦 **Integrace brokera:** Bezproblémové připojení k Alpaca pro tržní data, správu účtu a obchodování.
*   💾 **Perzistentní paměť:** Udržuje historii akcí, pozorování a poznatků pro informování budoucích rozhodnutí.
*   📢 **Notifikační systém:** Konfigurovatelná upozornění přes Mattermost a Email.
*   ⚙️ **Řízeno konfigurací:** Snadné přizpůsobení chování systému pomocí proměnných prostředí.
*   🧱 **Modulární architektura:** Oddělené služby pro lepší údržbu, testovatelnost a rozšiřitelnost.
*   📈 **Připraveno na optimalizaci:** Obsahuje komponenty pro analýzu výkonu a potenciální ladění parametrů.

---

## 🏗️ Přehled Architektury

Perun využívá architekturu orientovanou na služby, koordinovanou centrálním démonem:

*   **Orchestrační Služba (`OrchestrationDaemon`):** 🕰️ Hlavní řídicí smyčka, plánuje úkoly na základě tržních hodin a stavu systému. [Více Detailů](./docs/orchestration_service_cz.md)
*   **AI Služba (`AIServiceProcessor`):** 🤖 Interaguje s LLM (OpenAI/Gemini) a Perplexity pro analýzu dat a generování obchodních signálů. [Více Detailů](./docs/ai_service_cz.md)
*   **Exekuční Služba (`ExecutionManager`):** 💼 Spravuje veškeré interakce s brokerem (Alpaca), zpracovává příkazy a aktualizuje portfolio. [Více Detailů](./docs/execution_service_cz.md)
*   **Paměťová Služba (`MemoryStorage`, `MemoryOrganizer`):** 📚 Ukládá a načítá systémovou paměť (obchody, signály, logy, analýzy). [Více Detailů](./docs/memory_service_cz.md)
*   **Optimalizační Služba (`OptimizationEngine`, `FrequencyAnalyzer`):** 🛠️ Analyzuje výkon a navrhuje úpravy parametrů. [Více Detailů](./docs/optimization_service_cz.md)
*   **Rozhraní (Interfaces):** 🔌 Abstraktní vrstvy pro externí komunikaci:
    *   `BrokerageInterface`: Interakce s Alpaca. [Detaily](./docs/brokerage_interface_cz.md)
    *   `LLMInterface`: Interakce s OpenAI/Gemini. [Detaily](./docs/llm_interface_cz.md)
    *   `PerplexityInterface`: Interakce s Perplexity AI. (Viz `src/interfaces/perplexity.py`)
    *   `NotificationInterface`: Interakce s Mattermost/Email. [Detaily](./docs/notification_interface_cz.md)
    *   `WebDataInterface`: (Budoucí) Získávání externích webových dat. [Detaily](./docs/web_data_interface_cz.md)
*   **Modely:** 🧱 Základní datové struktury (`Order`, `Signal`, `Portfolio`, atd.).

[Obecné Koncepty Rozhraní](./docs/interfaces_cz.md)

---

## 🛠️ Nastavení & Konfigurace

Postupujte podle těchto kroků pro zprovoznění Peruna:

**1. Klonování Repozitáře:**
```bash
git clone https://github.com/david-strejc/perun.git
cd perun # Poznámka: Repozitář byl vytvořen jako 'perun' a obsahuje soubory 'trading_system' přímo
```

**2. Vytvoření & Aktivace Virtuálního Prostředí:**
```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (Git Bash/WSL)
python3 -m venv .venv
source .venv/Scripts/activate

# Windows (Příkazový řádek)
python -m venv .venv
.venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**3. Instalace Závislostí:**
```bash
pip install -r requirements.txt
```

**4. Konfigurace Proměnných Prostředí (`.env`):**

Vytvořte soubor `.env` v kořenovém adresáři projektu (`perun/`). Tento soubor ukládá vaše API klíče a nastavení konfigurace. **Nekomitujte tento soubor do Gitu.** Níže je šablona s podrobnými instrukcemi, kde najít každou požadovanou hodnotu.

```dotenv
#####################################################
# Konfigurace Prostředí Perun Trading System        #
# Podrobné instrukce pro získání přihlašovacích údajů #
#####################################################

# --- 🏦 Broker: Alpaca (Vyžadováno) ---
# Účel: Připojení k burze pro data a obchodování.
# Instrukce:
# 1. Registrace/Přihlášení: Jděte na https://alpaca.markets/ a vytvořte účet nebo se přihlaste.
# 2. Paper vs Live: Rozhodněte se, zda chcete testovat s fiktivními penězi (Paper Trading) nebo skutečnými (Live Trading). DŮRAZNĚ doporučujeme začít s Paper Trading.
# 3. Generování Klíčů:
#    - Přejděte na svůj dashboard (Paper nebo Live).
#    - Najděte sekci API Keys (často na pravé straně nebo v nastavení účtu).
#    - Klikněte na "Generate New Key" nebo podobné tlačítko.
#    - DŮLEŽITÉ: Okamžitě zkopírujte jak 'API Key ID', tak 'Secret Key'. Secret Key je zobrazen pouze jednou!
# 4. Nastavení URL:
#    - Pro Paper Trading: Použijte https://paper-api.alpaca.markets
#    - Pro Live Trading: Použijte https://api.alpaca.markets
ALPACA_API_KEY=VAS_ALPACA_KEY_ID_ZDE
ALPACA_SECRET_KEY=VAS_ALPACA_SECRET_KEY_ZDE
ALPACA_BASE_URL=https://paper-api.alpaca.markets # Začněte s Paper Trading!

# --- 🧠 LLM & Výzkumná API (Volitelné Klíče, Vyžadované Modely) ---
# Účel: Poskytnutí AI schopností pro analýzu a výzkum. Klíče potřebujete pouze pro služby, jejichž modely specifikujete níže.

# --- OpenAI ---
# Instrukce:
# 1. Registrace/Přihlášení: Jděte na https://platform.openai.com/
# 2. Navigace: Klikněte na ikonu/jméno svého profilu (vpravo nahoře).
# 3. API Klíče: Vyberte "View API keys" nebo přejděte do sekce "API Keys" (může být pod "Settings" nebo "Projects").
# 4. Vytvořit Klíč: Klikněte na "Create new secret key". Pojmenujte ho (např. "Perun Trading Bot").
# 5. Zkopírovat Klíč: Okamžitě zkopírujte vygenerovaný klíč (nebude znovu zobrazen) a vložte ho níže.
# 6. Platby: Používání OpenAI API vyžaduje přidání platebních údajů a je zpoplatněno podle využití.
OPENAI_API_KEY=VAS_OPENAI_KLIC_POKUD_POUZIVATE_OPENAI_MODELY

# --- Google Gemini ---
# Instrukce:
# 1. Jděte do Google AI Studio: Navštivte https://aistudio.google.com/app/apikey
# 2. Přihlášení: Přihlaste se svým Google účtem.
# 3. Vytvořit Klíč: Klikněte na "Create API key". Možná budete muset nejprve vytvořit nový projekt.
# 4. Zkopírovat Klíč: Zkopírujte vygenerovaný API klíč a vložte ho níže.
# 5. Limity Využití: Buďte si vědomi možných limitů bezplatné úrovně a souvisejících nákladů při vyšším využití.
GEMINI_API_KEY=VAS_GOOGLE_KLIC_POKUD_POUZIVATE_GEMINI_MODELY

# --- Perplexity AI ---
# Instrukce:
# 1. Registrace/Přihlášení: Jděte na https://perplexity.ai/
# 2. Navigace: Klikněte na ikonu svého profilu (vlevo dole), poté vyberte "API Keys" (nebo jděte do Settings -> API).
# 3. Fakturace (Pokud je vyžadována): Možná budete muset nejprve nastavit fakturační údaje. Postupujte podle pokynů na obrazovce.
# 4. Generovat Klíč: Klikněte na "Generate" nebo "Create New Key".
# 5. Zkopírovat Klíč: Zkopírujte vygenerovaný API klíč a vložte ho níže.
# 6. Ceny: Zkontrolujte detaily cen API Perplexity.
PERPLEXITY_API_KEY=VAS_PERPLEXITY_KLIC_POKUD_POUZIVATE_PERPLEXITY

# --- Výběr Modelu (Vyžadováno) ---
# Účel: Určení, které konkrétní AI modely má Perun používat pro různé úkoly.
# Instrukce: Vyberte modely kompatibilní s API klíči, které jste poskytli výše.
# Příklady: "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "sonar-small-online" (Perplexity)
# Ujistěte se, že vybrané modely jsou vhodné pro složitost úkolu a váš rozpočet.
TRADING_ANALYSIS_LLM_MODEL="gpt-4o" # Model pro hlavní obchodní rozhodnutí
MEMORY_ORGANIZATION_LLM_MODEL="gpt-3.5-turbo" # Zde lze často použít levnější/rychlejší model
OPTIMIZATION_LLM_MODEL="gpt-4o" # Model používaný optimalizační službou

# --- 📢 Notifikace (Volitelné) ---
# Účel: Příjem upozornění o obchodech, chybách nebo stavu systému.

# --- Mattermost ---
# Instrukce (Vyžaduje přístup k Mattermost serveru):
# 1. Povolit Boty: Systémový administrátor musí povolit Bot účty (System Console -> Integrations -> Bot Accounts).
# 2. Vytvořit Bota: Jako Admin jděte do Integrations -> Bot Accounts -> "Add Bot Account".
# 3. Vyplnit Detaily: Dejte botovi uživatelské jméno (např. "perun_bot"), popis.
# 4. Získat Token: Po vytvoření okamžitě zkopírujte vygenerovaný 'Token'. Toto je váš MATTERMOST_TOKEN.
# 5. Získat URL Serveru: Toto je webová adresa vaší Mattermost instance (např. https://vaspolecnost.mattermost.com).
# 6. Získat Team ID: Přejděte do týmu, ve kterém má bot být. Team ID je obvykle součástí URL (např. /team/TEAM_ID_ZDE/...).
# 7. Získat Channel ID: Přejděte do konkrétního kanálu pro notifikace. Channel ID je často v URL za team ID (např. /channels/CHANNEL_ID_ZDE).
MATTERMOST_ENABLED=false # Nastavte na true pro povolení
MATTERMOST_URL=https://vase.mattermost.instance.com
MATTERMOST_TOKEN=VAS_MATTERMOST_BOT_TOKEN_ZDE
MATTERMOST_TEAM_ID=VAS_MATTERMOST_TEAM_ID_ZDE
MATTERMOST_CHANNEL_ID=VAS_CILOVY_CHANNEL_ID_ZDE

# --- Email (SMTP) ---
# Instrukce: Použijte SMTP údaje od vašeho poskytovatele emailu (např. Gmail, Seznam, Outlook).
# 1. Najít SMTP Nastavení: Vyhledejte v nápovědě vašeho poskytovatele "SMTP nastavení".
# 2. Server & Port: Získejte adresu SMTP serveru (např. smtp.gmail.com, smtp.seznam.cz) a port (např. 587 pro TLS, 465 pro SSL).
# 3. Přihlašovací Údaje:
#    - Uživatelské jméno: Obvykle vaše plná emailová adresa.
#    - Heslo: Může to být vaše běžné heslo k emailu NEBO "Heslo pro aplikace". Pro Gmail/Google Workspace s 2FA MUSÍTE vygenerovat Heslo pro aplikace (Hledejte "Google Hesla pro aplikace"). Použití Hesla pro aplikace je bezpečnější.
# 4. Admin Email: Emailová adresa, kam mají být notifikace zasílány.
EMAIL_ENABLED=false # Nastavte na true pro povolení
SMTP_SERVER=smtp.priklad.com
SMTP_PORT=587
SMTP_USERNAME=vas_email@priklad.com
SMTP_PASSWORD=vase_heslo_k_emailu_nebo_heslo_pro_aplikace
ADMIN_EMAIL=email_prijemce@priklad.com

# --- 📁 Cesty k Souborům (Vyžadováno - Relativní ke kořenu projektu) ---
# Účel: Definování, kam Perun ukládá svá data a nachází své prompty. Výchozí hodnoty jsou obvykle v pořádku.
MEMDIR_PATH=data/memdir
LOG_PATH=data/logs
PROMPTS_PATH=prompts

# --- 📈 Obchodní Parametry (Vyžadováno) ---
# Účel: Definování základního obchodního chování a pravidel řízení rizika.
DEFAULT_SYMBOLS=AAPL,MSFT,GOOG # Čárkou oddělený seznam symbolů k obchodování
MAX_POSITION_SIZE=10000 # Maximální hodnota (USD) na pozici
MAX_TOTAL_POSITIONS=5 # Maximální počet souběžně otevřených pozic
RISK_LIMIT_PERCENT=0.02 # Max. riziko na obchod jako % ekvity portfolia (např. 0.02 = 2%)

# --- 📝 Konfigurace Logování (Volitelné - Výchozí hodnoty poskytnuty) ---
# Účel: Ovládání úrovně detailů logování do konzole a souborů.
LOG_LEVEL_CONSOLE=INFO # Možnosti: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL_FILE=DEBUG
LOG_FILE_NAME=trading_system.log # Název log souboru v LOG_PATH

# --- 🛠️ Optimalizační Parametry (Vyžadováno, pokud OPTIMIZATION_ENABLED=true) ---
# Účel: Konfigurace funkcí samooptimalizace.
OPTIMIZATION_ENABLED=true # Nastavte na false pro zakázání optimalizačních běhů
OPTIMIZATION_SCHEDULE=daily # Jak často spouštět optimalizaci (např. 'daily', 'weekly', nebo cron: '0 3 * * 0' pro 3:00 v neděli)
OPTIMIZATION_PROMPT_THRESHOLD=0.05 # Min. zlepšení výkonu (např. 5%) potřebné k automatickému přepnutí promptu
OPTIMIZATION_MIN_FREQUENCY=60 # Minimální obchodní frekvence (sekundy) povolená optimalizací
OPTIMIZATION_FREQUENCY_BUFFER_FACTOR=1.5 # Násobitel bezpečnostní rezervy pro výpočet frekvence
OPTIMIZATION_MEMORY_QUERY_DAYS=30 # Kolik dní historie dotazovat pro optimalizační analýzu

# --- 💾 Konfigurace Paměťové Služby (Vyžadováno) ---
# Účel: Konfigurace správy systémové paměti.
MEMDIR_PRUNE_MAX_AGE_DAYS=90 # Smazat paměťové soubory starší než toto (0 pro zakázání promazávání podle věku)
MEMDIR_PRUNE_MAX_COUNT=100000 # Max. počet paměťových souborů k uchování (0 pro zakázání promazávání podle počtu)
MEMDIR_ORGANIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2 # Model pro tagování/podobnost paměti (běží lokálně)

# --- 🕰️ Orchestrační Služba (Vyžadováno) ---
# Účel: Konfigurace časování hlavní řídicí smyčky.
MAIN_LOOP_SLEEP_INTERVAL=1 # Interval spánku (sekundy) při nečinnosti (např. mimo tržní hodiny)
LIQUIDATE_ON_CLOSE=false # Nastavte na true pro likvidaci všech pozic před uzavřením trhu
```

---

## ▶️ Použití

Ujistěte se, že máte aktivní virtuální prostředí a soubor `.env` je správně nakonfigurován. Spusťte hlavní orchestrační démon z kořenového adresáře projektu (`perun/`):

```bash
python main.py
```

Systém inicializuje všechny služby a zahájí svůj operační cyklus. Sledujte výstup konzole a log soubory (`data/logs/trading_system.log`) pro aktualizace stavu a potenciální problémy.

---

## 📁 Struktura Projektu

```
perun/
├── .env                # Proměnné prostředí (citlivé, NEKOMITOVAT)
├── .git/               # Git data repozitáře
├── .gitignore          # Soubory ignorované Gitem
├── .venv/              # Python virtuální prostředí (ignorováno)
├── data/               # Úložiště dat (logy, paměť - výchozí ignorováno)
│   ├── logs/           # Log soubory (.gitkeep pro zachování adresáře)
│   └── memdir/         # Perzistentní paměťové úložiště (.gitkeep pro zachování adresáře)
├── docs/               # Podrobná dokumentace konceptů/komponent
│   ├── ai_service.md
│   ├── brokerage_interface.md
│   ├── execution_service.md
│   ├── interfaces.md
│   ├── llm_interface.md
│   ├── memory_service.md
│   ├── notification_interface.md
│   ├── optimization_service.md
│   ├── orchestration_service.md
│   └── web_data_interface.md
├── prompts/            # Prompty pro LLM
│   ├── evaluation/
│   ├── memory_organization/
│   ├── trading/
│   └── metadata.json
├── scripts/            # Pomocné skripty
│   └── check_market_hours.py
├── src/                # Zdrojový kód
│   ├── __init__.py
│   ├── config.py       # Načítání konfigurace
│   ├── interfaces/     # Rozhraní k externím službám
│   ├── models/         # Datové modely (Pydantic)
│   ├── services/       # Služby s hlavní logikou
│   └── utils/          # Pomocné funkce (Logování, Výjimky)
├── tests/              # Unit a integrační testy
│   ├── __init__.py
│   ├── interfaces/
│   ├── services/
│   └── utils/
├── main.py             # Hlavní vstupní bod aplikace
├── README.md           # Tento soubor (Anglicky)
├── README_cz.md        # Tento soubor (Česky)
├── requirements.txt    # Python závislosti
└── repomix-output.txt  # (Volitelné) Výstup z nástrojů pro analýzu kódu
```

---

## 🧪 Vývoj & Testování

*   Ujistěte se, že máte nainstalované vývojové závislosti (`pip install -r requirements.txt`).
*   Spusťte testy pomocí `pytest` z kořenového adresáře projektu (`perun/`):
    ```bash
    pytest
    ```
*   Zvažte použití pre-commit hooks pro formátování kódu a linting.

---

## 🤝 Přispívání

Příspěvky jsou vítány! Prosím, dodržujte standardní postupy fork-and-pull-request. Ujistěte se, že testy procházejí a kód dodržuje standardy projektu. (Další detaily mohou být přidány).

---

## 📜 Licence

Tento projekt je licencován pod licencí MIT - viz soubor [LICENSE](LICENSE) pro detaily (předpokládá se MIT, v případě potřeby přidejte soubor LICENSE).
