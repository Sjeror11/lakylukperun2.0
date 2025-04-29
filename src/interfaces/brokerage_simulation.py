"""
Simulation mode for BrokerageInterface.
This module provides a simulated implementation of the BrokerageInterface class.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import pandas as pd
import uuid

from .. import config
from ..utils.logger import log
from ..utils.exceptions import BrokerageError, ConfigError, MarketClosedError
from ..models.order import Order, OrderStatus, OrderSide, OrderType, OrderTimeInForce
from ..models.portfolio import Portfolio, Position
from ..models.market_data import Bar, Quote, Trade, MarketDataSnapshot, BarTimeframe

class SimulatedBrokerageInterface:
    """
    Simulated implementation of the BrokerageInterface class.
    Provides simulated market data and trading functionality without requiring API keys.
    """

    def __init__(self):
        log.info("Initializing SimulatedBrokerageInterface...")
        
        # Create simulated account info
        self.simulated_account = {
            'id': 'SIM123456',
            'status': 'ACTIVE',
            'currency': 'USD',
            'cash': 100000.0,  # $100k starting cash
            'portfolio_value': 100000.0,
            'equity': 100000.0,
            'buying_power': 200000.0,  # 2x leverage
            'initial_margin': 0.0,
            'maintenance_margin': 0.0,
            'daytrade_count': 0,
            'trading_blocked': False,
            'account_blocked': False,
            'shorting_enabled': True,
            'regt_buying_power': 100000.0,
        }
        
        # Simulated positions
        self.simulated_positions = {}
        
        # Simulated orders
        self.simulated_orders = {}
        
        # Simulated market data
        self.simulated_market_data = self._initialize_simulated_market_data()
        
        # Simulated market status (open/closed)
        self.simulated_market_open = True
        
        log.info(f"Simulation initialized with ${self.simulated_account['cash']} cash")
    
    def _initialize_simulated_market_data(self):
        """Initialize simulated market data for default symbols."""
        symbols = config.DEFAULT_SYMBOLS.split(',')
        market_data = {}
        
        for symbol in symbols:
            # Generate a random base price between $10 and $500
            base_price = random.uniform(10.0, 500.0)
            market_data[symbol] = {
                'current_price': base_price,
                'last_updated': datetime.now(),
                'daily_high': base_price * 1.02,  # 2% higher than base
                'daily_low': base_price * 0.98,   # 2% lower than base
                'daily_open': base_price * 0.99,  # Slightly lower than current
                'volume': random.randint(100000, 10000000),
                'bars': self._generate_simulated_bars(symbol, base_price, 100)  # Generate 100 historical bars
            }
        
        return market_data
    
    def _generate_simulated_bars(self, symbol, base_price, count):
        """Generate simulated historical bars for a symbol."""
        bars = []
        current_price = base_price
        end_time = datetime.now()
        
        for i in range(count):
            # Move back in time
            bar_time = end_time - timedelta(days=count-i)
            # Random price movement (-2% to +2%)
            price_change = random.uniform(-0.02, 0.02)
            current_price = current_price * (1 + price_change)
            
            # Create a bar
            open_price = current_price * (1 + random.uniform(-0.005, 0.005))
            high_price = max(open_price, current_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, current_price) * (1 - random.uniform(0, 0.01))
            
            bar = Bar(
                symbol=symbol,
                timestamp=bar_time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=current_price,
                volume=random.randint(10000, 1000000),
                trade_count=random.randint(100, 10000),
                vwap=(open_price + high_price + low_price + current_price) / 4
            )
            bars.append(bar)
        
        return bars
    
    def _update_simulated_prices(self):
        """Update simulated prices with random movements."""
        for symbol, data in self.simulated_market_data.items():
            # Random price movement (-1% to +1%)
            price_change = random.uniform(-0.01, 0.01)
            new_price = data['current_price'] * (1 + price_change)
            
            # Update market data
            data['current_price'] = new_price
            data['last_updated'] = datetime.now()
            data['daily_high'] = max(data['daily_high'], new_price)
            data['daily_low'] = min(data['daily_low'], new_price)
            
            # Add a new bar
            bar_time = datetime.now()
            open_price = data['current_price'] * (1 + random.uniform(-0.005, 0.005))
            high_price = max(open_price, new_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, new_price) * (1 - random.uniform(0, 0.01))
            
            bar = Bar(
                symbol=symbol,
                timestamp=bar_time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=new_price,
                volume=random.randint(10000, 1000000),
                trade_count=random.randint(100, 10000),
                vwap=(open_price + high_price + low_price + new_price) / 4
            )
            data['bars'].append(bar)
            
            # Keep only the last 100 bars
            if len(data['bars']) > 100:
                data['bars'] = data['bars'][-100:]
    
    def is_market_open(self) -> bool:
        """Checks if the market is currently open."""
        # In simulation mode, we can control market hours
        # For simplicity, let's say market is always open
        return self.simulated_market_open
    
    def get_account_portfolio(self) -> Portfolio:
        """Retrieves the current account and portfolio status."""
        # Update prices before returning portfolio
        self._update_simulated_prices()
        
        # In simulation mode, return our simulated portfolio
        portfolio_positions = {}
        for symbol, position_data in self.simulated_positions.items():
            position = Position(
                symbol=symbol,
                qty=position_data['qty'],
                avg_entry_price=position_data['avg_entry_price'],
                current_price=self.simulated_market_data[symbol]['current_price'],
                market_value=position_data['qty'] * self.simulated_market_data[symbol]['current_price'],
                unrealized_pl=(self.simulated_market_data[symbol]['current_price'] - position_data['avg_entry_price']) * position_data['qty'],
                unrealized_plpc=(self.simulated_market_data[symbol]['current_price'] / position_data['avg_entry_price']) - 1.0 if position_data['avg_entry_price'] > 0 else 0.0,
                cost_basis=position_data['qty'] * position_data['avg_entry_price'],
                last_day_price=self.simulated_market_data[symbol]['daily_open'],
                change_today=(self.simulated_market_data[symbol]['current_price'] / self.simulated_market_data[symbol]['daily_open']) - 1.0,
            )
            portfolio_positions[symbol] = position
        
        # Calculate total portfolio value (cash + positions)
        total_position_value = sum(pos.market_value for pos in portfolio_positions.values())
        portfolio_value = self.simulated_account['cash'] + total_position_value
        
        portfolio = Portfolio(
            account_id=self.simulated_account['id'],
            cash=self.simulated_account['cash'],
            equity=portfolio_value,
            buying_power=self.simulated_account['buying_power'],
            positions=portfolio_positions,
            initial_margin=self.simulated_account['initial_margin'],
            maintenance_margin=self.simulated_account['maintenance_margin'],
            portfolio_value=portfolio_value,
            daytrade_count=self.simulated_account['daytrade_count'],
            is_account_blocked=self.simulated_account['account_blocked'],
            is_trading_blocked=self.simulated_account['trading_blocked'],
            regt_buying_power=self.simulated_account['regt_buying_power'],
            shorting_enabled=self.simulated_account['shorting_enabled'],
            currency=self.simulated_account['currency']
        )
        log.debug(f"Retrieved simulated portfolio: Equity={portfolio.equity}, Cash={portfolio.cash}, Positions={len(portfolio.positions)}")
        return portfolio
    
    def get_bars(self, symbols: List[str], timeframe: BarTimeframe, start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None, limit: Optional[int] = 100) -> Dict[str, List[Bar]]:
        """Retrieves historical bar data for multiple symbols."""
        if not symbols:
            return {}
        
        # Update prices before returning bars
        self._update_simulated_prices()
        
        result = {}
        for symbol in symbols:
            if symbol in self.simulated_market_data:
                # Filter bars by date if specified
                bars = self.simulated_market_data[symbol]['bars']
                if start_dt:
                    bars = [bar for bar in bars if bar.timestamp >= start_dt]
                if end_dt:
                    bars = [bar for bar in bars if bar.timestamp <= end_dt]
                
                # Limit the number of bars
                if limit and len(bars) > limit:
                    bars = bars[-limit:]
                
                result[symbol] = bars
        
        log.debug(f"Retrieved {sum(len(v) for v in result.values())} simulated bars for {len(symbols)} symbols.")
        return result
    
    def get_latest_market_data(self, symbols: List[str]) -> MarketDataSnapshot:
        """Retrieves the latest quote and trade for multiple symbols."""
        if not symbols:
            return MarketDataSnapshot()
        
        # Update prices before returning market data
        self._update_simulated_prices()
        
        snapshot = MarketDataSnapshot()
        snapshot.latest_quotes = {}
        snapshot.latest_trades = {}
        
        for symbol in symbols:
            if symbol in self.simulated_market_data:
                # Create a simulated quote
                current_price = self.simulated_market_data[symbol]['current_price']
                ask_price = current_price * (1 + random.uniform(0, 0.001))  # Slightly higher than current
                bid_price = current_price * (1 - random.uniform(0, 0.001))  # Slightly lower than current
                
                quote = Quote(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    ask_exchange='SIMU',
                    ask_price=ask_price,
                    ask_size=random.randint(100, 1000),
                    bid_exchange='SIMU',
                    bid_price=bid_price,
                    bid_size=random.randint(100, 1000),
                    conditions=['R'],
                    tape='C'
                )
                snapshot.latest_quotes[symbol] = quote
                
                # Create a simulated trade
                trade = Trade(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    exchange='SIMU',
                    price=current_price,
                    size=random.randint(100, 1000),
                    id=str(uuid.uuid4()),
                    conditions=['@'],
                    tape='C'
                )
                snapshot.latest_trades[symbol] = trade
        
        log.debug(f"Retrieved latest simulated market data snapshot for {len(symbols)} symbols.")
        return snapshot
    
    def submit_order(self, order_data: Order) -> Order:
        """Submits an order to the brokerage."""
        if not self.is_market_open() and not order_data.extended_hours:
            # Allow GTC orders outside market hours, but log warning
            if order_data.time_in_force != OrderTimeInForce.GTC:
                log.warning(f"Attempting to place non-GTC order for {order_data.symbol} while market is closed.")
            else:
                log.info(f"Placing GTC order for {order_data.symbol} outside market hours.")
        
        log.info(f"Submitting simulated order: {order_data.side} {order_data.qty} {order_data.symbol} @ {order_data.type}")
        
        # Check if symbol exists in our simulated market data
        if order_data.symbol not in self.simulated_market_data:
            log.error(f"Symbol {order_data.symbol} not found in simulated market data.")
            order_data.status = OrderStatus.REJECTED
            order_data.failed_at = datetime.utcnow()
            raise BrokerageError(f"Symbol {order_data.symbol} not found in simulated market data.")
        
        # Check if we have enough cash for the order
        current_price = self.simulated_market_data[order_data.symbol]['current_price']
        order_value = order_data.qty * current_price
        
        if order_data.side == OrderSide.BUY and order_value > self.simulated_account['cash']:
            log.error(f"Insufficient cash for order: {order_value} > {self.simulated_account['cash']}")
            order_data.status = OrderStatus.REJECTED
            order_data.failed_at = datetime.utcnow()
            raise BrokerageError(f"Insufficient cash for order: {order_value} > {self.simulated_account['cash']}")
        
        # Generate a unique order ID
        order_id = str(uuid.uuid4())
        order_data.id = order_id
        
        # Set order status
        order_data.status = OrderStatus.FILLED  # Simulate immediate fill for simplicity
        order_data.submitted_at = datetime.utcnow()
        order_data.filled_at = datetime.utcnow()
        order_data.filled_qty = order_data.qty
        order_data.filled_avg_price = current_price
        
        # Update account and positions
        if order_data.side == OrderSide.BUY:
            # Deduct cash
            self.simulated_account['cash'] -= order_value
            
            # Update position
            if order_data.symbol in self.simulated_positions:
                # Update existing position
                position = self.simulated_positions[order_data.symbol]
                total_qty = position['qty'] + order_data.qty
                total_value = position['qty'] * position['avg_entry_price'] + order_data.qty * current_price
                position['avg_entry_price'] = total_value / total_qty
                position['qty'] = total_qty
            else:
                # Create new position
                self.simulated_positions[order_data.symbol] = {
                    'qty': order_data.qty,
                    'avg_entry_price': current_price
                }
        elif order_data.side == OrderSide.SELL:
            # Check if we have the position
            if order_data.symbol not in self.simulated_positions:
                log.error(f"Cannot sell {order_data.symbol}: Position not found.")
                order_data.status = OrderStatus.REJECTED
                order_data.failed_at = datetime.utcnow()
                raise BrokerageError(f"Cannot sell {order_data.symbol}: Position not found.")
            
            position = self.simulated_positions[order_data.symbol]
            if position['qty'] < order_data.qty:
                log.error(f"Cannot sell {order_data.qty} shares of {order_data.symbol}: Only have {position['qty']} shares.")
                order_data.status = OrderStatus.REJECTED
                order_data.failed_at = datetime.utcnow()
                raise BrokerageError(f"Cannot sell {order_data.qty} shares of {order_data.symbol}: Only have {position['qty']} shares.")
            
            # Add cash
            self.simulated_account['cash'] += order_value
            
            # Update position
            position['qty'] -= order_data.qty
            if position['qty'] == 0:
                # Remove position if fully sold
                del self.simulated_positions[order_data.symbol]
        
        # Store order
        self.simulated_orders[order_id] = order_data
        
        log.info(f"Simulated order submitted successfully for {order_data.symbol}. Order ID: {order_data.id}, Status: {order_data.status.value}")
        return order_data
    
    def get_order_by_client_id(self, client_order_id: str) -> Optional[Order]:
        """Retrieves an order by its client_order_id."""
        log.debug(f"Getting simulated order by client ID: {client_order_id}")
        
        # Find order by client_order_id
        for order in self.simulated_orders.values():
            if order.client_order_id == client_order_id:
                log.debug(f"Found simulated order {order.id} (Client ID: {client_order_id}), Status: {order.status.value}")
                return order
        
        log.warning(f"Simulated order with client ID {client_order_id} not found.")
        return None
    
    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Retrieves an order by its brokerage-assigned ID."""
        log.debug(f"Getting simulated order by ID: {order_id}")
        
        if order_id in self.simulated_orders:
            order = self.simulated_orders[order_id]
            log.debug(f"Found simulated order {order.id}, Status: {order.status.value}")
            return order
        
        log.warning(f"Simulated order with ID {order_id} not found.")
        return None
    
    def list_orders(self, status: Optional[str] = 'open', limit: int = 50, after: Optional[datetime] = None, until: Optional[datetime] = None, direction: str = 'desc', nested: bool = False) -> List[Order]:
        """Lists orders based on specified filters."""
        log.debug(f"Listing simulated orders with status: {status}, limit: {limit}")
        
        # Filter orders by status
        filtered_orders = []
        for order in self.simulated_orders.values():
            if status == 'all' or order.status.value.lower() == status.lower():
                if after is None or order.submitted_at >= after:
                    if until is None or order.submitted_at <= until:
                        filtered_orders.append(order)
        
        # Sort orders by submitted_at
        filtered_orders.sort(key=lambda o: o.submitted_at, reverse=(direction.lower() == 'desc'))
        
        # Limit the number of orders
        if limit and len(filtered_orders) > limit:
            filtered_orders = filtered_orders[:limit]
        
        log.debug(f"Retrieved {len(filtered_orders)} simulated orders.")
        return filtered_orders
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancels an open order by its brokerage-assigned ID."""
        log.info(f"Attempting to cancel simulated order ID: {order_id}")
        
        if order_id not in self.simulated_orders:
            log.warning(f"Cannot cancel simulated order {order_id}: Order not found.")
            return False
        
        order = self.simulated_orders[order_id]
        if order.status not in [OrderStatus.NEW, OrderStatus.ACCEPTED, OrderStatus.PENDING_NEW]:
            log.warning(f"Cannot cancel simulated order {order_id}: Status is '{order.status.value}', not cancelable.")
            return False
        
        # Update order status
        order.status = OrderStatus.CANCELED
        order.canceled_at = datetime.utcnow()
        
        log.info(f"Simulated order {order_id} canceled successfully.")
        return True
    
    def _check_account_status(self, account_info):
        """Checks if the account status is ACTIVE."""
        # This is a no-op in simulation mode
        pass
