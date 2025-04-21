from mattermostdriver import Driver
import smtplib
from email.mime.text import MIMEText
from typing import Optional

from .. import config
from ..utils.logger import log
from ..utils.exceptions import NotificationError, ConfigError

class NotificationInterface:
    """
    Interface for sending notifications via different channels (Mattermost, Email).
    """

    def __init__(self):
        log.info("Initializing NotificationInterface...")
        self.mattermost_driver = None
        self.mattermost_channel_id = None

        # --- Mattermost Initialization ---
        if config.MATTERMOST_ENABLED:
            if not all([config.MATTERMOST_URL, config.MATTERMOST_TOKEN, config.MATTERMOST_CHANNEL_ID]):
                log.error("Mattermost is enabled, but required configuration (URL, Token, Channel ID) is missing.")
                # Decide whether to raise an error or just disable Mattermost
                # raise ConfigError("Missing required Mattermost configuration.")
            else:
                try:
                    # Ensure URL starts with http:// or https://
                    mm_url = config.MATTERMOST_URL
                    if not mm_url.startswith(('http://', 'https://')):
                        log.warning(f"Mattermost URL '{mm_url}' does not start with http/https. Prepending 'https://'.")
                        mm_url = f"https://{mm_url}"

                    # Extract scheme, netloc (host:port), and path
                    from urllib.parse import urlparse
                    parsed_url = urlparse(mm_url)
                    scheme = parsed_url.scheme
                    netloc_parts = parsed_url.netloc.split(':')
                    host = netloc_parts[0]
                    port = 443 if scheme == 'https' else 80 # Default ports
                    if len(netloc_parts) > 1:
                        try:
                            port = int(netloc_parts[1])
                        except ValueError:
                             log.error(f"Invalid port in Mattermost URL: {netloc_parts[1]}")
                             raise ConfigError(f"Invalid port in Mattermost URL: {netloc_parts[1]}")
                    basepath = parsed_url.path.rstrip('/') # Remove trailing slash if present

                    log.info(f"Connecting to Mattermost: Scheme={scheme}, Host={host}, Port={port}, BasePath={basepath}, Token=****")

                    self.mattermost_driver = Driver({
                        'url': host,
                        'token': config.MATTERMOST_TOKEN,
                        'scheme': scheme,
                        'port': port,
                        'basepath': basepath or '/api/v4', # Default basepath if none provided
                        'verify': True, # Set to False if using self-signed certs (not recommended)
                        'timeout': 10,
                    })
                    self.mattermost_driver.login()
                    # Verify channel exists (optional but recommended)
                    # channel_info = self.mattermost_driver.channels.get_channel(config.MATTERMOST_CHANNEL_ID)
                    self.mattermost_channel_id = config.MATTERMOST_CHANNEL_ID
                    log.info(f"Mattermost driver initialized and logged in. Ready to send to channel ID: {self.mattermost_channel_id}")

                except Exception as e:
                    log.error(f"Failed to initialize Mattermost driver: {e}", exc_info=True)
                    self.mattermost_driver = None # Ensure driver is None if init fails
                    # Optionally raise NotificationError here if Mattermost is critical
                    # raise NotificationError(f"Failed to initialize Mattermost: {e}") from e
        else:
            log.info("Mattermost notifications are disabled in configuration.")

        # --- Email Initialization (Placeholder) ---
        if config.EMAIL_ENABLED:
            log.warning("Email notifications are enabled but not fully implemented in this version.")
            if not all([config.SMTP_SERVER, config.SMTP_PORT, config.SMTP_USERNAME, config.SMTP_PASSWORD, config.ADMIN_EMAIL]):
                 log.error("Email is enabled, but required SMTP configuration is missing.")
                 # raise ConfigError("Missing required SMTP configuration for email.")
            else:
                 log.info("Email configuration found (implementation pending).")


    def send_notification(self, message: str, subject: Optional[str] = "Trading System Alert") -> bool:
        """
        Sends a notification message through all enabled channels.

        Args:
            message: The main content of the notification.
            subject: The subject line (primarily for email).

        Returns:
            True if at least one notification was sent successfully, False otherwise.
        """
        success = False
        message_with_prefix = f"**Trading System:**\n{message}" # Add prefix for clarity

        # --- Send via Mattermost ---
        if self.mattermost_driver and self.mattermost_channel_id:
            try:
                log.debug(f"Sending Mattermost notification to channel {self.mattermost_channel_id}...")
                self.mattermost_driver.posts.create_post(options={
                    'channel_id': self.mattermost_channel_id,
                    'message': message_with_prefix
                })
                log.info(f"Successfully sent notification to Mattermost channel {self.mattermost_channel_id}.")
                success = True
            except Exception as e:
                log.error(f"Failed to send Mattermost notification: {e}", exc_info=True)
                # Don't raise here, try other channels

        # --- Send via Email (Placeholder) ---
        if config.EMAIL_ENABLED:
            log.debug("Attempting to send email notification (implementation pending)...")
            try:
                # --- SMTP Logic (Implement when needed) ---
                # msg = MIMEText(message)
                # msg['Subject'] = subject
                # msg['From'] = config.SMTP_USERNAME
                # msg['To'] = config.ADMIN_EMAIL

                # server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
                # server.starttls() # Use TLS
                # server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                # server.sendmail(config.SMTP_USERNAME, [config.ADMIN_EMAIL], msg.as_string())
                # server.quit()
                # log.info(f"Successfully sent notification email to {config.ADMIN_EMAIL}.")
                # success = True
                log.warning("Email sending logic is not yet implemented.")
                pass # Remove pass when implemented
            except Exception as e:
                log.error(f"Failed to send email notification: {e}", exc_info=True)

        if not success:
             log.warning("Failed to send notification through any enabled channel.")

        return success

# Example Usage (can be removed or moved to tests)
# if __name__ == '__main__':
#     try:
#         notifier = NotificationInterface()
#         print("Notification Interface Initialized.")

#         # Test Mattermost (if enabled and configured)
#         if notifier.mattermost_driver:
#             print("\nTesting Mattermost...")
#             test_message = f"This is a test notification from the Trading System at {datetime.now()}."
#             sent = notifier.send_notification(test_message)
#             print(f"Mattermost test sent: {sent}")
#         else:
#             print("\nSkipping Mattermost test (disabled or failed to initialize).")

#         # Test Email (if enabled) - will just log warning for now
#         if config.EMAIL_ENABLED:
#              print("\nTesting Email (placeholder)...")
#              sent = notifier.send_notification("Test email message.", subject="Trading System Test Email")
#              print(f"Email test attempted: {sent}")


#     except (ConfigError, NotificationError) as e:
#         print(f"Error initializing or testing NotificationInterface: {e}")
#     except Exception as ex:
#         print(f"An unexpected error occurred: {ex}")
