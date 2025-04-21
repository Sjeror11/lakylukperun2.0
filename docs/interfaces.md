# Interfaces

## Overview

Interfaces in the Perun Trading System (`src/interfaces/`) define standardized contracts for interacting with external services or components whose specific implementations might vary. They act as abstraction layers, decoupling the core application logic from the concrete details of external systems like brokerages, Large Language Models (LLMs), or notification platforms.

## Purpose

*   **Decoupling:** Allows the core services (`AIService`, `ExecutionService`, etc.) to work with different external systems without changing their internal logic. For example, the `ExecutionService` interacts with the `BrokerageInterface`, not directly with the Alpaca API or another specific brokerage's API.
*   **Flexibility & Extensibility:** Makes it easier to swap out implementations or add support for new external services. To support a new brokerage, one would only need to create a new class implementing the `BrokerageInterface`.
*   **Testability:** Enables easier testing by allowing the use of mock implementations (stubs or fakes) of these interfaces during unit or integration testing. This avoids reliance on live external APIs during tests.

## Key Interfaces

The system defines several key interfaces:

*   **`BrokerageInterface`:** Defines methods for interacting with a trading brokerage (e.g., fetching market data, getting account info, submitting orders, checking order status).
*   **`LLMInterface`:** Defines methods for interacting with a Large Language Model (e.g., sending prompts, receiving completions/responses).
*   **`NotificationInterface`:** Defines methods for sending notifications or alerts (e.g., sending a message to Mattermost, email, SMS).
*   **`WebDataInterface` (Implied/Potential):** Could define methods for fetching external data like news articles or economic indicators from web sources.

Each interface typically specifies method signatures (function names, arguments, return types) that concrete implementations must adhere to. The actual implementations (e.g., `AlpacaBrokerage`, `OpenAILLM`, `MattermostNotifier`) would reside within the `interfaces` directory or subdirectories and would contain the specific logic and API calls for that particular service. The `OrchestrationDaemon` usually selects and instantiates the concrete implementations based on configuration settings during startup.
