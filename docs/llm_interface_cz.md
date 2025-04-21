# 💬 Rozhraní Velkého Jazykového Modelu (LLM Interface)

## 📝 Přehled

`LLMInterface` (`src/interfaces/large_language_model.py`) definuje standardní kontrakt pro interakci s různými velkými jazykovými modely (LLM), jako jsou ty poskytované OpenAI (řada GPT) nebo Google (řada Gemini). Abstrahuje specifické API endpointy, metody autentizace a formáty požadavků/odpovědí různých poskytovatelů LLM.

## 🎯 Účel

*   Abstrahovat detaily specifických LLM API (např. OpenAI API vs. Google Generative AI API).
*   Umožnit `AIService` používat různé LLM bez změny její základní logiky pro konstrukci promptů nebo interpretaci odpovědí.
*   Umožnit snadné přepínání mezi poskytovateli LLM na základě nákladů, výkonu nebo funkcí změnou konfigurace.
*   Usnadnit testování povolením použití mock (falešných) implementací LLM, které vracejí předdefinované odpovědi bez skutečných volání API.

## 🔑 Klíčové Metody (Koncepční)

Implementace `LLMInterface` by typicky definovala metody jako:

*   **`generate_response(prompt: str, context: Optional[Any] = None)`:** Odešle daný řetězec promptu (potenciálně spolu s dalším strukturovaným kontextem) nakonfigurovanému LLM a vrátí vygenerovanou odpověď modelu jako řetězec nebo strukturovaný objekt.
*   **`get_completion(prompt: str, **kwargs)`:** Běžná alternativní konvence pojmenování, potenciálně přijímající další LLM-specifické parametry (jako `temperature`, `max_tokens`) přes `kwargs`.

Přesná signatura metody závisí na návrhu v `large_language_model.py`. Cílem je poskytnout konzistentní způsob, jak `AIService` může získat textovou analýzu nebo strukturovaný výstup z LLM na základě promptu.

## ⚙️ Implementace

Systém může obsahovat konkrétní implementace jako:

*   `OpenAILLM`: Interaguje s OpenAI API (pomocí knihovny `openai`).
*   `GoogleLLM`: Interaguje s Google Generative AI API (pomocí knihovny `google-generativeai`).
*   `MockLLM`: Simulovaný LLM pro testování, vracející pevné nebo předvídatelné odpovědi.

`OrchestrationDaemon` vybírá a instanciuje příslušnou implementaci na základě konfigurace.

## ⚙️ Konfigurace

Konkrétní implementace vyžadují API klíče a potenciálně další nastavení nakonfigurovaná v souboru `.env`:

*   `OPENAI_API_KEY`
*   `GOOGLE_API_KEY` (V našem `.env` jako `GEMINI_API_KEY`)
*   Potenciálně názvy modelů (např. `OPENAI_MODEL_NAME=gpt-4o`)

## 🔗 Klíčové Interakce

*   **`AIService` 🤖:** Primárně používá toto rozhraní k odesílání promptů sestavených z tržních dat a kontextu paměti a na oplátku přijímá analýzu LLM nebo vygenerované signály.
*   **`config.py` ⚙️:** Čte potřebné API klíče a konfigurace modelů.
*   **Externí Knihovny:** Implementace používají knihovny specifické pro poskytovatele (`openai`, `google-generativeai`).
*   **`logger.py` 📝:** Loguje odeslané prompty a přijaté odpovědi (potenciálně zkrácené pro stručnost/bezpečnost).
