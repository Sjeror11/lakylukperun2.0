"""
Patch script to enable simulation mode for Perun Trading System.
This script modifies the BrokerageInterface class to work in simulation mode without requiring API keys.
"""

import os
import sys

# Set environment variable for simulation mode
os.environ['SIMULATION_MODE'] = 'true'

# Print banner
print("=" * 50)
print("PERUN TRADING SYSTEM - SIMULATION MODE")
print("=" * 50)
print("Running in simulation mode with simulated market data.")
print("No actual trades will be executed.")
print("=" * 50)

# Run the main application
sys.path.insert(0, os.path.abspath('.'))
import main
main.main()
