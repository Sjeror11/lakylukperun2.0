# Optimization Service

## Overview

The Optimization Service, potentially implemented across classes like `OptimizationEngine` (`src/services/optimization_service/engine.py`) and `FrequencyAnalyzer` (`src/services/optimization_service/frequency_analyzer.py`), is designed to analyze the performance of the trading system and suggest or automatically apply adjustments to its parameters to improve results. This is an advanced feature that aims to make the system adaptive.

## Responsibilities

*   **Performance Analysis:** Analyzes historical trading performance data stored in the `MemoryService`. This could involve calculating metrics like:
    *   Win/loss ratio
    *   Profit factor
    *   Sharpe ratio
    *   Maximum drawdown
    *   Trade frequency vs. profitability
*   **Parameter Tuning:** Based on the performance analysis, identifies parameters that could be adjusted for potential improvement. Examples include:
    *   `TRADING_FREQUENCY_MINUTES`: Finding the optimal frequency for analysis and trading.
    *   `TRADE_RISK_PER_TRADE`: Adjusting risk levels based on market volatility or performance.
    *   Parameters within the AI Service's prompts or logic.
    *   Specific thresholds used in signal generation or execution.
*   **Suggestion/Application:** Either suggests parameter changes to the user (via notifications) or, if configured, automatically updates the system's configuration or internal state with new parameter values.
*   **Frequency Analysis (`FrequencyAnalyzer`):** A specific component likely focused on determining the most effective `TRADING_FREQUENCY_MINUTES` by analyzing how profitability correlates with how often the system trades.

## Workflow

1.  **Trigger:** The `OrchestrationDaemon` periodically triggers the `OptimizationEngine` (e.g., daily, weekly).
2.  **Data Retrieval:** The `OptimizationEngine` queries the `MemoryService` to retrieve historical trade data, market conditions, and potentially system parameter values used during those trades.
3.  **Analysis:** Performs calculations and analysis on the historical data. This might involve specific components like the `FrequencyAnalyzer`.
4.  **Identify Improvements:** Determines if changing certain parameters (like trading frequency) could lead to better performance based on the analysis.
5.  **Generate Recommendations:** Formulates recommendations for new parameter values.
6.  **Report/Apply:**
    *   Sends recommendations via the `NotificationInterface`.
    *   OR, if auto-tuning is enabled, updates the system's configuration or runtime state (this requires careful implementation to avoid instability).

## Configuration

*   **Optimization Schedule:** How often the optimization analysis runs (likely managed within the `OrchestrationDaemon`).
*   **Analysis Parameters:** Specific metrics or thresholds used by the optimization logic.
*   **Auto-Tuning Flag:** A boolean configuration (`OPTIMIZATION_AUTO_APPLY`?) to enable/disable automatic parameter updates.

## Key Interactions

*   **`OrchestrationDaemon`:** Triggers the optimization process. May receive updated parameters if auto-tuning is enabled.
*   **`MemoryService`:** Retrieves historical performance data.
*   **`NotificationInterface`:** Sends reports or recommendations.
*   **`config.py`:** May read optimization-specific settings or potentially update configuration if auto-tuning modifies `.env` or runtime variables.
*   **`logger.py`:** Logs analysis results and parameter changes.
*   **Potentially other Services:** If tuning parameters specific to AI or Execution, it might interact with or influence those services indirectly.
