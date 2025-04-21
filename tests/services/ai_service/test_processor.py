import pytest
import os
import sys
import json
import uuid
from unittest.mock import MagicMock, patch, mock_open

# Adjust path to import from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports from the trading system
from src.services.ai_service.processor import AIServiceProcessor, DEFAULT_PROMPT_FILENAME, AI_SERVICE_SOURCE
from src.interfaces.large_language_model import LLMInterface
from src.interfaces.brokerage import BrokerageInterface
from src.services.memory_service.storage import MemoryStorage
from src.models.signal import TradingSignal, SignalAction, SignalSource
from src.models.market_data import MarketDataSnapshot
from src.models.portfolio import Portfolio
from src.models.memory_entry import MemoryEntry, MemoryEntryType
from src.utils.exceptions import AIServiceError, LLMError, ConfigError, MemoryServiceError
from src import config

# --- Fixtures ---

@pytest.fixture
def mock_llm():
    """Provides a mocked LLMInterface."""
    return MagicMock(spec=LLMInterface)

@pytest.fixture
def mock_brokerage():
    """Provides a mocked BrokerageInterface."""
    return MagicMock(spec=BrokerageInterface)

@pytest.fixture
def mock_memory_storage():
    """Provides a mocked MemoryStorage."""
    mock = MagicMock(spec=MemoryStorage)
    mock.save_memory.return_value = "mock_memory_filename.json" # Simulate successful save
    return mock

@pytest.fixture
def ai_processor(mock_llm, mock_brokerage, mock_memory_storage):
    """Provides an AIServiceProcessor instance with mocked dependencies."""
    # Temporarily override prompts path if needed, or ensure it exists
    # For simplicity, we'll mock the file reading directly in tests
    return AIServiceProcessor(
        llm_interface=mock_llm,
        brokerage_interface=mock_brokerage,
        memory_storage=mock_memory_storage
    )

@pytest.fixture
def dummy_market_data():
    """Provides a dummy MarketDataSnapshot."""
    return MarketDataSnapshot() # Empty for basic tests

@pytest.fixture
def dummy_portfolio():
    """Provides a dummy Portfolio."""
    return Portfolio(account_id="test_acc", cash=10000, equity=10000, buying_power=20000, portfolio_value=10000)

# --- Test Data ---
DUMMY_PROMPT_CONTENT = """
Current Time UTC: {current_datetime_utc}
Analyze market: {market_data_json}
Portfolio: {portfolio_summary_json}
Positions: {positions_json}
History: {recent_history_summary}
Recommend action for {target_symbols}.
Output JSON: {{"action": "buy|sell|hold", "symbol": "SYMBOL", "confidence": 0.0-1.0, "rationale": "..."}}
"""

LLM_RESPONSE_BUY = {
    "action": "buy",
    "symbol": "AAPL",
    "confidence": 0.85,
    "rationale": "Strong upward trend detected."
}

LLM_RESPONSE_HOLD = {
    "action": "hold",
    "symbol": "MSFT",
    "rationale": "Neutral indicators."
}

LLM_RESPONSE_INVALID_ACTION = {
    "action": "wait", # Invalid action
    "symbol": "GOOG",
    "rationale": "Market unclear."
}

LLM_RESPONSE_MISSING_SYMBOL = {
    "action": "buy",
    "confidence": 0.7,
    "rationale": "Good setup."
    # Missing symbol
}

# --- Tests ---

@patch("builtins.open", new_callable=mock_open, read_data=DUMMY_PROMPT_CONTENT)
def test_load_prompt_success(mock_file, ai_processor):
    """Tests successfully loading a prompt file."""
    prompt_name = "test_prompt.txt"
    content = ai_processor._load_prompt(prompt_name)
    expected_path = os.path.join(ai_processor.prompts_path, "trading", prompt_name)
    mock_file.assert_called_once_with(expected_path, 'r', encoding='utf-8')
    assert content == DUMMY_PROMPT_CONTENT

@patch("builtins.open", side_effect=FileNotFoundError)
def test_load_prompt_not_found(mock_file, ai_processor):
    """Tests handling when a prompt file is not found."""
    with pytest.raises(ConfigError, match="Required prompt file missing"):
        ai_processor._load_prompt("non_existent_prompt.txt")

def test_format_input_data(ai_processor, dummy_market_data, dummy_portfolio):
    """Tests the formatting of input data into a prompt string."""
    formatted_prompt = ai_processor._format_input_data(
        DUMMY_PROMPT_CONTENT, dummy_market_data, dummy_portfolio
    )
    assert isinstance(formatted_prompt, str)
    # Check if placeholders were replaced (presence of JSON-like structures)
    assert '"cash": 10000.0' in formatted_prompt # From portfolio (Note: Pydantic might add .0)
    assert '"latest_bars"' in formatted_prompt # Check key exists, value might be null or missing if excluded
    assert f"Recommend action for {', '.join(config.DEFAULT_SYMBOLS)}" in formatted_prompt
    assert "Current Time UTC:" in formatted_prompt # Check if datetime placeholder was replaced

def test_parse_llm_response_buy_signal(ai_processor):
    """Tests parsing a valid BUY signal response from the LLM."""
    signal = ai_processor._parse_llm_response(LLM_RESPONSE_BUY)
    assert isinstance(signal, TradingSignal)
    assert signal.action == SignalAction.BUY
    assert signal.symbol == "AAPL"
    assert signal.confidence == 0.85
    assert signal.rationale == "Strong upward trend detected."
    assert signal.source == SignalSource.AI_ANALYSIS
    assert signal.signal_id.startswith("sig_")

def test_parse_llm_response_hold_signal(ai_processor):
    """Tests parsing a HOLD signal response (should return None)."""
    signal = ai_processor._parse_llm_response(LLM_RESPONSE_HOLD)
    assert signal is None

def test_parse_llm_response_invalid_action(ai_processor):
    """Tests parsing a response with an invalid action."""
    signal = ai_processor._parse_llm_response(LLM_RESPONSE_INVALID_ACTION)
    assert signal is None

def test_parse_llm_response_missing_field(ai_processor):
    """Tests parsing a response missing a required field (symbol)."""
    signal = ai_processor._parse_llm_response(LLM_RESPONSE_MISSING_SYMBOL)
    assert signal is None

def test_parse_llm_response_invalid_json_structure(ai_processor):
    """Tests parsing an invalid JSON structure (not a dict)."""
    with pytest.raises(AIServiceError, match="Failed to parse LLM response"):
        ai_processor._parse_llm_response(["this", "is", "a", "list"]) # Pass invalid type

@patch("builtins.open", new_callable=mock_open, read_data=DUMMY_PROMPT_CONTENT)
def test_generate_trading_signal_success_buy(mock_file, ai_processor, mock_llm, mock_memory_storage, dummy_market_data, dummy_portfolio):
    """Tests the end-to-end signal generation process for a BUY signal."""
    # Configure mock LLM to return a BUY response
    mock_llm.generate_json_response.return_value = LLM_RESPONSE_BUY

    signal = ai_processor.generate_trading_signal(dummy_market_data, dummy_portfolio)

    # Verify signal
    assert isinstance(signal, TradingSignal)
    assert signal.action == SignalAction.BUY
    assert signal.symbol == "AAPL"
    assert signal.originating_memory_id is not None # Should be linked to the saved analysis entry

    # Verify LLM call
    mock_llm.generate_json_response.assert_called_once()

    # Verify memory storage call (should save ANALYSIS entry)
    mock_memory_storage.save_memory.assert_called_once()
    saved_entry_arg = mock_memory_storage.save_memory.call_args[0][0]
    assert isinstance(saved_entry_arg, MemoryEntry)
    assert saved_entry_arg.entry_type == MemoryEntryType.ANALYSIS
    assert saved_entry_arg.source_service == AI_SERVICE_SOURCE
    assert saved_entry_arg.payload["prompt_name"] == DEFAULT_PROMPT_FILENAME
    assert saved_entry_arg.payload["raw_llm_response"] == LLM_RESPONSE_BUY
    assert saved_entry_arg.payload["generated_signal"] is not None
    assert saved_entry_arg.payload["generated_signal"]["symbol"] == "AAPL"
    # Check that the signal's originating ID matches the saved entry's ID
    assert signal.originating_memory_id == saved_entry_arg.entry_id


@patch("builtins.open", new_callable=mock_open, read_data=DUMMY_PROMPT_CONTENT)
def test_generate_trading_signal_success_hold(mock_file, ai_processor, mock_llm, mock_memory_storage, dummy_market_data, dummy_portfolio):
    """Tests the end-to-end signal generation process for a HOLD signal."""
    # Configure mock LLM to return a HOLD response
    mock_llm.generate_json_response.return_value = LLM_RESPONSE_HOLD

    signal = ai_processor.generate_trading_signal(dummy_market_data, dummy_portfolio)

    # Verify no signal is returned
    assert signal is None

    # Verify LLM call
    mock_llm.generate_json_response.assert_called_once()

    # Verify memory storage call (should save ANALYSIS entry, but signal is None)
    mock_memory_storage.save_memory.assert_called_once()
    saved_entry_arg = mock_memory_storage.save_memory.call_args[0][0]
    assert saved_entry_arg.entry_type == MemoryEntryType.ANALYSIS
    assert saved_entry_arg.payload["raw_llm_response"] == LLM_RESPONSE_HOLD
    assert saved_entry_arg.payload["generated_signal"] is None

@patch("builtins.open", new_callable=mock_open, read_data=DUMMY_PROMPT_CONTENT)
def test_generate_trading_signal_llm_error(mock_file, ai_processor, mock_llm, mock_memory_storage, dummy_market_data, dummy_portfolio):
    """Tests signal generation when the LLM call fails."""
    # Configure mock LLM to raise an error
    llm_error_message = "Simulated API timeout"
    mock_llm.generate_json_response.side_effect = LLMError(llm_error_message)

    signal = ai_processor.generate_trading_signal(dummy_market_data, dummy_portfolio)

    # Verify no signal is returned
    assert signal is None

    # Verify memory storage call (should save ERROR entry)
    mock_memory_storage.save_memory.assert_called_once()
    saved_entry_arg = mock_memory_storage.save_memory.call_args[0][0]
    assert saved_entry_arg.entry_type == MemoryEntryType.ERROR
    assert saved_entry_arg.source_service == AI_SERVICE_SOURCE
    assert saved_entry_arg.payload["error_type"] == "LLMError"
    assert saved_entry_arg.payload["error_message"] == llm_error_message
    assert saved_entry_arg.payload["stage"] == "SignalGeneration"

@patch("builtins.open", new_callable=mock_open, read_data=DUMMY_PROMPT_CONTENT)
def test_generate_trading_signal_memory_save_error(mock_file, ai_processor, mock_llm, mock_memory_storage, dummy_market_data, dummy_portfolio):
    """Tests signal generation when saving the analysis to memory fails."""
    # Configure mock LLM to return successfully
    mock_llm.generate_json_response.return_value = LLM_RESPONSE_BUY
    # Configure mock memory storage to raise error on save
    memory_error_message = "Simulated disk full"
    mock_memory_storage.save_memory.side_effect = MemoryServiceError(memory_error_message)

    signal = ai_processor.generate_trading_signal(dummy_market_data, dummy_portfolio)

    # Verify signal IS still returned (error during saving shouldn't prevent signal)
    assert isinstance(signal, TradingSignal)
    assert signal.action == SignalAction.BUY

    # Verify memory save was attempted twice: once for analysis, once for the error
    assert mock_memory_storage.save_memory.call_count == 2
    # First call should be the analysis entry
    first_call_args = mock_memory_storage.save_memory.call_args_list[0][0][0]
    assert isinstance(first_call_args, MemoryEntry)
    assert first_call_args.entry_type == MemoryEntryType.ANALYSIS
    # Second call should be the error entry because the first one failed
    second_call_args = mock_memory_storage.save_memory.call_args_list[1][0][0]
    assert isinstance(second_call_args, MemoryEntry)
    assert second_call_args.entry_type == MemoryEntryType.ERROR
    assert second_call_args.payload["error_type"] == "MemoryServiceError"
    assert second_call_args.payload["error_message"] == memory_error_message
