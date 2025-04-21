# Memory Service

## Overview

The Memory Service is responsible for persistently storing and retrieving information relevant to the trading system's operation and decision-making process. It acts as the system's long-term memory, allowing it to learn from past events and maintain context over time. This service is typically composed of two main parts: storage and organization, implemented in `MemoryStorage` (`src/services/memory_service/storage.py`) and `MemoryOrganizer` (`src/services/memory_service/organizer.py`).

## Responsibilities

*   **Data Persistence (`MemoryStorage`):**
    *   Handles the low-level reading and writing of data to a persistent storage medium (e.g., files on disk in the `data/memdir/` directory, a database).
    *   Stores various types of information as `MemoryEntry` objects or similar structures, including:
        *   Market data snapshots.
        *   Generated signals.
        *   Placed and executed orders.
        *   LLM prompts and responses.
        *   System events and errors.
        *   Portfolio snapshots.
    *   Ensures data is saved reliably.
*   **Data Organization & Retrieval (`MemoryOrganizer`):**
    *   Provides higher-level functions for querying and structuring the stored memory.
    *   May use techniques like semantic search (e.g., using sentence transformers as indicated in `requirements.txt`) to find relevant past entries based on current context.
    *   Organizes memories, potentially summarizing or categorizing them.
    *   Provides relevant context to the `OrchestrationDaemon` or `AIService` when requested (e.g., "retrieve the last 5 trades for AAPL", "find recent market commentary related to GOOG").
*   **Context Provision:** Supplies historical data and context to other services, particularly the `AIService`, to inform its analysis and signal generation.

## Workflow

**Storage:**

1.  **Receive Data:** Another service (e.g., Orchestration, AI, Execution) generates data to be stored (e.g., a new order, an LLM response).
2.  **Format Data:** The data is formatted into a `MemoryEntry` or appropriate structure.
3.  **Store Data:** The `MemoryStorage` component writes the formatted data to the persistent store (e.g., appends to a log file, saves a new file, inserts into a database table).

**Retrieval:**

1.  **Receive Query:** The `OrchestrationDaemon` or `AIService` requests specific historical information or context from the `MemoryOrganizer`. The query might be time-based, event-based, or semantic.
2.  **Query Storage:** The `MemoryOrganizer` interacts with `MemoryStorage` to fetch potentially relevant raw data.
3.  **Process & Filter:** The `MemoryOrganizer` processes the raw data, potentially using embedding models or other logic to filter, rank, or summarize the information based on the query.
4.  **Return Context:** The organized and relevant context is returned to the requesting service.

## Configuration

*   **Storage Path:** The location for persistent storage (e.g., `data/memdir/`) might be configurable.
*   **Organizer Model (if applicable):** If using embedding models like sentence-transformers, the specific model used might be configurable.

## Key Interactions

*   **`OrchestrationDaemon`:** Triggers storage of cycle events and requests context for the `AIService`.
*   **`AIService`:** Receives context from the Memory Service to inform its prompts and analysis. May also trigger storage of its own interactions (prompts/responses).
*   **`ExecutionService`:** Triggers storage of order placements and executions.
*   **`MemoryEntry` Model:** Uses this data model (or similar) to structure stored information.
*   **`config.py`:** May read configuration related to storage paths or organizer models.
*   **`logger.py`:** Logs storage and retrieval operations.
*   **External Libraries:** May use libraries like `sentence-transformers`, `torch`, `transformers` for the `MemoryOrganizer` component.
