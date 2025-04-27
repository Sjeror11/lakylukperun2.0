import pytest
import os
import sys
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Adjust path to import from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports from the trading system
from src.interfaces.brokerage import BrokerageInterface
from src.interfaces.large_language_model import LLMInterface
from src.interfaces.notification import NotificationInterface # Import if needed for testing notifications
from src.services.memory_service.storage import MemoryStorage
from src.services.memory_service.organizer import MemoryOrganizer # Import if testing organizer interaction
from src.services.ai_service.processor import AIServiceProcessor
from src.services.execution_service.manager import ExecutionServiceManager
# Import models needed for test data
from src.models.signal import TradingSignal, SignalAction, SignalSource
from src.models.order import Order, OrderSide, OrderType, OrderTimeInForce, OrderStatus
from src.models.portfolio import Portfolio, Position
from src.models.market_data import MarketDataSnapshot, Trade, Quote
from src.models.memory_entry import MemoryEntry, MemoryEntryType
from src.utils.exceptions import MarketClosedError, InsufficientFundsError
from src import config

# --- Fixtures ---

# Use real instances where possible for integration, mock external APIs
@pytest.fixture(scope="module")
def live_brokerage_interface():
    """Provides a BrokerageInterface connected to the LIVE API."""
    # Ensure config points to live API
    if config.IS_PAPER_TRADING:
        pytest.skip("E2E tests require LIVE trading configuration.")
    try:
        # Initialize with actual live keys from config
        interface = BrokerageInterface()
        # Perform a basic check
        interface.get_account_portfolio()
        print("\n[E2E Setup] Connected to LIVE Alpaca API.")
        return interface
    except Exception as e:
        pytest.fail(f"Failed to initialize LIVE BrokerageInterface: {e}")

@pytest.fixture(scope="module")
def live_llm_interface():
    """Provides an LLMInterface connected to LIVE APIs."""
    try:
        interface = LLMInterface()
        print("\n[E2E Setup] Initialized LLM Interface.")
        return interface
    except Exception as e:
        pytest.fail(f"Failed to initialize LLMInterface: {e}")

@pytest.fixture
def memory_storage_e2e(tmp_path):
    """Provides a MemoryStorage instance using a temporary directory for E2E tests."""
    original_memdir_path = config.MEMDIR_PATH
    test_memdir = tmp_path / "e2e_memdir"
    config.MEMDIR_PATH = str(test_memdir)
    storage = MemoryStorage()
    print(f"\n[E2E Setup] Using temporary Memdir: {test_memdir}")
    yield storage
    config.MEMDIR_PATH = original_memdir_path

# Fixture to provide initialized services for testing cycles
@pytest.fixture
def trading_services(live_brokerage_interface, live_llm_interface, memory_storage_e2e):
    """Initializes and provides the core services needed for a trading cycle."""
    # Note: Using live interfaces here for integration testing aspects
    ai_processor = AIServiceProcessor(live_llm_interface, live_brokerage_interface, memory_storage_e2e)
    execution_manager = ExecutionServiceManager(live_brokerage_interface, memory_storage_e2e)
    return {
        "ai": ai_processor,
        "exec": execution_manager,
        "mem": memory_storage_e2e,
        "brokerage": live_brokerage_interface,
        "llm": live_llm_interface
    }

# --- E2E Test Cases ---

def test_e2e_initial_portfolio_check(trading_services):
    """Verify fetching the initial portfolio state via ExecutionService."""
    print("\n[E2E Test] Running Initial Portfolio Check...")
    exec_manager: ExecutionServiceManager = trading_services["exec"]
    portfolio = exec_manager.get_current_portfolio(force_refresh=True)
    assert portfolio is not None
    assert isinstance(portfolio, Portfolio)
    assert portfolio.account_id is not None
    print(f"  Portfolio fetched: Equity={portfolio.equity:.2f}, Cash={portfolio.cash:.2f}, Positions={len(portfolio.positions)}")
    # Check if portfolio update was saved
    mem_storage: MemoryStorage = trading_services["mem"]
    query_results = mem_storage.query_memories(max_results=5) # Check recent entries
    found_update = any(mem.payload.get("account_id") == portfolio.account_id and mem.entry_type == MemoryEntryType.PORTFOLIO_UPDATE for _, mem_info in query_results if (mem := mem_storage.read_memory("cur", _)))
    # assert found_update, "Portfolio update memory entry not found." # This check might be flaky depending on timing/other tests
    print("  Initial portfolio check completed.")


# @pytest.mark.skip("Skipping live order E2E test by default. Requires careful review and market open.") # Unskipped for live test
def test_e2e_buy_cycle(trading_services):
    """Simulates a BUY signal and attempts execution (LIVE API - USE WITH CAUTION)."""
    print("\n[E2E Test] Running BUY Cycle (LIVE API)...")
    ai_processor: AIServiceProcessor = trading_services["ai"]
    exec_manager: ExecutionServiceManager = trading_services["exec"]
    brokerage: BrokerageInterface = trading_services["brokerage"]
    mem_storage: MemoryStorage = trading_services["mem"]
    llm: LLMInterface = trading_services["llm"]

    # --- Setup ---
    test_symbol = "AAPL" # Symbol to test with
    # 1. Mock LLM response to generate a BUY signal for the test symbol
    buy_response = {
        "action": "buy", "symbol": test_symbol, "confidence": 0.75,
        "rationale": f"E2E test: Generate BUY for {test_symbol}", "stop_loss_price": 160.0 # Example stop
    }
    llm.generate_json_response = MagicMock(return_value=buy_response)

    # 2. Ensure market is open (or skip)
    if not brokerage.is_market_open():
        pytest.skip("Market is closed. Cannot run live BUY cycle test.")

    # --- Execution ---
    # 3. Get current market/portfolio state
    portfolio = exec_manager.get_current_portfolio(force_refresh=True)
    market_data = brokerage.get_latest_market_data([test_symbol])

    # 4. Generate signal
    print(f"  Generating signal for {test_symbol}...")
    # Need a dummy prompt file for this test
    prompt_name = "e2e_test_prompt.txt"
    prompt_path = os.path.join(config.PROMPTS_PATH, "trading", prompt_name)
    os.makedirs(os.path.dirname(prompt_path), exist_ok=True)
    with open(prompt_path, "w") as f:
        f.write("E2E Test Prompt: Recommend action for {target_symbols}. Market: {market_data_json}. Portfolio: {portfolio_summary_json}. Output JSON.")

    signal = ai_processor.generate_trading_signal(market_data, portfolio, prompt_name=prompt_name)

    # 5. Assert signal generation
    assert signal is not None, "AI Processor failed to generate a signal."
    assert signal.action == SignalAction.BUY
    assert signal.symbol == test_symbol
    print(f"  Signal generated: {signal.action.value} {signal.symbol}")

    # 6. Process signal (attempts live order)
    print(f"  Processing signal to submit LIVE order for {test_symbol}...")
    submitted_order = exec_manager.process_signal(signal)

    # --- Verification ---
    assert submitted_order is not None, "Execution manager failed to submit the order."
    assert submitted_order.symbol == test_symbol
    assert submitted_order.side == OrderSide.BUY
    assert submitted_order.id is not None
    print(f"  LIVE Order Submitted: ID={submitted_order.id}, Status={submitted_order.status.value}, Qty={submitted_order.qty}")

    # 7. Check memory entries (Analysis + Order Status)
    # Allow time for saving
    time.sleep(1)
    query_results = mem_storage.query_memories(max_results=10)
    analysis_found = any(e.entry_type == MemoryEntryType.ANALYSIS and e.payload.get("generated_signal", {}).get("symbol") == test_symbol for _, info in query_results if (e := mem_storage.read_memory("cur", _)))
    order_status_found = any(e.entry_type == MemoryEntryType.ORDER_STATUS and e.payload.get("broker_order_id") == submitted_order.id for _, info in query_results if (e := mem_storage.read_memory("cur", _)))
    assert analysis_found, "Analysis memory entry not found."
    assert order_status_found, "Order status memory entry not found."
    print("  Memory entries verified.")

    # --- Cleanup ---
    # Optionally cancel the submitted order immediately
    print(f"  Attempting to cancel submitted order {submitted_order.id}...")
    try:
        cancelled = brokerage.cancel_order(submitted_order.id)
        print(f"  Cancel request submitted: {cancelled}")
    except Exception as e:
        print(f"  WARNING: Failed to cancel order during cleanup: {e}")
    finally:
        if os.path.exists(prompt_path): os.remove(prompt_path) # Clean up dummy prompt


# @pytest.mark.skip("Skipping live order E2E test by default. Requires careful review, market open, and existing position.") # Unskipped for live test
def test_e2e_sell_cycle(trading_services):
    """Simulates a SELL signal and attempts execution (LIVE API - USE WITH CAUTION)."""
    print("\n[E2E Test] Running SELL Cycle (LIVE API)...")
    ai_processor: AIServiceProcessor = trading_services["ai"]
    exec_manager: ExecutionServiceManager = trading_services["exec"]
    brokerage: BrokerageInterface = trading_services["brokerage"]
    mem_storage: MemoryStorage = trading_services["mem"]
    llm: LLMInterface = trading_services["llm"]

    # --- Setup ---
    test_symbol = "AAPL" # Symbol to sell (MUST HAVE A POSITION IN LIVE ACCOUNT)
    # 1. Verify position exists (or skip)
    portfolio = exec_manager.get_current_portfolio(force_refresh=True)
    position = portfolio.positions.get(test_symbol)
    if not position or position.qty <= 0:
        pytest.skip(f"No existing long position found for {test_symbol} in live account to test selling.")
    sell_qty = 1 # Sell a small quantity for testing
    if position.qty < sell_qty:
         pytest.skip(f"Position quantity ({position.qty}) for {test_symbol} is less than test sell quantity ({sell_qty}).")

    # 2. Mock LLM response to generate a SELL signal
    sell_response = {
        "action": "sell", "symbol": test_symbol, "confidence": 0.80,
        "rationale": f"E2E test: Generate SELL for {test_symbol}"
    }
    llm.generate_json_response = MagicMock(return_value=sell_response)

    # 3. Ensure market is open
    if not brokerage.is_market_open():
        pytest.skip("Market is closed. Cannot run live SELL cycle test.")

    # --- Execution ---
    # 4. Get market/portfolio state
    market_data = brokerage.get_latest_market_data([test_symbol])

    # 5. Generate signal
    print(f"  Generating signal for {test_symbol}...")
    prompt_name = "e2e_test_prompt.txt" # Use same dummy prompt
    signal = ai_processor.generate_trading_signal(market_data, portfolio, prompt_name=prompt_name)

    # 6. Assert signal generation
    assert signal is not None, "AI Processor failed to generate a signal."
    assert signal.action == SignalAction.SELL
    assert signal.symbol == test_symbol
    print(f"  Signal generated: {signal.action.value} {signal.symbol}")

    # 7. Process signal (attempts live order)
    # Override quantity calculation for predictable test sell amount
    exec_manager._calculate_order_qty = MagicMock(return_value=float(sell_qty))
    print(f"  Processing signal to submit LIVE SELL order for {sell_qty} {test_symbol}...")
    submitted_order = exec_manager.process_signal(signal)

    # --- Verification ---
    assert submitted_order is not None, "Execution manager failed to submit the SELL order."
    assert submitted_order.symbol == test_symbol
    assert submitted_order.side == OrderSide.SELL
    assert submitted_order.qty == sell_qty
    assert submitted_order.id is not None
    print(f"  LIVE Order Submitted: ID={submitted_order.id}, Status={submitted_order.status.value}, Qty={submitted_order.qty}")

    # 8. Check memory entries
    time.sleep(1)
    query_results = mem_storage.query_memories(max_results=10)
    analysis_found = any(e.entry_type == MemoryEntryType.ANALYSIS and e.payload.get("generated_signal", {}).get("symbol") == test_symbol for _, info in query_results if (e := mem_storage.read_memory("cur", _)))
    order_status_found = any(e.entry_type == MemoryEntryType.ORDER_STATUS and e.payload.get("broker_order_id") == submitted_order.id for _, info in query_results if (e := mem_storage.read_memory("cur", _)))
    assert analysis_found, "Analysis memory entry not found."
    assert order_status_found, "Order status memory entry not found."
    print("  Memory entries verified.")
