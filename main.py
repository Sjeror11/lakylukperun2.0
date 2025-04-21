#!/usr/bin/env python3

import sys
import os

# Ensure the src directory is in the Python path
# This allows running the script directly from the project root (trading_system/)
# or potentially as an installed module.
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import necessary components after adjusting path
try:
    from src.services.orchestration_service.daemon import OrchestrationDaemon
    from src.utils.logger import log # Import the configured logger
    from src.utils.exceptions import TradingSystemError
except ImportError as e:
     # Provide a more helpful error message if imports fail
     print(f"ERROR: Failed to import necessary modules: {e}", file=sys.stderr)
     print("Ensure you are running this script from the 'trading_system' directory", file=sys.stderr)
     print("or have installed the package correctly.", file=sys.stderr)
     print(f"Current sys.path: {sys.path}", file=sys.stderr)
     sys.exit(1)


def main():
    """
    Main entry point for the AI Trading System daemon.
    Initializes and runs the OrchestrationDaemon.
    """
    log.info("=============================================")
    log.info("=== Starting AI Trading System Daemon ===")
    log.info("=============================================")

    daemon = None # Initialize daemon to None
    try:
        # Initialize the main daemon class
        daemon = OrchestrationDaemon()

        # Start the main run loop
        daemon.run() # This loop continues until shutdown signal

    except TradingSystemError as e:
        log.critical(f"Trading System failed to start or run: {e}", exc_info=True)
        # Daemon initialization might have already tried to notify
        sys.exit(1)
    except KeyboardInterrupt:
        log.warning("KeyboardInterrupt received. Daemon should handle shutdown via signal handler.")
        # The daemon's signal handler should manage graceful exit
        # If the daemon isn't fully initialized, this might be the first exit point
        if daemon and daemon._running:
             pass # Daemon's handler will take over
        else:
             log.info("Exiting immediately (daemon not fully running or already stopped).")
        sys.exit(0)
    except Exception as e:
        log.critical(f"An unexpected critical error occurred at the main level: {e}", exc_info=True)
        # Attempt last-resort notification if possible
        if daemon and hasattr(daemon, 'notifier'):
             try:
                  daemon.notifier.send_notification(f"CRITICAL FAILURE: Unhandled exception at main level: {e}", subject="Trading System CRITICAL FAILURE")
             except Exception as notify_err:
                  log.error(f"Last resort notification failed: {notify_err}")
        sys.exit(1)
    finally:
        log.info("=============================================")
        log.info("=== AI Trading System Daemon Exiting ===")
        log.info("=============================================")


if __name__ == "__main__":
    main()
