from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone # Added timezone
from enum import Enum

# Note: These models might need adjustments based on the specific data format
# provided by the Alpaca API or other data sources.

class BarTimeframe(str, Enum):
    """Standard bar timeframes."""
    MINUTE = "1Min"
    FIVE_MINUTE = "5Min"
    FIFTEEN_MINUTE = "15Min"
    THIRTY_MINUTE = "30Min"
    HOUR = "1Hour"
    DAY = "1Day"
    WEEK = "1Week"
    MONTH = "1Month"

class Bar(BaseModel):
    """Represents a single OHLCV bar for a symbol."""
    symbol: str = Field(..., description="Asset symbol")
    timestamp: datetime = Field(..., description="Timestamp marking the beginning of the bar interval (UTC)")
    open: float = Field(..., alias='o', description="Opening price")
    high: float = Field(..., alias='h', description="Highest price")
    low: float = Field(..., alias='l', description="Lowest price")
    close: float = Field(..., alias='c', description="Closing price")
    volume: float = Field(..., alias='v', description="Trading volume during the bar interval")
    trade_count: Optional[int] = Field(None, alias='n', description="Number of trades during the bar interval")
    vwap: Optional[float] = Field(None, alias='vw', description="Volume Weighted Average Price")

    model_config = ConfigDict(populate_by_name=True) # Pydantic V2 style

class Quote(BaseModel):
    """Represents a single bid/ask quote for a symbol."""
    symbol: str = Field(..., description="Asset symbol")
    timestamp: datetime = Field(..., description="Timestamp of the quote (UTC)")
    ask_exchange: Optional[str] = Field(None, alias='ax', description="Exchange providing the ask")
    ask_price: float = Field(..., alias='ap', description="Asking price")
    ask_size: float = Field(..., alias='as', description="Size of the ask")
    bid_exchange: Optional[str] = Field(None, alias='bx', description="Exchange providing the bid")
    bid_price: float = Field(..., alias='bp', description="Bidding price")
    bid_size: float = Field(..., alias='bs', description="Size of the bid")
    conditions: Optional[List[str]] = Field(None, alias='c', description="Quote conditions")
    tape: Optional[str] = Field(None, alias='z', description="Tape identifier") # Tape A, B, C

    model_config = ConfigDict(populate_by_name=True) # Pydantic V2 style

class Trade(BaseModel):
    """Represents a single executed trade for a symbol."""
    symbol: str = Field(..., description="Asset symbol")
    timestamp: datetime = Field(..., description="Timestamp of the trade (UTC)")
    exchange: Optional[str] = Field(None, alias='x', description="Exchange where the trade occurred")
    price: float = Field(..., alias='p', description="Trade price")
    size: float = Field(..., alias='s', description="Trade size (volume)")
    id: Optional[int] = Field(None, alias='i', description="Trade ID (often broker-specific)")
    conditions: Optional[List[str]] = Field(None, alias='c', description="Trade conditions")
    tape: Optional[str] = Field(None, alias='z', description="Tape identifier") # Tape A, B, C
    taker_side: Optional[str] = Field(None, description="Side of the taker ('B' for buy, 'S' for sell) - if available")

    model_config = ConfigDict(populate_by_name=True) # Pydantic V2 style

class MarketDataSnapshot(BaseModel):
    """Represents a snapshot of market data for multiple symbols at a point in time."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # Use timezone-aware now()
    latest_bars: Optional[Dict[str, Bar]] = Field(None, description="Latest OHLCV bars keyed by symbol")
    latest_quotes: Optional[Dict[str, Quote]] = Field(None, description="Latest quotes keyed by symbol")
    latest_trades: Optional[Dict[str, Trade]] = Field(None, description="Latest trades keyed by symbol")
    # Could add other data like news, indicators, etc.

# Example Usage (can be removed):
# if __name__ == "__main__":
#     bar_data = {
#         "symbol": "AAPL", "t": "2024-01-15T14:30:00Z", "o": 175.0, "h": 175.5, "l": 174.8, "c": 175.2, "v": 100000
#     }
#     # Timestamps from Alpaca often need parsing/timezone handling
#     bar_data['t'] = datetime.fromisoformat(bar_data['t'].replace('Z', '+00:00'))
#     bar = Bar(symbol=bar_data['symbol'], timestamp=bar_data['t'], **bar_data) # Pass symbol/timestamp explicitly if not using alias 't'
#     print("Bar:")
#     print(bar.model_dump_json(indent=2, by_alias=True)) # Use by_alias=True to see 'o', 'h', etc.

#     quote_data = {
#         "symbol": "MSFT", "t": "2024-01-15T14:31:05.123Z", "ax": "NASDAQ", "ap": 310.50, "as": 100, "bx": "NASDAQ", "bp": 310.45, "bs": 200
#     }
#     quote_data['t'] = datetime.fromisoformat(quote_data['t'].replace('Z', '+00:00'))
#     quote = Quote(symbol=quote_data['symbol'], timestamp=quote_data['t'], **quote_data)
#     print("\nQuote:")
#     print(quote.model_dump_json(indent=2, by_alias=True))

#     trade_data = {
#         "symbol": "GOOG", "t": "2024-01-15T14:32:10.456Z", "x": "NYSE", "p": 140.00, "s": 50, "i": 123456789
#     }
#     trade_data['t'] = datetime.fromisoformat(trade_data['t'].replace('Z', '+00:00'))
#     trade = Trade(symbol=trade_data['symbol'], timestamp=trade_data['t'], **trade_data)
#     print("\nTrade:")
#     print(trade.model_dump_json(indent=2, by_alias=True))

#     snapshot = MarketDataSnapshot(
#         latest_bars={"AAPL": bar},
#         latest_quotes={"MSFT": quote},
#         latest_trades={"GOOG": trade}
#     )
#     print("\nMarket Data Snapshot:")
#     print(snapshot.model_dump_json(indent=2, by_alias=True))
