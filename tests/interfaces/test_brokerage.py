import pytest
import os
import sys
from datetime import datetime, timedelta
import time
import uuid

# Adjust path to import from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports from the trading system
from src.interfaces.brokerage import BrokerageInterface
from src.utils.exceptions import BrokerageError
from src.models.order import Order, OrderSide, OrderType, OrderTimeInForce, OrderStatus
from src.models.market_data import BarTimeframe
from src import config # Ensure config is loaded with test environment vars if needed

# --- Test Fixture ---

# Use a fixture to initialize the interface once per module
# This avoids reconnecting for every test function.
@pytest.fixture(scope="module")
def brokerage_interface():
    """Provides an initialized BrokerageInterface instance."""
    # Ensure we are using paper trading for tests
    if not config.IS_PAPER_TRADING:
        pytest.skip("Brokerage tests require paper trading configuration (ALPACA_BASE_URL pointing to paper-api).")
    try:
        interface = BrokerageInterface()
        return interface
    except BrokerageError as e:
        pytest.fail(f"Failed to initialize BrokerageInterface for testing: {e}")
    except Exception as e:
         pytest.fail(f"Unexpected error initializing BrokerageInterface: {e}")

# --- Basic Connection and Info Tests ---

def test_brokerage_connection_and_account(brokerage_interface):
    """Tests basic connection and fetching account info."""
    assert brokerage_interface.api is not None
    assert brokerage_interface.data_api is not None
    try:
        portfolio = brokerage_interface.get_account_portfolio()
        assert portfolio is not None
        assert portfolio.account_id is not None
        assert isinstance(portfolio.cash, float)
        assert isinstance(portfolio.equity, float)
        assert portfolio.currency == "USD" # Assuming USD account
        print(f"\n[Brokerage Test] Account ID: {portfolio.account_id}, Equity: {portfolio.equity:.2f}, Cash: {portfolio.cash:.2f}")
    except BrokerageError as e:
        pytest.fail(f"BrokerageError fetching account portfolio: {e}")

def test_market_status(brokerage_interface):
    """Tests fetching market status (open/closed)."""
    try:
        is_open = brokerage_interface.is_market_open()
        assert isinstance(is_open, bool)
        print(f"\n[Brokerage Test] Market Open: {is_open}")
        # We can't assert if it *should* be open/closed without knowing the exact test time
    except BrokerageError as e:
        pytest.fail(f"BrokerageError fetching market status: {e}")

# --- Data Retrieval Tests ---

def test_get_latest_market_data(brokerage_interface):
    """Tests fetching latest quote/trade data for default symbols."""
    symbols = config.DEFAULT_SYMBOLS[:2] # Test with a couple of symbols
    if not symbols:
         pytest.skip("No default symbols configured for testing latest market data.")
    try:
        snapshot = brokerage_interface.get_latest_market_data(symbols)
        assert snapshot is not None
        print(f"\n[Brokerage Test] Latest Snapshot Timestamp: {snapshot.timestamp}")
        for symbol in symbols:
             # Check if data exists (might be None if market closed or no recent data)
             quote = snapshot.latest_quotes.get(symbol)
             trade = snapshot.latest_trades.get(symbol)
             print(f"  Symbol {symbol}: Quote={quote is not None}, Trade={trade is not None}")
             if quote:
                  assert isinstance(quote.ask_price, float)
                  assert isinstance(quote.bid_price, float)
             # Trades might be less frequent, so don't fail if None
             # if trade:
             #      assert isinstance(trade.price, float)
             #      assert isinstance(trade.size, float)

    except BrokerageError as e:
        pytest.fail(f"BrokerageError fetching latest market data: {e}")

def test_get_bars(brokerage_interface):
    """Tests fetching historical bar data."""
    symbols = config.DEFAULT_SYMBOLS[:1] # Test with one symbol
    if not symbols:
         pytest.skip("No default symbols configured for testing bar data.")
    try:
        # Fetch last 5 daily bars
        bars_dict = brokerage_interface.get_bars(
            symbols=symbols,
            timeframe=BarTimeframe.DAY,
            limit=5
        )
        assert isinstance(bars_dict, dict)
        assert symbols[0] in bars_dict
        bars = bars_dict[symbols[0]]
        assert isinstance(bars, list)
        # Allow empty list if market just opened or no data available
        if bars:
             assert len(bars) <= 5
             bar = bars[0]
             assert bar.symbol == symbols[0]
             assert isinstance(bar.timestamp, datetime)
             assert isinstance(bar.open, float)
             assert isinstance(bar.high, float)
             assert isinstance(bar.low, float)
             assert isinstance(bar.close, float)
             assert isinstance(bar.volume, float)
             print(f"\n[Brokerage Test] Fetched {len(bars)} daily bars for {symbols[0]}. Last close: {bars[-1].close} on {bars[-1].timestamp.date()}")
        else:
             print(f"\n[Brokerage Test] Fetched 0 daily bars for {symbols[0]} (might be expected).")

    except BrokerageError as e:
        pytest.fail(f"BrokerageError fetching bars: {e}")
    except ValueError as e:
         pytest.fail(f"ValueError fetching bars (likely timeframe issue): {e}")


# --- Order Management Tests (Requires Paper Account) ---

# This test will be skipped if not using paper trading, even if the fixture runs with live keys.
@pytest.mark.skipif(not config.IS_PAPER_TRADING, reason="Order submission tests should only run against paper trading.")
def test_submit_and_list_market_order(brokerage_interface):
    """Tests submitting a small market order and listing it."""
    symbol = "AAPL" # Use a common liquid stock
    qty = 1
    client_order_id = f"test_mkt_{uuid.uuid4()}"
    order_data = Order(
        client_order_id=client_order_id,
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        time_in_force=OrderTimeInForce.DAY # Use DAY for testing
    )

    submitted_order = None
    try:
        # Check market open first
        if not brokerage_interface.is_market_open():
             pytest.skip("Market is closed, cannot place DAY market order for test.")

        print(f"\n[Brokerage Test] Submitting test market order: {order_data.side} {order_data.qty} {order_data.symbol}")
        submitted_order = brokerage_interface.submit_order(order_data)

        assert submitted_order is not None
        assert submitted_order.id is not None # Broker ID assigned
        assert submitted_order.client_order_id == client_order_id
        assert submitted_order.status in [OrderStatus.ACCEPTED, OrderStatus.PENDING_NEW, OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED] # Should be accepted quickly
        print(f"  Submitted Order ID: {submitted_order.id}, Status: {submitted_order.status.value}")

        # Allow some time for the order to appear in lists
        time.sleep(3)

        # List open orders to find it (might be filled quickly)
        print("  Listing open orders...")
        open_orders = brokerage_interface.list_orders(status='open', limit=10)
        found_open = any(o.id == submitted_order.id for o in open_orders)
        print(f"  Found in open orders: {found_open}")

        # List all orders for today to find it
        print("  Listing all orders...")
        all_orders = brokerage_interface.list_orders(status='all', limit=10, after=datetime.now(timezone.utc)-timedelta(hours=1)) # Use timezone-aware now()
        found_all = any(o.id == submitted_order.id for o in all_orders)
        assert found_all, f"Submitted order {submitted_order.id} not found in 'all' orders list."
        print(f"  Found in all orders: {found_all}")

        # Get by client ID
        print(f"  Getting order by client ID: {client_order_id}")
        retrieved_order = brokerage_interface.get_order_by_client_id(client_order_id)
        assert retrieved_order is not None
        assert retrieved_order.id == submitted_order.id
        print(f"  Retrieved Order Status: {retrieved_order.status.value}")


    except MarketClosedError as e:
         pytest.skip(f"Market closed, skipping order test: {e}")
    except BrokerageError as e:
        pytest.fail(f"BrokerageError during market order test: {e}")
    finally:
        # Attempt to cancel if submitted and still open (cleanup)
        if submitted_order and submitted_order.id:
             try:
                  final_status = brokerage_interface.get_order_by_id(submitted_order.id)
                  if final_status and final_status.status not in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.EXPIRED, OrderStatus.REJECTED]:
                       print(f"  Attempting cleanup: Canceling order {submitted_order.id}...")
                       brokerage_interface.cancel_order(submitted_order.id)
                       print("  Cancel request submitted.")
                  elif final_status:
                       print(f"  Cleanup not needed: Order status is {final_status.status.value}")
                  else:
                       print(f"  Cleanup check failed: Could not retrieve final status for {submitted_order.id}")

             except BrokerageError as cancel_e:
                  print(f"  Warning: Failed to cancel test order during cleanup: {cancel_e}")


# Add more tests:
# - test_submit_limit_order
# - test_cancel_order (submit limit, then cancel)
# - test_get_order_by_id
# - test error handling (e.g., submitting invalid order)
