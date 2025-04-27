import os
from dotenv import load_dotenv
from typing import List, Optional
import logging

# Determine the project root directory (assuming config.py is in src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Construct the path to the .env file within the trading_system directory
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# Load the .env file from the trading_system directory
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    # print(f"Loaded environment variables from: {ENV_PATH}") # Debug print
else:
    # Fallback to loading from the current working directory or system environment
    # This might be useful in some deployment scenarios but less ideal for development
    load_dotenv(override=True)
    # print(f"Warning: {ENV_PATH} not found. Loading from default locations.") # Debug print
    if not os.getenv("ALPACA_API_KEY"): # Check if essential keys are loaded
         print(f"CRITICAL WARNING: Could not find .env file at {ENV_PATH} and essential environment variables (e.g., ALPACA_API_KEY) are not set.")
         # Consider raising an exception here if the .env file is strictly required
         # raise FileNotFoundError(f"Required .env file not found at {ENV_PATH}")


def get_string(var_name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Retrieves a string environment variable."""
    value = os.getenv(var_name)
    if value is None:
        if required:
            raise ValueError(f"Missing required environment variable: {var_name}")
        # print(f"get_string('{var_name}'): Not found, returning default '{default}'") # Debug print
        return default
    # print(f"get_string('{var_name}'): Found value '{value}'") # Debug print
    return value

def get_required_string(var_name: str) -> str:
    """Retrieves a required string environment variable, raising an error if missing."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {var_name}")
    # print(f"get_required_string('{var_name}'): Found value '{value}'") # Debug print
    return value

def get_int(var_name: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
    """Retrieves an integer environment variable."""
    value_str = os.getenv(var_name)
    if value_str is None:
        if required:
            raise ValueError(f"Missing required environment variable: {var_name}")
        # print(f"get_int('{var_name}'): Not found, returning default '{default}'") # Debug print
        return default
    try:
        value = int(value_str)
        # print(f"get_int('{var_name}'): Found value '{value}'") # Debug print
        return value
    except ValueError:
        logging.warning(f"Invalid integer format for {var_name}: '{value_str}'. Using default: {default}")
        return default

def get_float(var_name: str, default: Optional[float] = None, required: bool = False) -> Optional[float]:
    """Retrieves a float environment variable."""
    value_str = os.getenv(var_name)
    if value_str is None:
        if required:
            raise ValueError(f"Missing required environment variable: {var_name}")
        # print(f"get_float('{var_name}'): Not found, returning default '{default}'") # Debug print
        return default
    try:
        value = float(value_str)
        # print(f"get_float('{var_name}'): Found value '{value}'") # Debug print
        return value
    except ValueError:
        logging.warning(f"Invalid float format for {var_name}: '{value_str}'. Using default: {default}")
        return default

def get_bool(var_name: str, default: bool = False) -> bool:
    """Retrieves a boolean environment variable.
       Considers 'true', '1', 'yes', 'y' (case-insensitive) as True.
    """
    value_str = os.getenv(var_name)
    if value_str is None:
        # print(f"get_bool('{var_name}'): Not found, returning default '{default}'") # Debug print
        return default
    value = value_str.lower() in ('true', '1', 'yes', 'y')
    # print(f"get_bool('{var_name}'): Found value '{value}' (from '{value_str}')") # Debug print
    return value

def get_list(var_name: str, default: Optional[List[str]] = None, delimiter: str = ',', required: bool = False) -> List[str]:
    """Retrieves a list environment variable, split by a delimiter."""
    value_str = os.getenv(var_name)
    if value_str is None:
        if required:
            raise ValueError(f"Missing required environment variable: {var_name}")
        # print(f"get_list('{var_name}'): Not found, returning default '{default}'") # Debug print
        return default if default is not None else []
    value = [item.strip() for item in value_str.split(delimiter) if item.strip()]
    # print(f"get_list('{var_name}'): Found value '{value}' (from '{value_str}')") # Debug print
    return value

# --- Specific Configuration Accessors ---

# Brokerage
ALPACA_API_KEY = get_required_string("ALPACA_API_KEY")
ALPACA_SECRET_KEY = get_required_string("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = get_required_string("ALPACA_BASE_URL")
IS_PAPER_TRADING = "paper-api" in ALPACA_BASE_URL

# LLM & Research APIs
OPENAI_API_KEY = get_string("OPENAI_API_KEY") # Optional: User might only use one LLM provider
GEMINI_API_KEY = get_string("GEMINI_API_KEY")   # Optional: User might only use one LLM provider
PERPLEXITY_API_KEY = get_string("PERPLEXITY_API_KEY") # Optional: For market research via Perplexity
# Define specific models for different tasks - All required
TRADING_ANALYSIS_LLM_MODEL = get_string("TRADING_ANALYSIS_LLM_MODEL", required=True)
MEMORY_ORGANIZATION_LLM_MODEL = get_string("MEMORY_ORGANIZATION_LLM_MODEL", required=True) # If MemoryOrganizer uses LLM
OPTIMIZATION_LLM_MODEL = get_string("OPTIMIZATION_LLM_MODEL", required=True) # If Optimization uses LLM

# Notifications
MATTERMOST_ENABLED = get_bool("MATTERMOST_ENABLED", default=False) # Keep default for bool flags
# Mattermost vars are checked below if MATTERMOST_ENABLED is True
MATTERMOST_URL = get_string("MATTERMOST_URL")
MATTERMOST_TOKEN = get_string("MATTERMOST_TOKEN")
MATTERMOST_TEAM_ID = get_string("MATTERMOST_TEAM_ID")
MATTERMOST_CHANNEL_ID = get_string("MATTERMOST_CHANNEL_ID")

EMAIL_ENABLED = get_bool("EMAIL_ENABLED", default=False) # Keep default for bool flags
# Email vars are checked below if EMAIL_ENABLED is True
SMTP_SERVER = get_string("SMTP_SERVER")
SMTP_PORT = get_int("SMTP_PORT", default=587) # Keep default for standard port
SMTP_USERNAME = get_string("SMTP_USERNAME")
SMTP_PASSWORD = get_string("SMTP_PASSWORD")
ADMIN_EMAIL = get_string("ADMIN_EMAIL")

# File Paths - Resolve relative to project root - Make these required
MEMDIR_PATH = os.path.join(PROJECT_ROOT, get_string("MEMDIR_PATH", required=True))
LOG_PATH = os.path.join(PROJECT_ROOT, get_string("LOG_PATH", required=True))
PROMPTS_PATH = os.path.join(PROJECT_ROOT, get_string("PROMPTS_PATH", required=True))

# Trading Parameters - Make these required
DEFAULT_SYMBOLS = get_list("DEFAULT_SYMBOLS", required=True)
MAX_POSITION_SIZE = get_float("MAX_POSITION_SIZE", required=True)
MAX_TOTAL_POSITIONS = get_int("MAX_TOTAL_POSITIONS", required=True)
RISK_LIMIT_PERCENT = get_float("RISK_LIMIT_PERCENT", required=True)

# Logging - Keep defaults for basic operation
LOG_LEVEL_CONSOLE = get_string("LOG_LEVEL_CONSOLE", default="INFO").upper()
LOG_LEVEL_FILE = get_string("LOG_LEVEL_FILE", default="DEBUG").upper()
LOG_FILE_NAME = get_string("LOG_FILE_NAME", default="trading_system.log")
LOG_FILE_PATH = os.path.join(LOG_PATH, LOG_FILE_NAME) # Construct full log file path

# Optimization - Make required if enabled
OPTIMIZATION_ENABLED = get_bool("OPTIMIZATION_ENABLED", default=True) # Keep default for bool flag
OPTIMIZATION_SCHEDULE = get_string("OPTIMIZATION_SCHEDULE", required=OPTIMIZATION_ENABLED)
OPTIMIZATION_PROMPT_THRESHOLD = get_float("OPTIMIZATION_PROMPT_THRESHOLD", required=OPTIMIZATION_ENABLED)
OPTIMIZATION_MIN_FREQUENCY = get_int("OPTIMIZATION_MIN_FREQUENCY", required=OPTIMIZATION_ENABLED)
OPTIMIZATION_FREQUENCY_BUFFER_FACTOR = get_float("OPTIMIZATION_FREQUENCY_BUFFER_FACTOR", required=OPTIMIZATION_ENABLED)
OPTIMIZATION_MEMORY_QUERY_DAYS = get_int("OPTIMIZATION_MEMORY_QUERY_DAYS", required=OPTIMIZATION_ENABLED)

# Memory Service - Make these required
MEMDIR_PRUNE_MAX_AGE_DAYS = get_int("MEMDIR_PRUNE_MAX_AGE_DAYS", required=True)
MEMDIR_PRUNE_MAX_COUNT = get_int("MEMDIR_PRUNE_MAX_COUNT", required=True)
MEMDIR_ORGANIZER_MODEL = get_string("MEMDIR_ORGANIZER_MODEL", required=True)

# Orchestration Service - Make required
MAIN_LOOP_SLEEP_INTERVAL = get_int("MAIN_LOOP_SLEEP_INTERVAL", required=True)
LIQUIDATE_ON_CLOSE = get_bool("LIQUIDATE_ON_CLOSE", default=False) # Keep default for bool flag

# --- Ensure Log Directory Exists ---
os.makedirs(LOG_PATH, exist_ok=True)

# --- Basic Validation (Example) ---
if MATTERMOST_ENABLED and not all([MATTERMOST_URL, MATTERMOST_TOKEN, MATTERMOST_TEAM_ID, MATTERMOST_CHANNEL_ID]):
    logging.warning("Mattermost is enabled, but some configuration parameters are missing.")
if EMAIL_ENABLED and not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, ADMIN_EMAIL]):
    logging.warning("Email notifications are enabled, but some SMTP configuration parameters are missing.")

# You can add more validation checks here as needed

# print("--- Configuration Loaded ---")
# print(f"Alpaca Key: {ALPACA_API_KEY[:5]}...")
# print(f"Memdir Path: {MEMDIR_PATH}")
# print(f"Log Path: {LOG_PATH}")
# print(f"Log File Path: {LOG_FILE_PATH}")
# print(f"Mattermost Enabled: {MATTERMOST_ENABLED}")
# print("--------------------------")
