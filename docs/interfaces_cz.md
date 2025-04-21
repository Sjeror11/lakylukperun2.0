# 🔌 Rozhraní (Interfaces)

## 📝 Přehled

Rozhraní v Perun Trading System (`src/interfaces/`) definují standardizované kontrakty pro interakci s externími službami nebo komponentami, jejichž specifické implementace se mohou lišit. Fungují jako abstraktní vrstvy, oddělující základní logiku aplikace od konkrétních detailů externích systémů, jako jsou brokeři, velké jazykové modely (LLM) nebo notifikační platformy.

## 🎯 Účel

*   **Oddělení (Decoupling):** Umožňuje základním službám (`AIService`, `ExecutionService` atd.) pracovat s různými externími systémy bez změny jejich interní logiky. Například `ExecutionService` interaguje s `BrokerageInterface`, nikoli přímo s API Alpaca nebo API jiného konkrétního brokera.
*   **Flexibilita & Rozšiřitelnost:** Usnadňuje výměnu implementací nebo přidání podpory pro nové externí služby. Pro podporu nového brokera by stačilo vytvořit novou třídu implementující `BrokerageInterface`.
*   **Testovatelnost:** Umožňuje snadnější testování povolením použití mock (falešných) implementací (stubů nebo fakes) těchto rozhraní během unit nebo integračního testování. Tím se zabrání závislosti na živých externích API během testů.

## 🔑 Klíčová Rozhraní

Systém definuje několik klíčových rozhraní:

*   **`BrokerageInterface` 🏦:** Definuje metody pro interakci s obchodním brokerem (např. získávání tržních dat, informací o účtu, zadávání příkazů, kontrola stavu příkazů).
*   **`LLMInterface` 💬:** Definuje metody pro interakci s velkým jazykovým modelem (např. odesílání promptů, přijímání dokončení/odpovědí).
*   **`NotificationInterface` 📢:** Definuje metody pro odesílání oznámení nebo upozornění (např. odeslání zprávy do Mattermostu, emailu, SMS).
*   **`WebDataInterface` (Implikované/Potenciální) 🌐:** Mohlo by definovat metody pro získávání externích dat, jako jsou zpravodajské články nebo ekonomické ukazatele z webových zdrojů.

Každé rozhraní typicky specifikuje signatury metod (názvy funkcí, argumenty, návratové typy), které musí konkrétní implementace dodržovat. Skutečné implementace (např. `AlpacaBrokerage`, `OpenAILLM`, `MattermostNotifier`) by sídlily v adresáři `interfaces` nebo podadresářích a obsahovaly by specifickou logiku a volání API pro danou konkrétní službu. `OrchestrationDaemon` obvykle vybírá a instanciuje konkrétní implementace na základě nastavení konfigurace při spuštění.
