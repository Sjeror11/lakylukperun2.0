import uuid
import time
from datetime import datetime, timezone, timedelta # Import timezone and timedelta
from typing import Optional, Dict, Any

from ... import config
from ...utils.logger import log
from ...utils.exceptions import (
    ExecutionServiceError, BrokerageError, InsufficientFundsError,
    OrderValidationError, MarketClosedError, MemoryServiceError
)
from ...models.signal import TradingSignal, SignalAction
from ...models.order import Order, OrderSide, OrderType, OrderTimeInForce, OrderStatus
from ...models.portfolio import Portfolio, Position
from ...models.memory_entry import MemoryEntry, MemoryEntryType
from ...interfaces.brokerage import BrokerageInterface
from ..memory_service.storage import MemoryStorage

# --- Constants ---
EXECUTION_SERVICE_SOURCE = "ExecutionService"

class ExecutionServiceManager:
    """
    Manages trade execution based on incoming signals.
    Handles pre-trade checks, order placement, status monitoring, and portfolio updates.
    """

    def __init__(
        self,
        brokerage_interface: BrokerageInterface,
        memory_storage: MemoryStorage
    ):
        self.brokerage = brokerage_interface
        self.memory = memory_storage
        # Internal state for portfolio - might be updated periodically or on events
        self._current_portfolio: Optional[Portfolio] = None
        self._last_portfolio_update: Optional[datetime] = None
        log.info("ExecutionServiceManager initialized.")
        # Initial portfolio fetch
        self.update_portfolio_state()

    def update_portfolio_state(self) -> Portfolio:
        """Fetches and updates the internal portfolio state."""
        log.debug("Updating internal portfolio state...")
        try:
            self._current_portfolio = self.brokerage.get_account_portfolio()
            self._last_portfolio_update = datetime.now(timezone.utc) # Use timezone-aware datetime
            log.info(f"Portfolio state updated. Equity: {self._current_portfolio.equity}, Cash: {self._current_portfolio.cash}")
            # Save portfolio update to memory
            portfolio_payload = self._current_portfolio.model_dump(mode='json')
            memory_entry = MemoryEntry(
                entry_type=MemoryEntryType.PORTFOLIO_UPDATE,
                source_service=EXECUTION_SERVICE_SOURCE,
                payload=portfolio_payload
            )
            self.memory.save_memory(memory_entry)
            return self._current_portfolio
        except BrokerageError as e:
            log.error(f"Failed to update portfolio state from brokerage: {e}", exc_info=True)
            # Decide how to handle this - use stale data? Raise error?
            if self._current_portfolio:
                 log.warning("Using previously cached portfolio state due to update failure.")
                 return self._current_portfolio
            else:
                 raise ExecutionServiceError("Failed to fetch initial portfolio state.") from e
        except MemoryServiceError as e:
             log.error(f"Failed to save portfolio update to memory: {e}", exc_info=True)
             # Continue even if saving memory fails, but log error
             if self._current_portfolio:
                  return self._current_portfolio
             else: # Should not happen if brokerage call succeeded
                  raise ExecutionServiceError("Failed to fetch initial portfolio state and save update.") from e


    def get_current_portfolio(self, force_refresh: bool = False) -> Portfolio:
        """Returns the current portfolio state, potentially refreshing it."""
        # Add logic for staleness check if needed (e.g., refresh if older than X minutes)
        if force_refresh or not self._current_portfolio:
            return self.update_portfolio_state()
        return self._current_portfolio

    def _calculate_order_qty(self, signal: TradingSignal, portfolio: Portfolio) -> float:
        """Calculates the quantity for an order based on signal and risk parameters."""
        # Basic example: Fixed risk percentage per trade
        if not portfolio.equity or portfolio.equity <= 0:
             raise OrderValidationError("Cannot calculate order quantity: Invalid portfolio equity.")

        risk_amount = portfolio.equity * config.RISK_LIMIT_PERCENT
        log.debug(f"Calculating order quantity: Equity={portfolio.equity}, Risk%={config.RISK_LIMIT_PERCENT}, RiskAmount={risk_amount}")

        # Get current price (requires market data access or recent portfolio update)
        position = portfolio.positions.get(signal.symbol)
        current_price = position.current_price if position and position.current_price else None
        if not current_price:
             # Attempt to get latest price from brokerage if missing
             try:
                  log.warning(f"Current price missing for {signal.symbol} in portfolio cache. Fetching latest.")
                  # This might be slow - consider if AIService should provide price with signal
                  snapshot = self.brokerage.get_latest_market_data([signal.symbol])
                  if snapshot.latest_trades and signal.symbol in snapshot.latest_trades:
                       current_price = snapshot.latest_trades[signal.symbol].price
                  elif snapshot.latest_quotes and signal.symbol in snapshot.latest_quotes:
                       # Use mid-price as fallback
                       quote = snapshot.latest_quotes[signal.symbol]
                       current_price = (quote.ask_price + quote.bid_price) / 2
                  else:
                       raise OrderValidationError(f"Cannot determine current price for {signal.symbol} to calculate quantity.")
             except BrokerageError as e:
                  raise OrderValidationError(f"Failed to fetch current price for {signal.symbol}: {e}") from e

        log.debug(f"Using current price {current_price} for quantity calculation of {signal.symbol}.")

        # Example stop-loss based sizing (adjust based on actual strategy)
        if signal.stop_loss_price:
            price_diff = abs(current_price - signal.stop_loss_price)
            if price_diff <= 0:
                raise OrderValidationError(f"Invalid stop loss for {signal.symbol}: Stop price {signal.stop_loss_price} too close or equal to current price {current_price}.")
            qty = risk_amount / price_diff
            log.debug(f"Calculated quantity based on stop loss {signal.stop_loss_price}: {qty}")
        else:
            # Fallback: Risk amount divided by current price (simpler, less precise risk control)
            qty = risk_amount / current_price
            log.warning(f"No stop loss provided for {signal.symbol}. Using simple price-based quantity calculation: {qty}")

        # Apply position size limits
        max_position_value = config.MAX_POSITION_SIZE
        max_qty_by_value = max_position_value / current_price
        final_qty = min(qty, max_qty_by_value)
        log.debug(f"Applying max position size ({max_position_value}): Max Qty={max_qty_by_value}, Final Qty={final_qty}")

        # TODO: Add rounding logic (e.g., round down to nearest whole share for stocks)
        final_qty = float(int(final_qty)) # Simple integer rounding for now
        log.info(f"Calculated final order quantity for {signal.symbol}: {final_qty}")

        if final_qty <= 0:
             raise OrderValidationError(f"Calculated order quantity is zero or negative for {signal.symbol}.")

        return final_qty


    def _perform_pre_trade_checks(self, order: Order, portfolio: Portfolio):
        """Performs validation checks before submitting an order."""
        log.info(f"Performing pre-trade checks for {order.side} {order.qty} {order.symbol}...")

        # 1. Market Hours Check (already partially handled in submit_order)
        if not self.brokerage.is_market_open() and not order.extended_hours and order.time_in_force != OrderTimeInForce.GTC:
             raise MarketClosedError(f"Market is closed for non-GTC/extended order {order.symbol}.")

        # 2. Buying Power Check (for BUY orders)
        if order.side == OrderSide.BUY:
            estimated_cost = order.qty * (order.limit_price or self.brokerage.get_latest_market_data([order.symbol]).latest_trades[order.symbol].price) # Estimate cost
            # Add buffer for market orders
            if order.type == OrderType.MARKET:
                 estimated_cost *= 1.01 # Add 1% buffer for slippage
            log.debug(f"Estimated cost for BUY {order.symbol}: {estimated_cost}, Available Buying Power: {portfolio.buying_power}")
            if estimated_cost > portfolio.buying_power:
                raise InsufficientFundsError(f"Insufficient buying power for {order.symbol}. Need: {estimated_cost:.2f}, Have: {portfolio.buying_power:.2f}")

        # 3. Sufficient Shares Check (for SELL orders)
        if order.side == OrderSide.SELL:
            position = portfolio.positions.get(order.symbol)
            if not position or position.qty < order.qty:
                 # Allow selling if shorting is enabled (check portfolio status)
                 if not portfolio.shorting_enabled:
                      current_qty = position.qty if position else 0
                      raise OrderValidationError(f"Insufficient shares to sell {order.symbol}. Need: {order.qty}, Have: {current_qty}. Shorting not enabled.")
                 else:
                      log.info(f"Proceeding with SELL order for {order.symbol} as shorting is enabled.")
            else:
                 log.debug(f"Sufficient shares check passed for SELL {order.symbol}. Have: {position.qty}, Need: {order.qty}")


        # 4. Max Total Positions Check
        if order.side == OrderSide.BUY and order.symbol not in portfolio.positions: # Only check for new positions
             if len(portfolio.positions) >= config.MAX_TOTAL_POSITIONS:
                  raise OrderValidationError(f"Cannot open new position in {order.symbol}: Max total positions ({config.MAX_TOTAL_POSITIONS}) reached.")

        # 5. Check Asset Tradability (optional - Alpaca API might handle this)
        # try:
        #     asset = self.brokerage.api.get_asset(order.symbol)
        #     if not asset.tradable:
        #         raise OrderValidationError(f"Asset {order.symbol} is not tradable.")
        #     if asset.shortable is False and order.side == OrderSide.SELL and (order.symbol not in portfolio.positions or portfolio.positions[order.symbol].qty < order.qty):
        #          raise OrderValidationError(f"Asset {order.symbol} is not shortable.")
        # except APIError as e:
        #      log.warning(f"Could not verify asset tradability for {order.symbol}: {e}")


        log.info(f"Pre-trade checks passed for {order.symbol}.")


    def process_signal(self, signal: TradingSignal) -> Optional[Order]:
        """
        Processes a trading signal, performs checks, and submits an order if valid.

        Args:
            signal: The TradingSignal object to process.

        Returns:
            The submitted Order object if successful, None otherwise.
        """
        log.info(f"Processing signal ID {signal.signal_id}: {signal.action.value} {signal.symbol}")
        order_to_submit: Optional[Order] = None
        order_payload: Dict[str, Any] = {"signal_id": signal.signal_id} # For memory entry

        try:
            # 1. Get Current Portfolio State (Refresh only if stale)
            portfolio = None
            # Check if portfolio exists and is recent (e.g., within 5 minutes)
            if self._current_portfolio and self._last_portfolio_update and \
               (datetime.now(timezone.utc) - self._last_portfolio_update) < timedelta(minutes=5):
                portfolio = self._current_portfolio
                log.debug("Using cached portfolio state for signal processing.")
            else:
                log.info("Refreshing portfolio state before processing signal.")
                portfolio = self.update_portfolio_state() # Use update directly to ensure save happens

            # 2. Handle Signal Action (Create Order object)
            if signal.action in [SignalAction.BUY, SignalAction.SELL]:
                # Calculate quantity
                order_qty = self._calculate_order_qty(signal, portfolio)

                # Create Order object
                order_to_submit = Order(
                    client_order_id=f"sys_{uuid.uuid4()}", # Generate unique client ID
                    symbol=signal.symbol,
                    qty=order_qty,
                    side=OrderSide(signal.action.value), # Map SignalAction to OrderSide
                    type=OrderType.MARKET, # Default to market order, adjust based on signal/config
                    time_in_force=OrderTimeInForce.DAY, # Default to DAY, adjust as needed
                    limit_price=signal.target_price, # Use target as limit if provided? Requires LIMIT order type
                    stop_price=signal.stop_loss_price, # Use stop loss if provided? Requires STOP order type
                    # TODO: Refine order type based on signal details (target/stop prices)
                )
                order_payload.update(order_to_submit.model_dump(mode='json'))

                # 3. Perform Pre-Trade Checks
                self._perform_pre_trade_checks(order_to_submit, portfolio)

                # 4. Submit Order
                start_time = time.time()
                submitted_order = self.brokerage.submit_order(order_to_submit)
                end_time = time.time()
                latency = (end_time - start_time) * 1000 # Latency in ms
                order_payload["submission_latency_ms"] = latency
                order_payload["broker_order_id"] = submitted_order.id
                order_payload["status"] = submitted_order.status.value
                log.info(f"Order submission latency for {signal.symbol}: {latency:.2f} ms")

                # Save order submission attempt to memory
                memory_entry = MemoryEntry(
                    entry_type=MemoryEntryType.ORDER_STATUS, # Or a specific TRADE_ATTEMPT type?
                    source_service=EXECUTION_SERVICE_SOURCE,
                    payload=order_payload
                )
                self.memory.save_memory(memory_entry)

                # Return the submitted order (with updated status/ID from brokerage)
                return submitted_order

            elif signal.action in [SignalAction.CLOSE_LONG, SignalAction.CLOSE_SHORT]:
                 # TODO: Implement logic to close existing positions
                 log.warning(f"Position closing logic for action '{signal.action.value}' not yet implemented.")
                 position = portfolio.positions.get(signal.symbol)
                 if not position:
                      log.warning(f"Cannot close position for {signal.symbol}: No position found.")
                      return None
                 # Create SELL order for CLOSE_LONG, BUY order for CLOSE_SHORT
                 # Quantity should be the absolute quantity of the position
                 # Submit the closing order...
                 pass

            elif signal.action == SignalAction.HOLD:
                log.info(f"Signal action is HOLD for {signal.symbol}. No order placed.")
                return None
            else:
                log.warning(f"Unsupported signal action: {signal.action.value}")
                return None

        except (OrderValidationError, InsufficientFundsError, MarketClosedError, BrokerageError) as e:
            log.error(f"Trade execution failed for signal {signal.signal_id} ({signal.symbol}): {e}", exc_info=True)
            # Save error to memory
            error_payload = {
                "signal_id": signal.signal_id,
                "symbol": signal.symbol,
                "action": signal.action.value,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "order_details": order_to_submit.model_dump(mode='json') if order_to_submit else None
            }
            error_entry = MemoryEntry(
                entry_type=MemoryEntryType.ERROR,
                source_service=EXECUTION_SERVICE_SOURCE,
                payload=error_payload
            )
            try:
                self.memory.save_memory(error_entry)
            except MemoryServiceError as mem_err:
                log.error(f"Failed to save execution service error memory entry: {mem_err}")
            return None # Indicate failure
        except Exception as e:
            log.critical(f"Unexpected critical error processing signal {signal.signal_id} ({signal.symbol}): {e}", exc_info=True)
             # Save critical error memory entry
            error_payload = {
                 "signal_id": signal.signal_id,
                 "symbol": signal.symbol,
                 "action": signal.action.value,
                 "error_type": type(e).__name__,
                 "error_message": str(e),
                 "stage": "SignalProcessingCritical",
                 "order_details": order_to_submit.model_dump(mode='json') if order_to_submit else None
            }
            error_entry = MemoryEntry(entry_type=MemoryEntryType.ERROR, source_service=EXECUTION_SERVICE_SOURCE, payload=error_payload)
            try:
                 self.memory.save_memory(error_entry)
            except MemoryServiceError as mem_err:
                 log.error(f"Failed to save execution service critical error memory entry: {mem_err}")
            return None # Indicate failure

    # --- Optional: Add methods for monitoring order status updates via streaming/polling ---
    # def handle_order_update(self, update_data):
    #     """Processes an order status update received from the brokerage (e.g., via stream)."""
    #     # Parse update_data (format depends on Alpaca stream)
    #     # Update internal order status if tracked
    #     # Save ORDER_STATUS memory entry
    #     # Potentially update portfolio state on fills
    #     pass

# Example Usage (Requires setting up interfaces and storage)
# if __name__ == '__main__':
#      print("Testing ExecutionServiceManager...")
#      # Requires mocking or initializing:
#      # - config
#      # - BrokerageInterface
#      # - MemoryStorage

#      from unittest.mock import MagicMock
#      mock_brokerage = MagicMock(spec=BrokerageInterface)
#      mock_storage = MagicMock(spec=MemoryStorage)

#      # --- Mock Brokerage Setup ---
#      # Mock portfolio
#      mock_position = Position(symbol="TEST", qty=10, avg_entry_price=100, cost_basis=1000, current_price=105)
#      mock_portfolio = Portfolio(account_id="paper_acc", cash=5000, equity=6050, buying_power=10000, portfolio_value=6050, positions={"TEST": mock_position}, shorting_enabled=True)
#      mock_brokerage.get_account_portfolio.return_value = mock_portfolio
#      mock_brokerage.is_market_open.return_value = True
#      # Mock order submission
#      def mock_submit(order_data: Order):
#           order_data.id = f"brkr_{uuid.uuid4()}"
#           order_data.status = OrderStatus.ACCEPTED # Simulate acceptance
#           order_data.submitted_at = datetime.utcnow()
#           return order_data
#      mock_brokerage.submit_order.side_effect = mock_submit
#      # Mock latest data for quantity calc fallback
#      mock_trade = Trade(symbol="NEW", timestamp=datetime.utcnow(), price=50.0, size=1)
#      mock_snapshot = MarketDataSnapshot(latest_trades={"NEW": mock_trade})
#      mock_brokerage.get_latest_market_data.return_value = mock_snapshot
#      # --- End Mock Setup ---


#      try:
#           exec_service = ExecutionServiceManager(mock_brokerage, mock_storage)
#           print("Execution Service Initialized.")

#           # Test BUY signal
#           buy_signal = TradingSignal(
#                signal_id=f"sig_{uuid.uuid4()}",
#                symbol="NEW", # A new symbol not in portfolio
#                action=SignalAction.BUY,
#                confidence=0.8,
#                stop_loss_price=45.0 # For quantity calculation
#           )
#           print("\nProcessing BUY Signal...")
#           submitted_buy_order = exec_service.process_signal(buy_signal)
#           if submitted_buy_order:
#                print("Submitted BUY Order:")
#                print(submitted_buy_order.model_dump_json(indent=2))
#                mock_brokerage.submit_order.assert_called_once()
#                mock_storage.save_memory.assert_called() # Should be called for portfolio update and order status
#           else:
#                print("BUY order submission failed pre-checks or execution.")

#           mock_brokerage.submit_order.reset_mock()
#           mock_storage.save_memory.reset_mock()

#           # Test SELL signal (existing position)
#           sell_signal = TradingSignal(
#                signal_id=f"sig_{uuid.uuid4()}",
#                symbol="TEST", # Existing position
#                action=SignalAction.SELL,
#                confidence=0.7
#           )
#           print("\nProcessing SELL Signal (Existing Position)...")
#           # Need to recalculate qty based on risk for sell, or just sell fixed amount/all?
#           # Let's assume _calculate_order_qty handles sell sizing appropriately (e.g., based on risk % of position value)
#           # For simplicity here, let's assume it calculates qty=5
#           # We need to mock _calculate_order_qty or make it simpler for this test
#           exec_service._calculate_order_qty = MagicMock(return_value=5.0) # Mock calculation

#           submitted_sell_order = exec_service.process_signal(sell_signal)
#           if submitted_sell_order:
#                print("Submitted SELL Order:")
#                print(submitted_sell_order.model_dump_json(indent=2))
#                mock_brokerage.submit_order.assert_called_once()
#           else:
#                print("SELL order submission failed.")


#           # Test Insufficient Funds
#           buy_signal_large = TradingSignal(
#                signal_id=f"sig_{uuid.uuid4()}",
#                symbol="EXPENSIVE",
#                action=SignalAction.BUY,
#                confidence=0.9
#           )
#           # Mock price and qty calculation to exceed buying power
#           mock_trade_exp = Trade(symbol="EXPENSIVE", timestamp=datetime.utcnow(), price=10000.0, size=1)
#           mock_snapshot_exp = MarketDataSnapshot(latest_trades={"EXPENSIVE": mock_trade_exp})
#           mock_brokerage.get_latest_market_data.return_value = mock_snapshot_exp
#           exec_service._calculate_order_qty = MagicMock(return_value=2.0) # 2 * 10000 > 10000 buying power
#           print("\nProcessing BUY Signal (Insufficient Funds)...")
#           should_be_none = exec_service.process_signal(buy_signal_large)
#           print(f"Result (should be None): {should_be_none}")
#           # Check if error was logged to memory
#           # print(mock_storage.save_memory.call_args_list) # Check calls


#      except Exception as e:
#           print(f"\nError during Execution Service test: {e}")
