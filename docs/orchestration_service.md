# Orchestration Service

## Overview

The Orchestration Service, implemented primarily within the `OrchestrationDaemon` class (`src/services/orchestration_service/daemon.py`), acts as the central nervous system of the Perun Trading System. It is responsible for coordinating the actions of all other services, managing the main application lifecycle, and ensuring tasks are executed in the correct sequence and at the appropriate times.

## Responsibilities

*   **Initialization:** Instantiates and initializes all other core services (AI, Execution, Memory, Optimization, Notification, Brokerage, LLM interfaces) upon startup.
*   **Main Loop:** Runs the primary control loop of the application. This loop typically involves periodic checks and execution of the trading cycle.
*   **Scheduling:** Determines when to perform key actions, such as fetching market data, running the AI analysis, checking for trading signals, and executing orders. This often involves:
    *   Checking if the market is open (using utilities like `scripts/check_market_hours.py` or brokerage API data).
    *   Adhering to the configured `TRADING_FREQUENCY_MINUTES`.
*   **Coordination:** Passes data between services. For example, it takes market data, provides it to the AI Service, receives signals back, and passes those signals to the Execution Service.
*   **State Management:** Tracks the overall state of the system (e.g., running, shutting down).
*   **Error Handling:** Implements top-level error handling and attempts graceful shutdowns or notifications in case of critical failures within services.
*   **Signal Handling:** Listens for system signals (like `SIGINT` from Ctrl+C) to initiate a graceful shutdown process, ensuring pending operations are completed or cancelled safely.

## Workflow

A typical cycle managed by the Orchestration Daemon might look like this:

1.  **Wait/Schedule:** The daemon waits until the next scheduled trading cycle based on `TRADING_FREQUENCY_MINUTES`.
2.  **Market Check:** Verify if the relevant market is open. If not, wait for the next cycle.
3.  **Data Fetching:** Trigger the `BrokerageInterface` to fetch current market data (prices, volume) and portfolio status (cash, positions).
4.  **Memory Retrieval:** Query the `MemoryService` for relevant recent context (past trades, recent market observations, previous LLM insights).
5.  **AI Processing:** Pass the fetched market data and memory context to the `AIService`. The AI Service interacts with the LLM to analyze the information and generate potential trading signals (`Signal` objects).
6.  **Signal Evaluation:** Receive signals from the `AIService`. Potentially apply basic filtering or validation.
7.  **Execution:** If valid buy/sell signals are generated, pass them to the `ExecutionService` to place orders via the `BrokerageInterface`.
8.  **Memory Update:** Store the events of the cycle (data fetched, signals generated, orders placed, errors encountered) in the `MemoryService`.
9.  **Notification:** Send status updates or alerts via the `NotificationInterface` if configured.
10. **Optimization Check (Optional):** Periodically trigger the `OptimizationService` to analyze performance and potentially suggest or apply parameter adjustments.
11. **Loop:** Repeat the cycle.

## Configuration

The behavior of the Orchestration Service is influenced by environment variables defined in `.env`, such as:

*   `TRADING_FREQUENCY_MINUTES`: Controls how often the main trading cycle runs.
*   `MARKET_OPEN_CHECK_ENABLED`: Toggles the check for market hours.
*   `TRADING_SYMBOLS`: Determines which assets the system focuses on.

## Key Interactions

*   **`main.py`:** Instantiates and starts the `OrchestrationDaemon`.
*   **All other Services:** The daemon holds references to and calls methods on the AI, Execution, Memory, and Optimization services.
*   **Interfaces:** Uses the Brokerage, LLM, and Notification interfaces (often indirectly via the services).
*   **`config.py`:** Reads configuration settings.
*   **`logger.py`:** Uses the central logger for recording events.
