import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError, TimeFrame, TimeFrameUnit
from alpaca_trade_api.stream import Stream
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd # Alpaca API often returns pandas DataFrames

from .. import config
from ..utils.logger import log
from ..utils.exceptions import BrokerageError, ConfigError, MarketClosedError
from ..models.order import Order, OrderStatus, OrderSide, OrderType, OrderTimeInForce # Import necessary models
from ..models.portfolio import Portfolio, Position # Import necessary models
from ..models.market_data import Bar, Quote, Trade, MarketDataSnapshot, BarTimeframe # Import necessary models

# Mapping from internal timeframe enum to Alpaca's TimeFrame
TIMEFRAME_MAP = {
    BarTimeframe.MINUTE: TimeFrame.Minute,
    BarTimeframe.FIVE_MINUTE: TimeFrame(5, TimeFrameUnit.Minute),
    BarTimeframe.FIFTEEN_MINUTE: TimeFrame(15, TimeFrameUnit.Minute),
    BarTimeframe.THIRTY_MINUTE: TimeFrame(30, TimeFrameUnit.Minute),
    BarTimeframe.HOUR: TimeFrame.Hour,
    BarTimeframe.DAY: TimeFrame.Day,
    # AlpacaPy might handle Week/Month differently or require adjustments
    # BarTimeframe.WEEK: TimeFrame.Week,
    # BarTimeframe.MONTH: TimeFrame.Month,
}


class BrokerageInterface:
    """
    Interface for interacting with the Alpaca brokerage API.
    Handles authentication, data retrieval, order placement, and error handling.
    """

    def __init__(self):
        log.info("Initializing BrokerageInterface...")
        try:
            self.api = tradeapi.REST(
                key_id=config.ALPACA_API_KEY,
                secret_key=config.ALPACA_SECRET_KEY,
                base_url=config.ALPACA_BASE_URL,
                api_version='v2'
            )
            # Check connection by fetching account info
            account_info = self.api.get_account()
            log.info(f"Successfully connected to Alpaca. Account ID: {account_info.id}, Status: {account_info.status}")
            self._check_account_status(account_info)

            # Initialize data client (Alpaca uses separate clients for trading and data)
            # Note: Data API keys might be the same or different depending on Alpaca setup
            self.data_api = tradeapi.REST(
                 key_id=config.ALPACA_API_KEY,
                 secret_key=config.ALPACA_SECRET_KEY,
                 base_url=config.ALPACA_BASE_URL # Data API might have a different URL in some Alpaca setups, adjust if needed
            )
            # Consider initializing the Alpaca MarketDataStreamClient for real-time data if needed
            # self.stream = Stream(...)

        except APIError as e:
            log.error(f"Alpaca API Error during initialization: {e}", exc_info=True)
            raise BrokerageError(f"Failed to connect to Alpaca: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error during BrokerageInterface initialization: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error initializing Alpaca connection: {e}") from e

    def _check_account_status(self, account_info):
        """Checks if the Alpaca account status is ACTIVE."""
        if account_info.status != 'ACTIVE':
            log.error(f"Alpaca account status is not ACTIVE: {account_info.status}. Trading may be disabled.")
            # Depending on severity, you might raise an error or just warn
            raise BrokerageError(f"Alpaca account status is not ACTIVE: {account_info.status}")
        if account_info.trading_blocked:
            log.error("Trading is blocked for the Alpaca account.")
            raise BrokerageError("Trading is blocked for the Alpaca account.")
        if account_info.account_blocked:
            log.error("The Alpaca account is blocked.")
            raise BrokerageError("The Alpaca account is blocked.")

    def is_market_open(self) -> bool:
        """Checks if the market is currently open."""
        try:
            clock = self.api.get_clock()
            if not clock.is_open:
                 log.debug(f"Market is closed. Next open: {clock.next_open}, Next close: {clock.next_close}")
                 return False
            log.debug(f"Market is open. Current time: {clock.timestamp}")
            return True
        except APIError as e:
            log.error(f"Alpaca API Error checking market clock: {e}", exc_info=True)
            raise BrokerageError(f"Failed to get market clock: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error checking market status: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error checking market status: {e}") from e

    def get_account_portfolio(self) -> Portfolio:
        """Retrieves the current account and portfolio status."""
        try:
            account_info = self.api.get_account()
            self._check_account_status(account_info) # Re-check status
            positions_raw = self.api.list_positions()

            portfolio_positions = {}
            for pos_raw in positions_raw:
                try:
                    position = Position(
                        symbol=pos_raw.symbol,
                        qty=float(pos_raw.qty),
                        avg_entry_price=float(pos_raw.avg_entry_price),
                        current_price=float(pos_raw.current_price) if pos_raw.current_price else None,
                        market_value=float(pos_raw.market_value) if pos_raw.market_value else None,
                        unrealized_pl=float(pos_raw.unrealized_pl) if pos_raw.unrealized_pl else None,
                        unrealized_plpc=float(pos_raw.unrealized_plpc) if pos_raw.unrealized_plpc else None,
                        cost_basis=float(pos_raw.cost_basis) if pos_raw.cost_basis else None,
                        last_day_price=float(pos_raw.lastday_price) if pos_raw.lastday_price else None,
                        change_today=float(pos_raw.change_today) if pos_raw.change_today else None,
                    )
                    portfolio_positions[position.symbol] = position
                except Exception as pe:
                     log.error(f"Error processing position data for {pos_raw.symbol}: {pe}", exc_info=True)
                     # Decide whether to skip this position or raise an error

            portfolio = Portfolio(
                account_id=account_info.id,
                cash=float(account_info.cash),
                equity=float(account_info.equity),
                buying_power=float(account_info.buying_power),
                positions=portfolio_positions,
                initial_margin=float(account_info.initial_margin) if account_info.initial_margin else None,
                maintenance_margin=float(account_info.maintenance_margin) if account_info.maintenance_margin else None,
                portfolio_value=float(account_info.portfolio_value), # Use Alpaca's value
                daytrade_count=int(account_info.daytrade_count) if account_info.daytrade_count else None,
                is_account_blocked=bool(account_info.account_blocked),
                is_trading_blocked=bool(account_info.trading_blocked),
                regt_buying_power=float(account_info.regt_buying_power) if account_info.regt_buying_power else None,
                shorting_enabled=bool(account_info.shorting_enabled),
                currency=account_info.currency
            )
            log.debug(f"Retrieved portfolio: Equity={portfolio.equity}, Cash={portfolio.cash}, Positions={len(portfolio.positions)}")
            return portfolio

        except APIError as e:
            log.error(f"Alpaca API Error getting account/portfolio: {e}", exc_info=True)
            raise BrokerageError(f"Failed to get account/portfolio: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error getting account/portfolio: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error getting account/portfolio: {e}") from e

    def get_bars(self, symbols: List[str], timeframe: BarTimeframe, start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None, limit: Optional[int] = 100) -> Dict[str, List[Bar]]:
        """
        Retrieves historical bar data for multiple symbols.
        Note: Alpaca's free tier has limitations on historical data depth.
        """
        if not symbols:
            return {}

        alpaca_timeframe = TIMEFRAME_MAP.get(timeframe)
        if not alpaca_timeframe:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Format dates for Alpaca API (ISO 8601)
        start_iso = start_dt.isoformat() if start_dt else None
        end_iso = end_dt.isoformat() if end_dt else None

        try:
            # Use Alpaca's get_bars method
            bar_data_raw = self.data_api.get_bars(
                symbol_or_symbols=symbols,
                timeframe=alpaca_timeframe,
                start=start_iso,
                end=end_iso,
                limit=limit,
                adjustment='raw' # Or 'split', 'dividend', 'all'
            )

            result: Dict[str, List[Bar]] = {symbol: [] for symbol in symbols}
            if isinstance(bar_data_raw, dict): # Multi-symbol request returns dict
                 for symbol, bars in bar_data_raw.items():
                     for bar_raw in bars:
                         try:
                             bar = Bar(
                                 symbol=symbol, # Use the key from the dict
                                 timestamp=bar_raw.t.to_pydatetime(), # Convert pandas timestamp
                                 open=float(bar_raw.o),
                                 high=float(bar_raw.h),
                                 low=float(bar_raw.l),
                                 close=float(bar_raw.c),
                                 volume=float(bar_raw.v),
                                 trade_count=int(bar_raw.n) if hasattr(bar_raw, 'n') and bar_raw.n is not None else None,
                                 vwap=float(bar_raw.vw) if hasattr(bar_raw, 'vw') and bar_raw.vw is not None else None,
                             )
                             result[symbol].append(bar)
                         except Exception as pe:
                             log.error(f"Error processing bar data for {symbol} at {bar_raw.t}: {pe}", exc_info=True)
            elif isinstance(bar_data_raw, list): # Single symbol request might return list
                 symbol = symbols[0]
                 for bar_raw in bar_data_raw:
                      try:
                           bar = Bar(
                               symbol=symbol,
                               timestamp=bar_raw.t.to_pydatetime(),
                               open=float(bar_raw.o),
                               high=float(bar_raw.h),
                               low=float(bar_raw.l),
                               close=float(bar_raw.c),
                               volume=float(bar_raw.v),
                               trade_count=int(bar_raw.n) if hasattr(bar_raw, 'n') and bar_raw.n is not None else None,
                               vwap=float(bar_raw.vw) if hasattr(bar_raw, 'vw') and bar_raw.vw is not None else None,
                           )
                           result[symbol].append(bar)
                      except Exception as pe:
                           log.error(f"Error processing bar data for {symbol} at {bar_raw.t}: {pe}", exc_info=True)


            log.debug(f"Retrieved {sum(len(v) for v in result.values())} bars for {len(symbols)} symbols.")
            return result

        except APIError as e:
            log.error(f"Alpaca API Error getting bars for {symbols}: {e}", exc_info=True)
            raise BrokerageError(f"Failed to get bars: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error getting bars for {symbols}: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error getting bars: {e}") from e

    def get_latest_market_data(self, symbols: List[str]) -> MarketDataSnapshot:
        """Retrieves the latest quote and trade for multiple symbols."""
        if not symbols:
            return MarketDataSnapshot()
        try:
            # Note: AlpacaPy v2 might have different methods or require separate calls
            latest_quotes_raw = self.data_api.get_latest_quotes(symbols)
            latest_trades_raw = self.data_api.get_latest_trades(symbols)

            snapshot = MarketDataSnapshot()
            snapshot.latest_quotes = {}
            snapshot.latest_trades = {}

            for symbol in symbols:
                # Process Quote
                quote_raw = latest_quotes_raw.get(symbol)
                if quote_raw:
                    try:
                        quote = Quote(
                            symbol=symbol,
                            timestamp=quote_raw.t.to_pydatetime(),
                            ask_exchange=quote_raw.ax,
                            ask_price=float(quote_raw.ap),
                            ask_size=float(quote_raw.as_), # Note the underscore for 'as' if it conflicts
                            bid_exchange=quote_raw.bx,
                            bid_price=float(quote_raw.bp),
                            bid_size=float(quote_raw.bs),
                            conditions=quote_raw.c,
                            tape=quote_raw.z
                        )
                        snapshot.latest_quotes[symbol] = quote
                    except Exception as qe:
                         log.error(f"Error processing latest quote for {symbol}: {qe}", exc_info=True)

                # Process Trade
                trade_raw = latest_trades_raw.get(symbol)
                if trade_raw:
                     try:
                          trade = Trade(
                               symbol=symbol,
                               timestamp=trade_raw.t.to_pydatetime(),
                               exchange=trade_raw.x,
                               price=float(trade_raw.p),
                               size=float(trade_raw.s),
                               id=trade_raw.i,
                               conditions=trade_raw.c,
                               tape=trade_raw.z
                          )
                          snapshot.latest_trades[symbol] = trade
                     except Exception as te:
                          log.error(f"Error processing latest trade for {symbol}: {te}", exc_info=True)


            log.debug(f"Retrieved latest market data snapshot for {len(symbols)} symbols.")
            return snapshot

        except APIError as e:
            log.error(f"Alpaca API Error getting latest data for {symbols}: {e}", exc_info=True)
            raise BrokerageError(f"Failed to get latest market data: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error getting latest data for {symbols}: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error getting latest market data: {e}") from e


    def submit_order(self, order_data: Order) -> Order:
        """Submits an order to the brokerage."""
        if not self.is_market_open() and not order_data.extended_hours:
             # Allow GTC orders outside market hours, but log warning
             if order_data.time_in_force != OrderTimeInForce.GTC:
                  log.warning(f"Attempting to place non-GTC order for {order_data.symbol} while market is closed.")
                  # raise MarketClosedError(f"Cannot place non-GTC order for {order_data.symbol} - market is closed.")
             else:
                  log.info(f"Placing GTC order for {order_data.symbol} outside market hours.")


        log.info(f"Submitting order: {order_data.side} {order_data.qty} {order_data.symbol} @ {order_data.type}")
        try:
            # Map internal Order model to Alpaca API parameters
            alpaca_order = self.api.submit_order(
                symbol=order_data.symbol,
                qty=order_data.qty,
                side=order_data.side.value,
                type=order_data.type.value,
                time_in_force=order_data.time_in_force.value,
                limit_price=order_data.limit_price,
                stop_price=order_data.stop_price,
                client_order_id=order_data.client_order_id,
                extended_hours=order_data.extended_hours,
                trail_price=order_data.trail_price,
                trail_percent=order_data.trail_percent,
                # Add other parameters as needed (order_class, take_profit, stop_loss)
            )

            # Update the order object with brokerage-assigned ID and status
            order_data.id = alpaca_order.id
            order_data.status = OrderStatus(alpaca_order.status) # Convert string status to enum
            order_data.submitted_at = alpaca_order.submitted_at.to_pydatetime() if alpaca_order.submitted_at else datetime.utcnow() # Use current time if not provided
            log.info(f"Order submitted successfully for {order_data.symbol}. Broker Order ID: {order_data.id}, Status: {order_data.status.value}")
            return order_data

        except APIError as e:
            # Handle specific errors like insufficient funds, invalid order, etc.
            log.error(f"Alpaca API Error submitting order for {order_data.symbol}: {e}", exc_info=True)
            order_data.status = OrderStatus.REJECTED # Mark as rejected
            order_data.failed_at = datetime.utcnow()
            # You might want to parse the error message for more specific reasons
            raise BrokerageError(f"Failed to submit order for {order_data.symbol}: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error submitting order for {order_data.symbol}: {e}", exc_info=True)
            order_data.status = OrderStatus.REJECTED # Mark as rejected
            order_data.failed_at = datetime.utcnow()
            raise BrokerageError(f"Unexpected error submitting order for {order_data.symbol}: {e}") from e

    def get_order_by_client_id(self, client_order_id: str) -> Optional[Order]:
        """Retrieves an order by its client_order_id."""
        log.debug(f"Getting order by client ID: {client_order_id}")
        try:
            alpaca_order = self.api.get_order_by_client_order_id(client_order_id)
            if alpaca_order:
                order = self._map_alpaca_order_to_model(alpaca_order)
                log.debug(f"Found order {order.id} (Client ID: {client_order_id}), Status: {order.status.value}")
                return order
            else:
                log.warning(f"Order with client ID {client_order_id} not found.")
                return None
        except APIError as e:
            # Alpaca might return 404 if not found, handle this gracefully
            if e.code == 404:
                log.warning(f"Order with client ID {client_order_id} not found (API 404).")
                return None
            log.error(f"Alpaca API Error getting order by client ID {client_order_id}: {e}", exc_info=True)
            raise BrokerageError(f"Failed to get order by client ID {client_order_id}: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error getting order by client ID {client_order_id}: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error getting order by client ID {client_order_id}: {e}") from e

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Retrieves an order by its brokerage-assigned ID."""
        log.debug(f"Getting order by ID: {order_id}")
        try:
            alpaca_order = self.api.get_order(order_id)
            order = self._map_alpaca_order_to_model(alpaca_order)
            log.debug(f"Found order {order.id}, Status: {order.status.value}")
            return order
        except APIError as e:
            if e.code == 404:
                log.warning(f"Order with ID {order_id} not found (API 404).")
                return None
            log.error(f"Alpaca API Error getting order ID {order_id}: {e}", exc_info=True)
            raise BrokerageError(f"Failed to get order ID {order_id}: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error getting order ID {order_id}: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error getting order ID {order_id}: {e}") from e

    def list_orders(self, status: Optional[str] = 'open', limit: int = 50, after: Optional[datetime] = None, until: Optional[datetime] = None, direction: str = 'desc', nested: bool = False) -> List[Order]:
        """Lists orders based on specified filters."""
        log.debug(f"Listing orders with status: {status}, limit: {limit}")
        try:
            # Convert Optional[datetime] to Optional[str] in ISO format
            after_iso = after.isoformat() if after else None
            until_iso = until.isoformat() if until else None

            alpaca_orders = self.api.list_orders(
                status=status, # 'open', 'closed', 'all'
                limit=limit,
                after=after_iso,
                until=until_iso,
                direction=direction,
                nested=nested # Set True to include nested legs for complex orders
            )
            orders = [self._map_alpaca_order_to_model(o) for o in alpaca_orders]
            log.debug(f"Retrieved {len(orders)} orders.")
            return orders
        except APIError as e:
            log.error(f"Alpaca API Error listing orders: {e}", exc_info=True)
            raise BrokerageError(f"Failed to list orders: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error listing orders: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error listing orders: {e}") from e

    def cancel_order(self, order_id: str) -> bool:
        """Cancels an open order by its brokerage-assigned ID."""
        log.info(f"Attempting to cancel order ID: {order_id}")
        try:
            # Check if order exists and is cancelable first
            order = self.get_order_by_id(order_id)
            if not order:
                log.warning(f"Cannot cancel order {order_id}: Order not found.")
                return False # Or raise error?
            if order.status not in [OrderStatus.NEW, OrderStatus.ACCEPTED, OrderStatus.PENDING_NEW, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING_REPLACE, OrderStatus.PENDING_CANCEL]:
                 log.warning(f"Cannot cancel order {order_id}: Status is '{order.status.value}', not cancelable.")
                 return False # Order is already final or pending cancellation

            self.api.cancel_order(order_id)
            log.info(f"Cancel request submitted for order ID: {order_id}")
            # Note: Cancellation might not be immediate. Status might become PENDING_CANCEL first.
            return True
        except APIError as e:
            # Handle cases where order is already filled/canceled
            if e.code == 404:
                 log.warning(f"Cannot cancel order {order_id}: Order not found (API 404).")
                 return False
            if e.code == 422: # Unprocessable Entity - often means order cannot be canceled
                 log.warning(f"Cannot cancel order {order_id}: Order likely already filled or canceled (API 422 - {e}).")
                 # Check status again to confirm
                 current_order = self.get_order_by_id(order_id)
                 if current_order and current_order.status not in [OrderStatus.NEW, OrderStatus.ACCEPTED, OrderStatus.PENDING_NEW, OrderStatus.PARTIALLY_FILLED]:
                      log.info(f"Order {order_id} confirmed as non-cancelable (status: {current_order.status.value}).")
                      return False # Consider it non-cancelable
                 else: # If status is still potentially cancelable, re-raise
                      log.error(f"Alpaca API Error (422) canceling order {order_id}, but status seems cancelable: {e}", exc_info=True)
                      raise BrokerageError(f"Failed to cancel order {order_id}: {e}") from e
            else:
                 log.error(f"Alpaca API Error canceling order {order_id}: {e}", exc_info=True)
                 raise BrokerageError(f"Failed to cancel order {order_id}: {e}") from e
        except Exception as e:
            log.error(f"Unexpected error canceling order {order_id}: {e}", exc_info=True)
            raise BrokerageError(f"Unexpected error canceling order {order_id}: {e}") from e

    def _map_alpaca_order_to_model(self, alpaca_order) -> Order:
        """Helper function to map an Alpaca order object to the internal Order model."""
        # Helper to safely convert Alpaca timestamps (which might be None or NaT)
        def safe_to_pydatetime(ts):
            if ts is pd.NaT or ts is None:
                return None
            # Alpaca timestamps are typically timezone-aware (UTC)
            return ts.to_pydatetime()

        # Map legs recursively if they exist
        legs = None
        if hasattr(alpaca_order, 'legs') and alpaca_order.legs:
            legs = [self._map_alpaca_order_to_model(leg) for leg in alpaca_order.legs]

        return Order(
            id=alpaca_order.id,
            client_order_id=alpaca_order.client_order_id,
            symbol=alpaca_order.symbol,
            qty=float(alpaca_order.qty),
            side=OrderSide(alpaca_order.side),
            type=OrderType(alpaca_order.type),
            time_in_force=OrderTimeInForce(alpaca_order.time_in_force),
            limit_price=float(alpaca_order.limit_price) if alpaca_order.limit_price is not None else None,
            stop_price=float(alpaca_order.stop_price) if alpaca_order.stop_price is not None else None,
            trail_price=float(alpaca_order.trail_price) if alpaca_order.trail_price is not None else None,
            trail_percent=float(alpaca_order.trail_percent) if alpaca_order.trail_percent is not None else None,
            extended_hours=bool(alpaca_order.extended_hours),
            status=OrderStatus(alpaca_order.status),
            created_at=safe_to_pydatetime(alpaca_order.created_at),
            submitted_at=safe_to_pydatetime(alpaca_order.submitted_at),
            filled_at=safe_to_pydatetime(alpaca_order.filled_at),
            expired_at=safe_to_pydatetime(alpaca_order.expired_at),
            canceled_at=safe_to_pydatetime(alpaca_order.canceled_at),
            failed_at=safe_to_pydatetime(alpaca_order.failed_at),
            replaced_at=safe_to_pydatetime(alpaca_order.replaced_at),
            filled_qty=float(alpaca_order.filled_qty),
            filled_avg_price=float(alpaca_order.filled_avg_price) if alpaca_order.filled_avg_price is not None else None,
            legs=legs,
            commission=float(alpaca_order.commission) if hasattr(alpaca_order, 'commission') and alpaca_order.commission is not None else None,
            notes=alpaca_order.notes if hasattr(alpaca_order, 'notes') else None,
        )

    # --- Optional: Add methods for streaming data ---
    # def start_data_stream(self, symbols: List[str], handler_callback):
    #     """Starts listening to real-time market data streams."""
    #     # Implementation using alpaca_trade_api.stream.Stream
    #     pass

    # def stop_data_stream(self):
    #     """Stops the market data stream."""
    #     pass

# Example Usage (can be removed or moved to tests)
# if __name__ == '__main__':
#     try:
#         broker = BrokerageInterface()
#         print(f"Market Open: {broker.is_market_open()}")
#         portfolio = broker.get_account_portfolio()
#         print("\nPortfolio:")
#         print(portfolio.model_dump_json(indent=2))

#         # Example: Get bars
#         bars = broker.get_bars(['AAPL', 'MSFT'], timeframe=BarTimeframe.DAY, limit=5)
#         print("\nRecent Bars (AAPL):")
#         if bars.get('AAPL'):
#             for bar in bars['AAPL']:
#                 print(bar.model_dump_json())

#         # Example: Get latest data
#         snapshot = broker.get_latest_market_data(['AAPL', 'TSLA'])
#         print("\nLatest Snapshot:")
#         print(snapshot.model_dump_json(indent=2))

#         # Example: Place an order (Use with caution, especially with live keys!)
#         if config.IS_PAPER_TRADING:
#              from uuid import uuid4
#              test_order_data = Order(
#                  client_order_id=f"test-{uuid4()}",
#                  symbol="AAPL",
#                  qty=1, # Small quantity for testing
#                  side=OrderSide.BUY,
#                  type=OrderType.MARKET,
#                  time_in_force=OrderTimeInForce.DAY
#              )
#              try:
#                  submitted_order = broker.submit_order(test_order_data)
#                  print("\nSubmitted Test Order:")
#                  print(submitted_order.model_dump_json(indent=2))

#                  # Example: Get order status
#                  time.sleep(2) # Allow time for status update
#                  retrieved_order = broker.get_order_by_id(submitted_order.id)
#                  if retrieved_order:
#                      print("\nRetrieved Order Status:")
#                      print(retrieved_order.model_dump_json(indent=2))

#                  # Example: Cancel order
#                  # canceled = broker.cancel_order(submitted_order.id)
#                  # print(f"\nOrder Cancel Attempted: {canceled}")

#              except BrokerageError as order_err:
#                  print(f"\nError placing/managing test order: {order_err}")
#         else:
#              print("\nSkipping order placement example (not paper trading).")


#         # Example: List open orders
#         open_orders = broker.list_orders(status='open')
#         print(f"\nOpen Orders ({len(open_orders)}):")
#         # for o in open_orders:
#         #     print(o.model_dump_json(indent=2))


#     except BrokerageError as be:
#         print(f"Brokerage Error: {be}")
#     except ConfigError as ce:
#         print(f"Configuration Error: {ce}")
#     except Exception as ex:
#         print(f"An unexpected error occurred: {ex}")
