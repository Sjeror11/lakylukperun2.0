import pytest
import os
import sys
from datetime import datetime

# Adjust path to import from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports from the trading system
from src.interfaces.notification import NotificationInterface
from src.utils.exceptions import NotificationError, ConfigError
from src import config # Ensure config is loaded

# --- Test Fixture ---

@pytest.fixture(scope="module")
def notification_interface():
    """Provides an initialized NotificationInterface instance."""
    # Skip module if Mattermost is not enabled or configured
    if not config.MATTERMOST_ENABLED:
        pytest.skip("Mattermost notifications are disabled in configuration.")
    if not all([config.MATTERMOST_URL, config.MATTERMOST_TOKEN, config.MATTERMOST_CHANNEL_ID]):
        pytest.skip("Mattermost is enabled, but required configuration is missing.")

    try:
        interface = NotificationInterface()
        # Check if driver initialization actually succeeded
        if not interface.mattermost_driver:
             pytest.skip("Mattermost driver failed to initialize during setup.")
        return interface
    except (ConfigError, NotificationError) as e:
        pytest.fail(f"Failed to initialize NotificationInterface for testing: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error initializing NotificationInterface: {e}")

# --- Mattermost Tests ---

# Mark test to skip if fixture failed/skipped
@pytest.mark.skipif(not config.MATTERMOST_ENABLED or not all([config.MATTERMOST_URL, config.MATTERMOST_TOKEN, config.MATTERMOST_CHANNEL_ID]), reason="Mattermost not enabled or fully configured.")
def test_send_mattermost_notification(notification_interface):
    """Tests sending a simple notification to the configured Mattermost channel."""
    assert notification_interface.mattermost_driver is not None
    assert notification_interface.mattermost_channel_id is not None

    test_message = f"Hello from pytest! This is a test notification for the AI Trading System sent at {datetime.now().isoformat()}."
    print(f"\n[Notification Test] Sending test message to Mattermost channel: {notification_interface.mattermost_channel_id}")

    try:
        success = notification_interface.send_notification(test_message)
        assert success, "send_notification returned False, indicating failure."
        print("  Mattermost notification sent successfully (check the channel).")
        # Note: We can only assert that the API call didn't raise an exception.
        # Actual delivery confirmation isn't possible here.
    except NotificationError as e:
        pytest.fail(f"NotificationError during Mattermost send: {e}")
    except Exception as e:
        # Catch potential issues from the mattermostdriver library
        pytest.fail(f"Unexpected error sending Mattermost notification: {e}")

# --- Email Tests (Skipped) ---

@pytest.mark.skip(reason="Email notification sending is not implemented.")
def test_send_email_notification():
    """Placeholder test for email notifications."""
    pass
