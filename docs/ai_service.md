# AI Service

## Overview

The AI Service, primarily implemented in the `AIProcessor` class (`src/services/ai_service/processor.py`), is the core component responsible for leveraging Large Language Models (LLMs) to analyze market conditions and generate trading signals. It acts as a bridge between the raw market data/context and actionable trading decisions.

## Responsibilities

*   **LLM Interaction:** Manages communication with the configured LLM via the `LLMInterface`. This includes formatting prompts, sending requests, and parsing responses.
*   **Contextual Analysis:** Takes input data provided by the `OrchestrationDaemon`, which typically includes:
    *   Current market data (`MarketData` objects) for relevant symbols.
    *   Recent portfolio status (`Portfolio` object).
    *   Relevant historical context retrieved from the `MemoryService` (e.g., recent trades, past market observations, previous LLM insights).
    *   Potentially external data like news headlines (if `WebDataInterface` is implemented and used).
*   **Prompt Engineering:** Constructs effective prompts for the LLM based on the available context and the specific goal (e.g., "Analyze the sentiment for AAPL based on recent news and price action", "Generate a buy/sell/hold signal for MSFT"). Prompts are likely stored and managed in the `prompts/` directory.
*   **Signal Generation:** Interprets the LLM's response to identify potential trading opportunities. It translates the LLM's analysis (which might be textual) into structured `Signal` objects (e.g., BUY AAPL at market, SELL MSFT with limit price X).
*   **Risk Assessment (Potential):** May incorporate basic risk parameters (like `TRADE_RISK_PER_TRADE` from config) when formulating signals, although final risk management might reside in the `ExecutionService`.
*   **Error Handling:** Manages potential errors during LLM interaction (e.g., API errors, timeouts, malformed responses).

## Workflow

1.  **Receive Request:** The `OrchestrationDaemon` calls a method on the `AIProcessor` (e.g., `process_data_and_generate_signals`), providing the necessary market data and context.
2.  **Prepare Context:** The `AIProcessor` organizes the received data and retrieves relevant prompts.
3.  **Construct Prompt:** Builds the final prompt string(s) to be sent to the LLM.
4.  **Call LLM:** Uses the `LLMInterface` to send the prompt(s) to the configured LLM API (e.g., OpenAI, Google Gemini).
5.  **Receive & Parse Response:** Gets the response from the LLM. Parses the response to extract meaningful information and potential trading instructions.
6.  **Generate Signals:** Translates the parsed information into one or more `Signal` objects, including symbol, action (buy/sell), quantity/risk, order type, etc.
7.  **Return Signals:** Returns the list of generated `Signal` objects to the `OrchestrationDaemon`.

## Configuration

The AI Service's behavior depends on:

*   **LLM API Keys:** (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, etc.) defined in `.env`.
*   **Selected LLM:** The specific implementation of `LLMInterface` chosen (e.g., `OpenAILLM`, `GoogleLLM`).
*   **Prompts:** The content and structure of files within the `prompts/` directory.
*   **Trading Symbols:** (`TRADING_SYMBOLS`) to focus the analysis.

## Key Interactions

*   **`OrchestrationDaemon`:** Receives data from and returns signals to the daemon.
*   **`LLMInterface`:** Uses this interface to communicate with the actual LLM API.
*   **`MemoryService`:** May query the memory service (directly or indirectly via the daemon) for historical context.
*   **`Signal` Model:** Creates instances of the `Signal` data model.
*   **`MarketData`, `Portfolio` Models:** Consumes these data models as input.
*   **`config.py`:** Reads LLM API keys and potentially other related configurations.
*   **`logger.py`:** Logs activities, prompts, and responses.
