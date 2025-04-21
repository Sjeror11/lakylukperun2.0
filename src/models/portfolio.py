from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone # Added timezone

class Position(BaseModel):
    """Represents a single position held in the portfolio."""
    symbol: str = Field(..., description="Asset symbol")
    qty: float = Field(..., description="Number of shares held (can be negative for short positions)")
    avg_entry_price: float = Field(..., description="Average price at which the position was entered")
    current_price: Optional[float] = Field(None, description="Last known market price of the asset")
    market_value: Optional[float] = Field(None, description="Total market value of the position (qty * current_price)")
    unrealized_pl: Optional[float] = Field(None, description="Unrealized profit or loss")
    unrealized_plpc: Optional[float] = Field(None, description="Unrealized profit or loss percentage")
    cost_basis: float = Field(..., description="Total cost of acquiring the position (qty * avg_entry_price)")
    last_day_price: Optional[float] = Field(None, description="Market price at the previous trading day's close")
    change_today: Optional[float] = Field(None, description="Change in market value since previous close") # market_value - (qty * last_day_price)

    # Optional: Add methods for calculations if needed
    # def calculate_market_value(self):
    #     if self.current_price is not None:
    #         self.market_value = self.qty * self.current_price
    #     return self.market_value

    # def calculate_unrealized_pl(self):
    #     if self.current_price is not None:
    #         self.market_value = self.qty * self.current_price
    #         self.unrealized_pl = self.market_value - self.cost_basis
    #         if self.cost_basis != 0:
    #             self.unrealized_plpc = (self.unrealized_pl / self.cost_basis)
    #         else:
    #             self.unrealized_plpc = 0.0
    #     return self.unrealized_pl


class Portfolio(BaseModel):
    """Represents the overall state of the trading account portfolio."""
    account_id: str = Field(..., description="Brokerage account identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the portfolio state was captured") # Use timezone-aware now()
    cash: float = Field(..., description="Available cash balance")
    equity: float = Field(..., description="Total value of cash + positions")
    buying_power: float = Field(..., description="Buying power available for trading")
    positions: Dict[str, Position] = Field(default_factory=dict, description="Dictionary of current positions, keyed by symbol")
    initial_margin: Optional[float] = Field(None, description="Initial margin requirement")
    maintenance_margin: Optional[float] = Field(None, description="Maintenance margin requirement")
    portfolio_value: float = Field(..., description="Alias for equity") # Often used interchangeably
    daytrade_count: Optional[int] = Field(None, description="Number of day trades executed")
    is_account_blocked: bool = Field(False, description="Whether the account is currently blocked from trading")
    is_trading_blocked: bool = Field(False, description="Whether trading is currently blocked for the account")
    regt_buying_power: Optional[float] = Field(None, description="Reg T buying power")
    shorting_enabled: bool = Field(False, description="Whether short selling is enabled for the account")
    currency: str = Field("USD", description="Base currency of the account")

    # Optional: Add methods for calculations
    # def update_equity_and_value(self):
    #     total_position_value = sum(pos.market_value for pos in self.positions.values() if pos.market_value is not None)
    #     self.equity = self.cash + total_position_value
    #     self.portfolio_value = self.equity
    #     return self.equity

    # def get_position(self, symbol: str) -> Optional[Position]:
    #     return self.positions.get(symbol)

    # def update_position(self, position: Position):
    #     self.positions[position.symbol] = position
    #     # Recalculate portfolio metrics after updating a position
    #     # self.update_equity_and_value()


# Example Usage (can be removed):
# if __name__ == "__main__":
#     pos1 = Position(
#         symbol="AAPL",
#         qty=10,
#         avg_entry_price=170.0,
#         current_price=175.0,
#         cost_basis=1700.0
#     )
#     # pos1.calculate_market_value()
#     # pos1.calculate_unrealized_pl()

#     pos2 = Position(
#         symbol="MSFT",
#         qty=5,
#         avg_entry_price=300.0,
#         current_price=310.0,
#         cost_basis=1500.0
#     )
#     # pos2.calculate_market_value()
#     # pos2.calculate_unrealized_pl()

#     portfolio_state = Portfolio(
#         account_id="PA123456",
#         cash=50000.0,
#         equity=53300.0, # Example value, should be calculated
#         buying_power=100000.0,
#         positions={"AAPL": pos1, "MSFT": pos2},
#         portfolio_value=53300.0 # Example value
#     )

#     # portfolio_state.update_equity_and_value() # Call calculation method

#     print("Portfolio State:")
#     print(portfolio_state.model_dump_json(indent=2))
