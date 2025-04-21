"""Custom exception classes for the trading system."""

class TradingSystemError(Exception):
    """Base exception class for all application-specific errors."""
    pass

# --- Configuration Errors ---
class ConfigError(TradingSystemError):
    """Errors related to configuration loading or validation."""
    pass

# --- Interface Errors ---
class InterfaceError(TradingSystemError):
    """Base class for errors originating from external interfaces."""
    pass

class BrokerageError(InterfaceError):
    """Errors related to the brokerage API (e.g., Alpaca)."""
    pass

class LLMError(InterfaceError):
    """Errors related to Large Language Model APIs (e.g., OpenAI, Gemini)."""
    pass

class NotificationError(InterfaceError):
    """Errors related to notification services (e.g., Mattermost, Email)."""
    pass

class WebDataError(InterfaceError):
    """Errors related to fetching web data (if used)."""
    pass

# --- Service Errors ---
class ServiceError(TradingSystemError):
    """Base class for errors originating within core services."""
    pass

class AIServiceError(ServiceError):
    """Errors specific to the AI Service."""
    pass

class ExecutionServiceError(ServiceError):
    """Errors specific to the Execution Service (e.g., order placement, portfolio tracking)."""
    pass

class InsufficientFundsError(ExecutionServiceError):
    """Specific error for insufficient funds during trade execution."""
    pass

class OrderValidationError(ExecutionServiceError):
    """Error during pre-trade validation checks."""
    pass

class MemoryServiceError(ServiceError):
    """Errors specific to the Memory Service (e.g., file operations, querying)."""
    pass

class MemdirIOError(MemoryServiceError):
    """Errors related to filesystem operations within Memdir."""
    pass

class MemoryQueryError(MemoryServiceError):
    """Errors during the querying of memories."""
    pass

class OptimizationServiceError(ServiceError):
    """Errors specific to the Optimization Service."""
    pass

class OrchestrationError(ServiceError):
    """Errors specific to the Orchestration Service (main loop, scheduling)."""
    pass

# --- Data Model Errors ---
class DataValidationError(TradingSystemError):
    """Errors related to data model validation (e.g., Pydantic)."""
    pass

# --- Other Specific Errors ---
class SignalProcessingError(TradingSystemError):
    """Errors during the processing or translation of trading signals."""
    pass

class MarketClosedError(TradingSystemError):
    """Error raised when attempting operations while the market is closed."""
    pass
class ExternalAPIError(InterfaceError):
    """Errors related to external API calls (e.g., Perplexity, other web services)."""
    pass
