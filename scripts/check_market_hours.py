#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timezone

# Adjust path to import from src by adding the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root) # Add project root, not src

try:
    from src.interfaces.brokerage import BrokerageInterface
    from src.utils.exceptions import BrokerageError
    from src import config # Load configuration
except ImportError as e:
    print(f"ERROR: Failed to import necessary modules: {e}", file=sys.stderr)
    print("Ensure you are running this script from the 'trading_system' directory", file=sys.stderr)
    print(f"Current sys.path: {sys.path}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: An unexpected error occurred during import: {e}", file=sys.stderr)
    sys.exit(1)

def check_status():
    """Checks and prints the current market status using the BrokerageInterface."""
    print("Initializing Brokerage Interface to check market status...")
    print(f"Using API Base URL: {config.ALPACA_BASE_URL}")

    try:
        brokerage = BrokerageInterface()
        clock = brokerage.api.get_clock() # Access the underlying clock object

        now_utc = datetime.now(timezone.utc)
        is_open = clock.is_open
        # Display times directly in UTC as provided by Alpaca
        next_open_utc = clock.next_open
        next_close_utc = clock.next_close

        print("\n--- Market Status ---")
        print(f"Current Time (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Market Open Now?  {'YES' if is_open else 'NO'}")
        # Format UTC times directly
        print(f"Next Open Time (UTC):   {next_open_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Next Close Time (UTC):  {next_close_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("---------------------\n")

    except BrokerageError as e:
        print(f"\nERROR: Failed to connect to brokerage or get market clock: {e}")
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    check_status()
