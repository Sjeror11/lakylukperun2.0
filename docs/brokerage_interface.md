# Brokerage Interface

## Overview

The `BrokerageInterface` (`src/interfaces/brokerage.py`) defines the standard contract for interacting with a financial brokerage platform. It abstracts the specific API calls and data formats of a particular broker (like Alpaca, Interactive Brokers, etc.), allowing the `ExecutionService` and potentially other services to perform trading-related actions in a broker-agnostic way.

## Purpose

*   Abstract away the complexities of specific brokerage APIs.
*   Enable switching between different brokers by simply changing the concrete implementation used, without altering the core trading logic.
*   Facilitate testing by allowing mock brokerage implementations.

## Key Methods (Conceptual)

A typical `BrokerageInterface` implementation would define methods for essential brokerage operations. The exact method names and parameters might vary based on the actual `brokerage.py` file, but common functionalities include:

*   **`get_account_info()`:** Retrieves current account details, such as buying power, cash balance, portfolio value, and account status. Returns a `Portfolio` object or similar structure.
*   **`get_market_data(symbols: List[str])`:** Fetches current market data (e.g., latest quotes, bars) for a list of specified trading symbols. Returns a list of `MarketData` objects or a dictionary mapping symbols to data.
*   **`submit_order(order: Order)`:** Places a trade order with the brokerage based on the details provided in an `Order` object. Returns an order confirmation or identifier.
*   **`get_order_status(order_id: str)`:** Checks the status (e.g., pending, filled, cancelled, rejected) of a previously submitted order using its unique identifier. Returns an updated `Order` object or status information.
*   **`cancel_order(order_id: str)`:** Attempts to cancel an open order.
*   **`list_positions()`:** Retrieves a list of currently held positions in the account.
*   **`is_market_open()`:** Checks if the relevant market (e.g., US equities) is currently open for trading.

## Implementations

The `trading_system` might include one or more concrete implementations of this interface, for example:

*   `AlpacaBrokerage`: Interacts with the Alpaca Trade API.
*   `MockBrokerage`: A simulated brokerage used for testing purposes, returning predefined data and simulating order fills without connecting to a live market.

The specific implementation used at runtime is typically determined by configuration settings in `.env` and instantiated by the `OrchestrationDaemon`.

## Configuration

Concrete implementations will require specific API credentials and endpoint URLs, configured in the `.env` file:

*   `APCA_API_KEY_ID`
*   `APCA_API_SECRET_KEY`
*   `APCA_API_BASE_URL` (e.g., paper or live trading endpoint)

## Key Interactions

*   **`ExecutionService`:** Primarily uses this interface to place orders, check statuses, and get portfolio information for risk management and order sizing.
*   **`OrchestrationDaemon`:** May use this interface to fetch initial portfolio status or check market hours.
*   **`Order`, `Portfolio`, `MarketData` Models:** The interface methods often consume or return instances of these data models.
*   **`config.py`:** Reads the necessary API credentials for the chosen implementation.
