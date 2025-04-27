import pytest
import os
import sys
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone # Added timezone

# Adjust path to import from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports from the trading system
from src.services.execution_service.manager import ExecutionServiceManager, EXECUTION_SERVICE_SOURCE
from src.interfaces.brokerage import BrokerageInterface
from src.services.memory_service.storage import MemoryStorage
from src.models.signal import TradingSignal, SignalAction, SignalSource
from src.models.order import Order, OrderSide, OrderType, OrderTimeInForce, OrderStatus
from src.models.portfolio import Portfolio, Position
from src.models.market_data import MarketDataSnapshot, Trade, Quote # Import needed models
from src.models.memory_entry import MemoryEntry, MemoryEntryType
from src.utils.exceptions import (
    ExecutionServiceError, BrokerageError, InsufficientFundsError,
    OrderValidationError, MarketClosedError, MemoryServiceError
)
from src import config

# --- Fixtures ---

@pytest.fixture
def mock_brokerage():
    """Provides a mocked BrokerageInterface."""
    mock = MagicMock(spec=BrokerageInterface)
    # Default mock portfolio
    mock.get_account_portfolio.return_value = Portfolio(
        account_id="test_paper_acc", cash=50000, equity=50000, buying_power=100000, portfolio_value=50000, shorting_enabled=True, positions={}
    )
    # Mock market status
    mock.is_market_open.return_value = True
    # Mock order submission
    def mock_submit(order_data: Order):
        order_data.id = f"sim_brkr_{uuid.uuid4()}"
        order_data.status = OrderStatus.ACCEPTED # Simulate acceptance
        order_data.submitted_at = datetime.now(timezone.utc) # Use timezone-aware now()
        return order_data
    mock.submit_order.side_effect = mock_submit
    # Mock latest data
    mock.get_latest_market_data.return_value = MarketDataSnapshot(
        latest_trades={
            "AAPL": Trade(symbol="AAPL", timestamp=datetime.now(timezone.utc), price=175.0, size=10), # Use timezone-aware now()
            "MSFT": Trade(symbol="MSFT", timestamp=datetime.now(timezone.utc), price=310.0, size=5), # Use timezone-aware now()
            "NEW": Trade(symbol="NEW", timestamp=datetime.now(timezone.utc), price=50.0, size=1), # Use timezone-aware now()
        },
        latest_quotes={ # Provide quotes as fallback if trades are missing
             "AAPL": Quote(symbol="AAPL", timestamp=datetime.now(timezone.utc), ask_price=175.05, bid_price=174.95, ask_size=100, bid_size=100), # Use timezone-aware now()
             "MSFT": Quote(symbol="MSFT", timestamp=datetime.now(timezone.utc), ask_price=310.10, bid_price=310.00, ask_size=100, bid_size=100), # Use timezone-aware now()
             "NEW": Quote(symbol="NEW", timestamp=datetime.now(timezone.utc), ask_price=50.05, bid_price=49.95, ask_size=100, bid_size=100), # Use timezone-aware now()
        }
    )
    return mock

@pytest.fixture
def mock_memory_storage():
    """Provides a mocked MemoryStorage."""
    mock = MagicMock(spec=MemoryStorage)
    mock.save_memory.return_value = "mock_exec_mem.json"
    return mock

@pytest.fixture
def execution_manager(mock_brokerage, mock_memory_storage):
    """Provides an ExecutionServiceManager instance with mocked dependencies."""
    # Temporarily adjust config if needed for tests
    original_risk = config.RISK_LIMIT_PERCENT
    config.RISK_LIMIT_PERCENT = 0.01 # Use 1% risk for easier calculation in tests
    manager = ExecutionServiceManager(
        brokerage_interface=mock_brokerage,
        memory_storage=mock_memory_storage
    )
    # Reset mocks *after* initial portfolio fetch in __init__
    mock_brokerage.reset_mock()
    mock_memory_storage.reset_mock()
    yield manager
    # Restore original config
    config.RISK_LIMIT_PERCENT = original_risk


# --- Test Data ---

BUY_SIGNAL_AAPL = TradingSignal(
    signal_id=f"sig_{uuid.uuid4()}", symbol="AAPL", action=SignalAction.BUY, confidence=0.8, stop_loss_price=170.0 # 5 point stop loss
)
SELL_SIGNAL_MSFT = TradingSignal(
    signal_id=f"sig_{uuid.uuid4()}", symbol="MSFT", action=SignalAction.SELL, confidence=0.7, stop_loss_price=320.0 # 10 point stop loss
)
HOLD_SIGNAL_GOOG = TradingSignal(
    signal_id=f"sig_{uuid.uuid4()}", symbol="GOOG", action=SignalAction.HOLD
)
BUY_SIGNAL_NEW = TradingSignal(
    signal_id=f"sig_{uuid.uuid4()}", symbol="NEW", action=SignalAction.BUY, confidence=0.9, stop_loss_price=45.0 # $5 stop loss
)

# --- Tests ---

def test_initialization_and_portfolio_fetch(mock_brokerage, mock_memory_storage):
    """Tests initialization fetches portfolio and saves memory."""
    # Need to re-init manager here as the fixture resets mocks after init
    manager = ExecutionServiceManager(mock_brokerage, mock_memory_storage)
    assert manager.brokerage == mock_brokerage
    assert manager.memory == mock_memory_storage
    assert manager._current_portfolio is not None
    assert manager._current_portfolio.cash == 50000
    # Check that portfolio update was fetched and saved to memory on init
    mock_brokerage.get_account_portfolio.assert_called_once()
    mock_memory_storage.save_memory.assert_called_once()
    saved_entry = mock_memory_storage.save_memory.call_args[0][0]
    assert isinstance(saved_entry, MemoryEntry)
    assert saved_entry.entry_type == MemoryEntryType.PORTFOLIO_UPDATE

def test_calculate_order_qty_stop_loss(execution_manager):
    """Tests quantity calculation based on stop loss and risk %."""
    portfolio = execution_manager.get_current_portfolio() # Gets the mocked portfolio
    # Risk = 50000 * 0.01 = 500
    # Price = 175, Stop = 170 -> Diff = 5
    # Qty = 500 / 5 = 100
    qty = execution_manager._calculate_order_qty(BUY_SIGNAL_AAPL, portfolio)
    # Max Size = 10000 -> Max Qty = 10000 / 175 = 57.14... -> Final Qty = 57
    assert qty == 57.0 # Corrected assertion

def test_calculate_order_qty_no_stop_loss(execution_manager):
    """Tests quantity calculation fallback when no stop loss is provided."""
    portfolio = execution_manager.get_current_portfolio()
    signal_no_stop = TradingSignal(signal_id="s2", symbol="MSFT", action=SignalAction.BUY, confidence=0.7)
    # Risk = 50000 * 0.01 = 500
    # Price = 310
    # Qty = 500 / 310 = 1.61... -> rounded down to 1
    qty = execution_manager._calculate_order_qty(signal_no_stop, portfolio)
    assert qty == 1.0

def test_calculate_order_qty_max_position_size(execution_manager):
    """Tests quantity calculation respecting max position size."""
    portfolio = execution_manager.get_current_portfolio()
    # Risk = 500
    # Price = 175, Stop = 170 -> Diff = 5 -> Risk Qty = 100
    # Max Size = 10000 (from default config)
    # Max Qty by Value = 10000 / 175 = 57.14...
    # Final Qty = min(100, 57.14...) -> rounded down to 57
    with patch('src.config.MAX_POSITION_SIZE', 10000): # Ensure config value
         qty = execution_manager._calculate_order_qty(BUY_SIGNAL_AAPL, portfolio)
         assert qty == 57.0

def test_calculate_order_qty_zero_equity(execution_manager):
    """Tests quantity calculation fails with zero equity."""
    portfolio = execution_manager.get_current_portfolio()
    portfolio.equity = 0.0
    with pytest.raises(OrderValidationError, match="Invalid portfolio equity"):
        execution_manager._calculate_order_qty(BUY_SIGNAL_AAPL, portfolio)

def test_pre_trade_checks_buy_sufficient_funds(execution_manager):
    """Tests pre-trade checks pass for BUY with sufficient funds."""
    portfolio = execution_manager.get_current_portfolio() # buying_power=100000
    order = Order(client_order_id="c1", symbol="AAPL", qty=10, side=OrderSide.BUY, type=OrderType.MARKET, time_in_force=OrderTimeInForce.DAY)
    # Cost ~ 10 * 175 * 1.01 = 1767.5 < 100000
    try:
        execution_manager._perform_pre_trade_checks(order, portfolio)
    except OrderValidationError as e:
        pytest.fail(f"Pre-trade check failed unexpectedly: {e}")

def test_pre_trade_checks_buy_insufficient_funds(execution_manager):
    """Tests pre-trade checks fail for BUY with insufficient funds."""
    portfolio = execution_manager.get_current_portfolio()
    portfolio.buying_power = 1000 # Set low buying power
    order = Order(client_order_id="c2", symbol="AAPL", qty=10, side=OrderSide.BUY, type=OrderType.MARKET, time_in_force=OrderTimeInForce.DAY)
    # Cost ~ 1767.5 > 1000
    with pytest.raises(InsufficientFundsError, match="Insufficient buying power"):
        execution_manager._perform_pre_trade_checks(order, portfolio)

def test_pre_trade_checks_sell_sufficient_shares(execution_manager):
    """Tests pre-trade checks pass for SELL with sufficient shares."""
    portfolio = execution_manager.get_current_portfolio()
    # Add position to mock portfolio
    portfolio.positions["MSFT"] = Position(symbol="MSFT", qty=20, avg_entry_price=300, cost_basis=6000)
    order = Order(client_order_id="c3", symbol="MSFT", qty=15, side=OrderSide.SELL, type=OrderType.MARKET, time_in_force=OrderTimeInForce.DAY)
    try:
        execution_manager._perform_pre_trade_checks(order, portfolio)
    except OrderValidationError as e:
        pytest.fail(f"Pre-trade check failed unexpectedly: {e}")

def test_pre_trade_checks_sell_insufficient_shares_no_shorting(execution_manager):
    """Tests pre-trade checks fail for SELL with insufficient shares when shorting disabled."""
    portfolio = execution_manager.get_current_portfolio()
    portfolio.positions["MSFT"] = Position(symbol="MSFT", qty=5, avg_entry_price=300, cost_basis=1500)
    portfolio.shorting_enabled = False # Disable shorting
    order = Order(client_order_id="c4", symbol="MSFT", qty=10, side=OrderSide.SELL, type=OrderType.MARKET, time_in_force=OrderTimeInForce.DAY)
    with pytest.raises(OrderValidationError, match="Insufficient shares to sell MSFT.*Shorting not enabled"):
        execution_manager._perform_pre_trade_checks(order, portfolio)

def test_pre_trade_checks_sell_insufficient_shares_with_shorting(execution_manager):
    """Tests pre-trade checks pass for SELL (short) when shorting enabled."""
    portfolio = execution_manager.get_current_portfolio()
    portfolio.positions["MSFT"] = Position(symbol="MSFT", qty=5, avg_entry_price=300, cost_basis=1500)
    portfolio.shorting_enabled = True # Enable shorting
    order = Order(client_order_id="c5", symbol="MSFT", qty=10, side=OrderSide.SELL, type=OrderType.MARKET, time_in_force=OrderTimeInForce.DAY)
    try:
        execution_manager._perform_pre_trade_checks(order, portfolio)
    except OrderValidationError as e:
        pytest.fail(f"Pre-trade check failed unexpectedly for short sell: {e}")

def test_pre_trade_checks_max_positions(execution_manager):
    """Tests pre-trade checks fail when max positions reached."""
    portfolio = execution_manager.get_current_portfolio()
    # Fill portfolio with max positions
    max_pos = config.MAX_TOTAL_POSITIONS
    portfolio.positions = {f"SYM{i}": Position(symbol=f"SYM{i}", qty=1, avg_entry_price=10, cost_basis=10) for i in range(max_pos)}
    assert len(portfolio.positions) == max_pos
    # Try to buy a new symbol
    order = Order(client_order_id="c6", symbol="NEW", qty=1, side=OrderSide.BUY, type=OrderType.MARKET, time_in_force=OrderTimeInForce.DAY)
    with pytest.raises(OrderValidationError, match="Max total positions"):
        execution_manager._perform_pre_trade_checks(order, portfolio)

def test_process_signal_buy_success(execution_manager, mock_brokerage, mock_memory_storage):
    """Tests processing a valid BUY signal successfully."""
    # Mocks are reset in the fixture after init
    expected_memory_saves = 1 # Only ORDER_STATUS save expected here

    # Use BUY_SIGNAL_AAPL (stop loss = 170, price = 175 -> diff=5)
    # Risk = 50000 * 0.01 = 500. Qty = 500/5 = 100.
    # Max size = 10000 (default config from patch) -> Max Qty = 10000/175 = 57.14...
    # Final Qty = min(100, 57.14...) -> rounded down to 57
    expected_qty = 57.0 # Corrected expected quantity

    submitted_order = execution_manager.process_signal(BUY_SIGNAL_AAPL)

    assert isinstance(submitted_order, Order)
    assert submitted_order.symbol == "AAPL"
    assert submitted_order.side == OrderSide.BUY
    assert submitted_order.qty == expected_qty
    assert submitted_order.type == OrderType.MARKET # Default used in manager
    assert submitted_order.status == OrderStatus.ACCEPTED # From mock
    assert submitted_order.id is not None

    # Verify brokerage submit call
    mock_brokerage.submit_order.assert_called_once()
    call_args = mock_brokerage.submit_order.call_args[0][0] # Get the Order object passed
    assert isinstance(call_args, Order)
    assert call_args.symbol == "AAPL"
    assert call_args.qty == expected_qty
    assert call_args.side == OrderSide.BUY

    # Verify memory save calls (only one call after reset in fixture)
    assert mock_memory_storage.save_memory.call_count == expected_memory_saves
    # Check the ORDER_STATUS entry (it's the first call after reset)
    order_status_entry = mock_memory_storage.save_memory.call_args_list[0][0][0]
    assert order_status_entry.entry_type == MemoryEntryType.ORDER_STATUS
    assert order_status_entry.payload["signal_id"] == BUY_SIGNAL_AAPL.signal_id
    assert order_status_entry.payload["broker_order_id"] == submitted_order.id
    assert order_status_entry.payload["status"] == OrderStatus.ACCEPTED.value
    assert "submission_latency_ms" in order_status_entry.payload

def test_process_signal_hold(execution_manager, mock_brokerage, mock_memory_storage):
    """Tests processing a HOLD signal (should do nothing)."""
    # Mocks are reset in the fixture after init
    submitted_order = execution_manager.process_signal(HOLD_SIGNAL_GOOG)
    assert submitted_order is None
    mock_brokerage.submit_order.assert_not_called()
    # No memory should be saved by process_signal for HOLD after reset in fixture
    assert mock_memory_storage.save_memory.call_count == 0

def test_process_signal_insufficient_funds(execution_manager, mock_brokerage, mock_memory_storage):
    """Tests processing a BUY signal that fails due to insufficient funds."""
    # Mocks are reset in the fixture after init

    # Get the portfolio *after* init and modify it
    portfolio = execution_manager.get_current_portfolio(force_refresh=True) # Ensure we have the base portfolio
    portfolio.buying_power = 100 # Now modify it

    # Mock get_current_portfolio to return the modified one during the check within process_signal
    # Also need to mock the get_latest_market_data called within _perform_pre_trade_checks
    with patch.object(execution_manager, 'get_current_portfolio', return_value=portfolio), \
         patch.object(mock_brokerage, 'get_latest_market_data', return_value=mock_brokerage.get_latest_market_data.return_value): # Ensure market data mock is active

        # process_signal should catch the error internally and return None
        # Using NEW ($50 price, $5 stop loss -> Risk Qty = 500/5 = 100)
        # Estimated cost ~ 100 * $50 * 1.01 = $5050 > $100 buying power
        submitted_order = execution_manager.process_signal(BUY_SIGNAL_NEW)
        assert submitted_order is None

    mock_brokerage.submit_order.assert_not_called() # Check should fail before submission

    # Check that memory was saved twice after reset: 1 for portfolio refresh, 1 for the error
    assert mock_memory_storage.save_memory.call_count == 2
    # The second call should be the ERROR entry
    error_entry = mock_memory_storage.save_memory.call_args_list[1][0][0]
    assert error_entry.entry_type == MemoryEntryType.ERROR
    assert error_entry.payload["error_type"] == "InsufficientFundsError"
    assert error_entry.payload["signal_id"] == BUY_SIGNAL_NEW.signal_id # Check correct signal ID

def test_process_signal_market_closed(execution_manager, mock_brokerage, mock_memory_storage):
    """Tests processing a signal when the market is closed."""
    # Mocks are reset in the fixture after init

    mock_brokerage.is_market_open.return_value = False # Simulate closed market
    # Use a DAY order signal
    day_buy_signal = TradingSignal(signal_id="s_day", symbol="AAPL", action=SignalAction.BUY)

    # process_signal should catch the error internally and return None
    submitted_order = execution_manager.process_signal(day_buy_signal)
    assert submitted_order is None

    mock_brokerage.submit_order.assert_not_called()

    # Check that an ERROR memory entry was saved
    assert mock_memory_storage.save_memory.call_count == 1 # Only the error entry save should happen after reset
    error_entry = mock_memory_storage.save_memory.call_args[0][0]
    assert error_entry.entry_type == MemoryEntryType.ERROR
    assert error_entry.payload["error_type"] == "MarketClosedError"
