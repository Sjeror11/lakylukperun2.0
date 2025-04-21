# Large Language Model (LLM) Interface

## Overview

The `LLMInterface` (`src/interfaces/large_language_model.py`) defines the standard contract for interacting with different Large Language Models (LLMs), such as those provided by OpenAI (GPT series) or Google (Gemini series). It abstracts the specific API endpoints, authentication methods, and request/response formats of various LLM providers.

## Purpose

*   Abstract away the details of specific LLM APIs (e.g., OpenAI API vs. Google Generative AI API).
*   Allow the `AIService` to use different LLMs without changing its core logic for prompt construction or response interpretation.
*   Enable easy switching between LLM providers based on cost, performance, or features by changing the configuration.
*   Facilitate testing by allowing the use of mock LLM implementations that return predefined responses without making actual API calls.

## Key Methods (Conceptual)

An `LLMInterface` implementation would typically define methods like:

*   **`generate_response(prompt: str, context: Optional[Any] = None)`:** Sends a given prompt string (potentially along with additional structured context) to the configured LLM and returns the model's generated response as a string or a structured object.
*   **`get_completion(prompt: str, **kwargs)`:** A common alternative naming convention, potentially accepting additional LLM-specific parameters (like `temperature`, `max_tokens`) via `kwargs`.

The exact method signature depends on the design in `large_language_model.py`. The goal is to provide a consistent way for the `AIService` to get textual analysis or structured output from an LLM based on a prompt.

## Implementations

The system might include concrete implementations such as:

*   `OpenAILLM`: Interacts with the OpenAI API (using the `openai` library).
*   `GoogleLLM`: Interacts with the Google Generative AI API (using the `google-generativeai` library).
*   `MockLLM`: A simulated LLM for testing, returning fixed or predictable responses.

The `OrchestrationDaemon` selects and instantiates the appropriate implementation based on configuration.

## Configuration

Concrete implementations require API keys and potentially other settings configured in the `.env` file:

*   `OPENAI_API_KEY`
*   `GOOGLE_API_KEY`
*   Potentially model names (e.g., `OPENAI_MODEL_NAME=gpt-4o`)

## Key Interactions

*   **`AIService`:** Primarily uses this interface to send prompts constructed from market data and memory context, and receives the LLM's analysis or generated signals in return.
*   **`config.py`:** Reads the necessary API keys and model configurations.
*   **External Libraries:** Implementations use provider-specific libraries (`openai`, `google-generativeai`).
*   **`logger.py`:** Logs prompts sent and responses received (potentially truncated for brevity/security).
