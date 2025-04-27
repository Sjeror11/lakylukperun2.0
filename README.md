# ✨ Perun Trading System ✨

Welcome to **Perun**, an automated trading system designed to leverage the power of Large Language Models (LLMs) for market analysis and trade execution. Perun analyzes market data, generates trading signals, manages a portfolio, and interacts with brokerage APIs, all orchestrated within a modular and configurable framework. For a deeper dive into the system's concepts and workflow, see the [🌌 Conceptual Overview](./docs/system_overview.md).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Example Badge -->

---

## 🚀 Features

*   🧠 **LLM-Powered Analysis:** Utilizes LLMs (OpenAI, Gemini) for deep market analysis and signal generation.
*   🔍 **Market Research:** Integrates with Perplexity AI for real-time news and sentiment analysis.
*   🤖 **Automated Trading Cycle:** Full automation from data fetching to order execution and portfolio monitoring.
*   🏦 **Brokerage Integration:** Connects seamlessly with Alpaca for market data, account management, and trading.
*   💾 **Persistent Memory:** Maintains a history of actions, observations, and insights to inform future decisions.
*   📢 **Notification System:** Configurable alerts via Mattermost and Email.
*   ⚙️ **Configuration Driven:** Easily customize system behavior via environment variables.
*   🧱 **Modular Architecture:** Decoupled services for enhanced maintainability, testability, and extensibility.
*   📈 **Optimization Ready:** Includes components for performance analysis and potential parameter tuning.

---

## 🏗️ Architecture Overview

Perun employs a service-oriented architecture, coordinated by a central daemon:

*   **Orchestration Service (`OrchestrationDaemon`):** 🕰️ The main control loop, scheduling tasks based on market hours and system state. [More Details](./docs/orchestration_service.md)
*   **AI Service (`AIServiceProcessor`):** 🤖 Interacts with LLMs (OpenAI/Gemini) and Perplexity to analyze data and generate trading signals. [More Details](./docs/ai_service.md)
*   **Execution Service (`ExecutionManager`):** 💼 Manages all interactions with the brokerage (Alpaca), handling orders and portfolio updates. [More Details](./docs/execution_service.md)
*   **Memory Service (`MemoryStorage`, `MemoryOrganizer`):** 📚 Stores and retrieves system memory (trades, signals, logs, analysis). [More Details](./docs/memory_service.md)
*   **Optimization Service (`OptimizationEngine`, `FrequencyAnalyzer`):** 🛠️ Analyzes performance and suggests parameter adjustments. [More Details](./docs/optimization_service.md)
*   **Interfaces:** 🔌 Abstract layers for external communication:
    *   `BrokerageInterface`: Alpaca interactions. [Details](./docs/brokerage_interface.md)
    *   `LLMInterface`: OpenAI/Gemini interactions. [Details](./docs/llm_interface.md)
    *   `PerplexityInterface`: Perplexity AI interactions. (See `src/interfaces/perplexity.py`)
    *   `NotificationInterface`: Mattermost/Email interactions. [Details](./docs/notification_interface.md)
    *   `WebDataInterface`: (Future) Fetching external web data. [Details](./docs/web_data_interface.md)
*   **Models:** 🧱 Core data structures (`Order`, `Signal`, `Portfolio`, etc.).

[General Interface Concepts](./docs/interfaces.md)

---

## 🛠️ Setup & Configuration

Follow these steps to get Perun up and running:

**1. Clone the Repository:**
```bash
git clone https://github.com/david-strejc/perun.git
cd perun # Note: The repo was created as 'perun', containing the 'trading_system' files directly
```

**2. Create & Activate Virtual Environment:**
```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (Git Bash/WSL)
python3 -m venv .venv
source .venv/Scripts/activate

# Windows (Command Prompt)
python -m venv .venv
.venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**3. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables (`.env`):**

Create a `.env` file in the project root (`perun/`). This file stores your API keys and configuration settings. **Do not commit this file to Git.** Below is a template with detailed instructions on where to find each required value.

```dotenv
#####################################################
# Perun Trading System Environment Configuration    #
# Detailed instructions for obtaining credentials   #
#####################################################

# --- 🏦 Brokerage: Alpaca (Required) ---
# Purpose: Connects to the stock market for data and trading.
# Instructions:
# 1. Sign up/Log in: Go to https://alpaca.markets/ and create an account or log in.
# 2. Paper vs Live: Decide if you want to test with fake money (Paper Trading) or real money (Live Trading). It's HIGHLY recommended to start with Paper Trading.
# 3. Generate Keys:
#    - Navigate to your dashboard (Paper or Live).
#    - Find the API Keys section (often on the right side or under account settings).
#    - Click "Generate New Key" or similar.
#    - IMPORTANT: Copy both the 'API Key ID' and the 'Secret Key' immediately. The Secret Key is only shown once!
# 4. Set URLs:
#    - For Paper Trading: Use https://paper-api.alpaca.markets
#    - For Live Trading: Use https://api.alpaca.markets
ALPACA_API_KEY=YOUR_ALPACA_KEY_ID_HERE
ALPACA_SECRET_KEY=YOUR_ALPACA_SECRET_KEY_HERE
ALPACA_BASE_URL=https://paper-api.alpaca.markets # Start with Paper Trading!

# --- 🧠 LLM & Research APIs (Optional Keys, Required Models) ---
# Purpose: Provide AI capabilities for analysis and research. You only need keys for the services whose models you specify below.

# --- OpenAI ---
# Instructions:
# 1. Sign up/Log in: Go to https://platform.openai.com/
# 2. Navigate: Click on your profile icon/name (top-right).
# 3. API Keys: Select "View API keys" or navigate to the "API Keys" section (might be under "Settings" or "Projects").
# 4. Create Key: Click "Create new secret key". Give it a name (e.g., "Perun Trading Bot").
# 5. Copy Key: Copy the generated key immediately (it won't be shown again) and paste it below.
# 6. Funding: Note that using the OpenAI API requires adding payment information and incurs costs based on usage.
OPENAI_API_KEY=YOUR_OPENAI_KEY_IF_USING_OPENAI_MODELS

# --- Google Gemini ---
# Instructions:
# 1. Go to Google AI Studio: Visit https://aistudio.google.com/app/apikey
# 2. Sign in: Log in with your Google Account.
# 3. Create Key: Click "Create API key". You might need to create a new project first.
# 4. Copy Key: Copy the generated API key and paste it below.
# 5. Usage Limits: Be aware of potential free tier limits and associated costs for higher usage.
GEMINI_API_KEY=YOUR_GOOGLE_KEY_IF_USING_GEMINI_MODELS

# --- Perplexity AI ---
# Instructions:
# 1. Sign up/Log in: Go to https://perplexity.ai/
# 2. Navigate: Click your profile icon (bottom-left), then select "API Keys" (or go to Settings -> API).
# 3. Billing (If Required): You might need to set up billing information first. Follow the on-screen prompts.
# 4. Generate Key: Click "Generate" or "Create New Key".
# 5. Copy Key: Copy the generated API key and paste it below.
# 6. Pricing: Check Perplexity's API pricing details.
PERPLEXITY_API_KEY=YOUR_PERPLEXITY_API_KEY_IF_USING_PERPLEXITY

# --- Model Selection (Required) ---
# Purpose: Tell Perun which specific AI models to use for different tasks.
# Instructions: Choose models compatible with the API keys you provided above.
# Examples: "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "sonar-small-online" (Perplexity)
# Ensure the chosen models are suitable for the task complexity and your budget.
TRADING_ANALYSIS_LLM_MODEL="gpt-4o" # Model for the main trading decisions
MEMORY_ORGANIZATION_LLM_MODEL="gpt-3.5-turbo" # Can often use a cheaper/faster model here
OPTIMIZATION_LLM_MODEL="gpt-4o" # Model used by the optimization service

# --- 📢 Notifications (Optional) ---
# Purpose: Receive alerts about trades, errors, or system status.

# --- Mattermost ---
# Instructions (Requires access to a Mattermost server):
# 1. Enable Bots: A System Admin needs to enable Bot Accounts (System Console -> Integrations -> Bot Accounts).
# 2. Create Bot: As Admin, go to Integrations -> Bot Accounts -> "Add Bot Account".
# 3. Fill Details: Give the bot a username (e.g., "perun_bot"), description.
# 4. Get Token: After creation, copy the generated 'Token' immediately. This is your MATTERMOST_TOKEN.
# 5. Get Server URL: This is the web address of your Mattermost instance (e.g., https://yourcompany.mattermost.com).
# 6. Get Team ID: Navigate to the team you want the bot in. The Team ID is usually part of the URL (e.g., /team/TEAM_ID_HERE/...).
# 7. Get Channel ID: Navigate to the specific channel for notifications. The Channel ID is often in the URL after the team ID (e.g., /channels/CHANNEL_ID_HERE).
MATTERMOST_ENABLED=false # Set to true to enable
MATTERMOST_URL=https://your.mattermost.instance.com
MATTERMOST_TOKEN=YOUR_MATTERMOST_BOT_TOKEN_HERE
MATTERMOST_TEAM_ID=YOUR_MATTERMOST_TEAM_ID_HERE
MATTERMOST_CHANNEL_ID=YOUR_TARGET_CHANNEL_ID_HERE

# --- Email (SMTP) ---
# Instructions: Use the SMTP details from your email provider (e.g., Gmail, Outlook, SendGrid).
# 1. Find SMTP Settings: Search your email provider's help documentation for "SMTP settings".
# 2. Server & Port: Get the SMTP server address (e.g., smtp.gmail.com) and port (e.g., 587 for TLS, 465 for SSL).
# 3. Credentials:
#    - Username: Usually your full email address.
#    - Password: This might be your regular email password OR an "App Password". For Gmail/Google Workspace with 2FA, you MUST generate an App Password (Search "Google App Passwords"). Using an App Password is more secure.
# 4. Admin Email: The email address where notifications should be sent.
EMAIL_ENABLED=false # Set to true to enable
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_email_password_or_app_password
ADMIN_EMAIL=recipient_email@example.com

# --- 📁 File Paths (Required - Relative to project root) ---
# Purpose: Define where Perun stores its data and finds its prompts. Defaults are usually fine.
MEMDIR_PATH=data/memdir
LOG_PATH=data/logs
PROMPTS_PATH=prompts

# --- 📈 Trading Parameters (Required) ---
# Purpose: Define core trading behavior and risk management rules.
DEFAULT_SYMBOLS=AAPL,MSFT,GOOG # Comma-separated list of symbols to trade
MAX_POSITION_SIZE=10000 # Maximum value (USD) per position
MAX_TOTAL_POSITIONS=5 # Maximum number of concurrent open positions
RISK_LIMIT_PERCENT=0.02 # Max risk per trade as % of portfolio equity (e.g., 0.02 = 2%)

# --- 📝 Logging Configuration (Optional - Defaults provided) ---
# Purpose: Control how much detail is logged to the console and files.
LOG_LEVEL_CONSOLE=INFO # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL_FILE=DEBUG
LOG_FILE_NAME=trading_system.log # Log filename within LOG_PATH

# --- 🛠️ Optimization Parameters (Required if OPTIMIZATION_ENABLED=true) ---
# Purpose: Configure the self-optimization features.
OPTIMIZATION_ENABLED=true # Set to false to disable optimization runs
OPTIMIZATION_SCHEDULE=daily # How often to run optimization (e.g., 'daily', 'weekly', or cron: '0 3 * * 0' for 3 AM Sunday)
OPTIMIZATION_PROMPT_THRESHOLD=0.05 # Min performance improvement (e.g., 5%) needed to automatically switch prompts
OPTIMIZATION_MIN_FREQUENCY=60 # Minimum trading frequency (seconds) allowed by optimization
OPTIMIZATION_FREQUENCY_BUFFER_FACTOR=1.5 # Safety buffer multiplier for frequency calculation
OPTIMIZATION_MEMORY_QUERY_DAYS=30 # How many days of history to query for optimization analysis

# --- 💾 Memory Service Configuration (Required) ---
# Purpose: Configure how the system's memory is managed.
MEMDIR_PRUNE_MAX_AGE_DAYS=90 # Delete memory files older than this (0 to disable age pruning)
MEMDIR_PRUNE_MAX_COUNT=100000 # Max memory files to keep (0 to disable count pruning)
MEMDIR_ORGANIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2 # Model for memory tagging/similarity (runs locally)

# --- 🕰️ Orchestration Service (Required) ---
# Purpose: Configure the main control loop timing.
MAIN_LOOP_SLEEP_INTERVAL=1 # Sleep interval (seconds) when idle (e.g., outside market hours)
LIQUIDATE_ON_CLOSE=false # Set to true to liquidate all positions before market close
```

---

## ▶️ Usage

Ensure your virtual environment is active and the `.env` file is configured correctly. Run the main orchestration daemon from the project root (`perun/`):

```bash
python main.py
```

The system will initialize all services and begin its operational cycle. Monitor the console output and log files (`data/logs/trading_system.log`) for status updates and potential issues.

---

## 📁 Project Structure

```
perun/
├── .env                # Environment variables (sensitive, DO NOT COMMIT)
├── .git/               # Git repository data
├── .gitignore          # Files ignored by Git
├── .venv/              # Python virtual environment (ignored)
├── data/               # Data storage (logs, memory - ignored by default)
│   ├── logs/           # Log files (.gitkeep to keep dir)
│   └── memdir/         # Persistent memory storage (.gitkeep to keep dir)
├── docs/               # Detailed documentation for concepts/components
│   ├── ai_service.md
│   ├── brokerage_interface.md
│   ├── execution_service.md
│   ├── interfaces.md
│   ├── llm_interface.md
│   ├── memory_service.md
│   ├── notification_interface.md
│   ├── optimization_service.md
│   ├── orchestration_service.md
│   └── web_data_interface.md
├── prompts/            # LLM prompts
│   ├── evaluation/
│   ├── memory_organization/
│   ├── trading/
│   └── metadata.json
├── scripts/            # Utility scripts
│   └── check_market_hours.py
├── src/                # Source code
│   ├── __init__.py
│   ├── config.py       # Configuration loading
│   ├── interfaces/     # External service interfaces
│   ├── models/         # Data models (Pydantic)
│   ├── services/       # Core logic services
│   └── utils/          # Utility functions (Logging, Exceptions)
├── tests/              # Unit and integration tests
│   ├── __init__.py
│   ├── interfaces/
│   ├── services/
│   └── utils/
├── main.py             # Main application entry point
├── README.md           # This file
├── requirements.txt    # Python dependencies
└── repomix-output.txt  # (Optional) Output from code analysis tools
```

---

## 🧪 Development & Testing

*   Make sure development dependencies are installed (`pip install -r requirements.txt`).
*   Run tests using `pytest` from the project root (`perun/`):
    ```bash
    pytest
    ```
*   Consider using pre-commit hooks for code formatting and linting.

---

## 🤝 Contributing

Contributions are welcome! Please follow standard fork-and-pull-request workflows. Ensure tests pass and code adheres to project standards. (Further details can be added).

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (assuming MIT, add a LICENSE file if needed).
