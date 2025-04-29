"""
Patch for BrokerageInterface to use simulation mode.
This module patches the BrokerageInterface class to use simulation mode when SIMULATION_MODE is set to true.
"""

import os
import sys
import importlib

# Check if we should use simulation mode
simulation_mode = os.environ.get('SIMULATION_MODE', 'false').lower() == 'true'

if simulation_mode:
    # Import the original module
    from src.interfaces import brokerage
    
    # Import the simulation module
    from src.interfaces.brokerage_simulation import SimulatedBrokerageInterface
    
    # Replace the BrokerageInterface class with SimulatedBrokerageInterface
    brokerage.BrokerageInterface = SimulatedBrokerageInterface
    
    # Print a message
    print("=" * 50)
    print("PERUN TRADING SYSTEM - SIMULATION MODE")
    print("=" * 50)
    print("Running in simulation mode with simulated market data.")
    print("No actual trades will be executed.")
    print("=" * 50)
