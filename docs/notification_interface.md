# Notification Interface

## Overview

The `NotificationInterface` (`src/interfaces/notification.py`) defines a standard contract for sending messages, alerts, or status updates from the trading system to external channels. It abstracts the specific APIs or protocols used by different notification platforms (like Mattermost, Slack, email, SMS, etc.).

## Purpose

*   Abstract away the details of specific notification service APIs (e.g., Mattermost webhooks vs. email SMTP).
*   Allow the system (primarily the `OrchestrationDaemon` or other services) to send notifications without needing to know the specifics of the chosen channel.
*   Enable easy configuration of different notification methods or adding new ones by creating new implementations.
*   Facilitate testing by allowing mock notification implementations that simply log messages or store them for verification instead of sending them externally.

## Key Methods (Conceptual)

A `NotificationInterface` typically defines a primary method for sending messages:

*   **`send_notification(message: str, subject: Optional[str] = None, **kwargs)`:** Sends the provided `message` string to the configured notification channel. It might accept an optional `subject` (useful for emails) and potentially other channel-specific parameters via `kwargs`.

## Implementations

The system might include concrete implementations such as:

*   `MattermostNotifier`: Sends messages to a specified Mattermost channel using the `mattermostdriver` library.
*   `EmailNotifier`: Sends messages via email using SMTP.
*   `ConsoleNotifier`: Simply prints messages to the console (useful for debugging or simple setups).
*   `MockNotifier`: A simulated notifier for testing that records messages sent to it.

The `OrchestrationDaemon` selects and instantiates the appropriate implementation based on configuration.

## Configuration

Concrete implementations require specific configuration details in the `.env` file:

*   **Mattermost:** `MATTERMOST_URL`, `MATTERMOST_TOKEN`, `MATTERMOST_CHANNEL_ID`
*   **Email:** SMTP server details, sender/recipient addresses, credentials.

## Key Interactions

*   **`OrchestrationDaemon`:** Most likely service to use this interface for sending startup/shutdown messages, critical errors, or periodic status updates.
*   **Other Services (Potentially):** Services like `ExecutionService` or `OptimizationService` might use it to report significant events (e.g., large trade execution, optimization recommendations).
*   **`config.py`:** Reads the necessary credentials and endpoint details for the chosen notification implementation.
*   **External Libraries:** Implementations use provider-specific libraries (`mattermostdriver`, `smtplib`).
*   **`logger.py`:** May log attempts to send notifications and their success/failure.
