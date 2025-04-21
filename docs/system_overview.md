# 🌌 Perun Trading System: Conceptual Overview

Welcome to the conceptual overview of the Perun Trading System! This document aims to explain the *why* and *how* behind Perun in a way that's accessible, even if you're new to automated trading, programming, or AI.

---

## 🎯 What is Perun's Goal?

At its heart, Perun is an **experimental automated trading assistant**. Its primary goal is to:

1.  **Analyze Financial Markets:** 📈 Continuously monitor market data (like stock prices).
2.  **Generate Trading Ideas:** 💡 Use Artificial Intelligence (specifically Large Language Models - LLMs) combined with market research (like Perplexity AI) to form opinions or "signals" about whether to buy or sell specific assets (like stocks).
3.  **Execute Trades:** 🤖 Automatically place buy or sell orders with a connected brokerage (like Alpaca) based on the generated signals.
4.  **Manage Risk:** 🛡️ Operate within predefined risk limits to protect capital.
5.  **Learn & Adapt:** 🧠 Use a memory system to record its actions and outcomes, and potentially use this information to optimize its strategies over time.

Think of Perun not as a guaranteed money-making machine, but as a framework for exploring how modern AI can be applied to the complex challenge of financial market trading.

---

## 🤔 How Does Perun Decide What to Trade? (The Trading Logic)

Perun doesn't rely on traditional, fixed trading rules (like "buy when moving average X crosses moving average Y"). Instead, it uses a more dynamic, AI-driven approach:

**The Core Cycle:**

```ascii
+-------------------+      +---------------------+      +--------------------+      +----------------------+      +---------------------+
| 1. Gather Data    | ---> | 2. AI Analysis      | ---> | 3. Generate Signal | ---> | 4. Risk Assessment   | ---> | 5. Execute Order    |
| (Market Prices,   |      | (LLM + Perplexity)  |      | (Buy/Sell/Hold?)   |      | (Position Size, etc.)|      | (Via Brokerage API) |
| Portfolio Status) |      |                     |      |                    |      |                      |      |                     |
+-------------------+      +---------------------+      +--------------------+      +----------------------+      +---------------------+
        ^                                                                                                                  |
        |-----------------------------------< Loop >-----------------------------------------------------------------------+
```

1.  **Gather Data 📊:** The system fetches the latest market prices for the stocks it's configured to watch (e.g., AAPL, MSFT). It also checks the current status of its own trading account (cash balance, existing positions) via the **Brokerage Interface** (Alpaca).
2.  **AI Analysis 🧠:** This is where the magic happens!
    *   **Market Research (Optional):** It might first ask **Perplexity AI** for recent news or sentiment about the target stocks (`"What's the latest news on MSFT?"`).
    *   **LLM Prompting:** All the gathered data (market prices, portfolio status, recent history from memory, Perplexity insights) is formatted into a detailed text prompt. This prompt is sent to a powerful **Large Language Model (LLM)** like OpenAI's GPT-4 or Google's Gemini via the **LLM Interface**. The prompt essentially asks the LLM: *"Given all this information, what trading action (if any) do you recommend for which stock, and why?"*
3.  **Generate Signal 💡:** The LLM processes the prompt and (hopefully) returns a structured response, typically in JSON format, indicating:
    *   `action`: BUY, SELL, or HOLD.
    *   `symbol`: The stock ticker (e.g., AAPL).
    *   `confidence`: How sure the LLM is (e.g., 0.8 for 80% confidence).
    *   `rationale`: The LLM's reasoning.
    The **AI Service** parses this response. If it's a valid BUY or SELL signal with sufficient confidence, it becomes a formal `TradingSignal`.
4.  **Risk Assessment 🛡️:** Before acting on a signal, the **Execution Service** checks against pre-set rules defined in the configuration (`.env` file):
    *   *Is there enough buying power?*
    *   *Does this trade exceed the maximum allowed size for one position?*
    *   *Do we already have the maximum number of open positions?*
    *   *Does the potential loss fit within the risk limit per trade?*
    If the trade is too risky according to the rules, it's rejected.
5.  **Execute Order 🤖:** If the signal is valid and passes the risk assessment, the **Execution Service** sends the order (e.g., "Buy 10 shares of AAPL") to the **Brokerage Interface** (Alpaca) to be placed on the real market.

This entire cycle repeats at a configured interval (e.g., every few minutes or hours) during market open hours.

---

## 💾 How Does Perun Remember? (Memory Management)

Trading decisions are often better when informed by past events. Perun has a **Memory Service** designed to store and retrieve important information:

**What's Stored?**

*   **Trades:** Records of every buy and sell order placed.
*   **Signals:** The trading signals generated by the AI Service.
*   **Analysis:** The prompts sent to the LLM and the raw responses received.
*   **Market Snapshots:** Periodic snapshots of market data.
*   **Portfolio Snapshots:** Periodic snapshots of the account status.
*   **Errors:** Any errors encountered by the system.
*   **Log Messages:** Important events logged by different services.

**How is it Stored?**

*   Each piece of information is saved as a `MemoryEntry` object.
*   These entries are typically stored as individual files (e.g., JSON files) in a dedicated directory (`data/memdir/`). This is a simple but effective approach for this system.

**How is it Used?**

*   **Context for AI:** When the **AI Service** prepares its prompt for the LLM, it can query the **Memory Service** for recent relevant history (e.g., "Show me the last 5 trades and signals for AAPL"). This gives the LLM context beyond the immediate market snapshot.
*   **Optimization:** The **Optimization Service** can analyze long-term memory (e.g., weeks or months of trades and signals) to evaluate strategy performance.
*   **Debugging:** Developers can examine the memory files to understand why the system made certain decisions or encountered errors.

**Organization:**

*   The `MemoryOrganizer` component (potentially using simpler models like `sentence-transformers`) can help tag or categorize memory entries, making it easier to find relevant information later.

```ascii
+---------------------+      +-------------------------+      +---------------------+
|    Other Services   | ---> |   Memory Service        | <--- |    Other Services   |
| (AI, Execution etc.)|      |   (Storage/Organizer)   |      | (AI, Optimization)  |
|   [Save Memory]     |      +-------------------------+      |   [Query Memory]    |
+---------------------+      | - Stores Trades         |      +---------------------+
                           | - Stores Signals        |
                           | - Stores Analysis       |
                           | - Stores Errors         |
                           | - Organizes/Tags Data |
                           +-------------------------+
```

---

## 🚀 How Does Perun Try to Improve? (Self-Optimization)

Perun includes an **Optimization Service** designed to periodically review its own performance and potentially adjust its strategy. This is an advanced feature and might involve:

1.  **Performance Review:** 📊 Regularly (e.g., daily or weekly, based on `OPTIMIZATION_SCHEDULE`), the service analyzes historical data from the **Memory Service**. It looks at the profitability of past trades generated by specific prompts or configurations.
2.  **Strategy Evaluation:** 🤔 It might compare the performance of the current trading prompt against alternative prompts (potentially generated by another LLM or predefined by the user).
3.  **Parameter Tuning:** ⚙️ It could analyze if changing parameters like the `RISK_LIMIT_PERCENT` or the list of `DEFAULT_SYMBOLS` might have led to better results historically. It might also analyze the ideal frequency of trading using the `FrequencyAnalyzer`.
4.  **Making Adjustments:** ✨ If the analysis suggests a clear improvement (e.g., a new prompt consistently outperforms the old one by more than the `OPTIMIZATION_PROMPT_THRESHOLD`), the service might automatically:
    *   Update the system to use the better-performing prompt.
    *   Suggest changes to configuration parameters (though automatic changes to `.env` are complex and might require manual intervention).

**Important Note:** True self-optimization is very complex. Perun's optimization capabilities are likely focused on specific areas like prompt performance or trading frequency analysis rather than a complete overhaul of its core logic.

```ascii
+---------------------+      +---------------------+      +---------------------+
|   Memory Service    | ---> | Optimization Service| ---> | Configuration/State |
| (Historical Data)   |      | (Analyze Performance|      | (Update Prompts,    |
+---------------------+      |  Evaluate Strategy) |      |  Suggest Params)    |
                           +---------------------+      +---------------------+
```

---

## 🏁 Conclusion

Perun is a sophisticated system integrating market data, brokerage interactions, multiple AI tools (LLMs, Perplexity), memory, and optimization concepts. Its modular design allows for experimentation and extension. By understanding these core concepts – the AI-driven trading cycle, the importance of memory, and the potential for optimization – you can better grasp how Perun operates and how you might configure, run, or even contribute to its development. Remember to start with paper trading and understand the risks involved!
