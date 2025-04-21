# 🌐 Rozhraní Webových Dat (Web Data Interface)

## 📝 Přehled

`WebDataInterface` (`src/interfaces/web_data.py`) definuje standardní kontrakt pro získávání a potenciálně parsování dat z externích webových zdrojů, jako jsou finanční zpravodajské weby, ekonomické kalendáře nebo agregátory sentimentu sociálních médií.

## 🎯 Účel

*   Abstrahovat proces získávání informací z různých webových zdrojů (např. scraping webových stránek, volání specifických zpravodajských API).
*   Poskytnout konzistentní způsob, jak mohou služby (primárně `AIService`) přistupovat k externím informacím, které by mohly ovlivnit obchodní rozhodnutí (např. titulky zpráv, skóre sentimentu, nadcházející ekonomické události).
*   Umožnit přidávání nových zdrojů webových dat vytvořením nových implementací rozhraní.
*   Usnadnit testování povolením mock (falešných) implementací, které vracejí vzorová webová data bez provádění živých HTTP požadavků.

## 🔑 Klíčové Metody (Koncepční)

`WebDataInterface` může definovat metody jako:

*   **`fetch_news(query: str, max_results: int)`:** Získá nedávné zpravodajské články související s konkrétním dotazem (např. symbol akcie, tržní sektor). Vrací seznam zpravodajských položek (např. titulky, shrnutí, URL, časová razítka).
*   **`fetch_economic_events(date_range: Tuple[date, date])`:** Načte naplánované ekonomické události (např. zveřejnění HDP, rozhodnutí o úrokových sazbách) v daném časovém rozmezí.
*   **`fetch_sentiment(symbol: str)`:** Pokusí se získat skóre sentimentu nebo související komentáře pro specifický obchodní symbol z nakonfigurovaného zdroje.

Přesné metody závisí na specifických potřebách `AIService` a integrovaných zdrojích dat.

## ⚙️ Implementace

Konkrétní implementace mohou zahrnovat:

*   `NewsAPIFetcher`: Používá komerční službu News API.
*   `WebScraper`: Implementuje logiku pro scraping specifických finančních webových stránek (vyžaduje pečlivé zacházení s podmínkami služby webových stránek a potenciálními změnami struktury).
*   `MockWebData`: Vrací předdefinovaná vzorová data zpráv nebo událostí pro testování.

`OrchestrationDaemon` nebo `AIService` by vybraly a instanciovaly příslušnou implementaci.

## ⚙️ Konfigurace

Implementace mohou vyžadovat:

*   API klíče pro komerční poskytovatele dat.
*   URL adresy webových stránek pro scraping.
*   Konfiguraci pro logiku parsování.

Tyto by byly typicky uloženy v souboru `.env`.

## 🔗 Klíčové Interakce

*   **`AIService` 🤖:** Pravděpodobně primární konzument, požadující externí data k obohacení kontextu poskytovaného LLM pro analýzu.
*   **`config.py` ⚙️:** Čte API klíče nebo URL potřebné pro implementaci.
*   **Externí Knihovny:** Může používat knihovny jako `requests`, `beautifulsoup4` (pro scraping) nebo specifické klientské knihovny API.
*   **`logger.py` 📝:** Loguje pokusy o získání webových dat a jejich výsledky.
