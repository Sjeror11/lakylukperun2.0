import requests
import logging
from typing import Optional, Dict, Any

from .. import config  # Use relative import within the src package
from ..utils.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

class PerplexityInterface:
    """
    Interface for interacting with the Perplexity API for market research.
    """
    BASE_URL = "https://api.perplexity.ai" # Standard Perplexity API endpoint

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the PerplexityInterface.

        Args:
            api_key: The Perplexity API key. If None, it's fetched from config.
        """
        self.api_key = api_key or config.PERPLEXITY_API_KEY
        if not self.api_key:
            logger.warning("Perplexity API key is not configured. PerplexityInterface will not function.")
            # Optionally raise an error if Perplexity is strictly required
            # raise ValueError("Perplexity API key is required but not configured.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Makes a POST request to the Perplexity API.

        Args:
            endpoint: The API endpoint (e.g., '/chat/completions').
            payload: The JSON payload for the request.

        Returns:
            The JSON response from the API.

        Raises:
            ExternalAPIError: If the API request fails or returns an error status.
        """
        if not self.api_key:
            raise ExternalAPIError("Perplexity API key is missing. Cannot make request.")

        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API request failed: {e}", exc_info=True)
            raise ExternalAPIError(f"Error connecting to Perplexity API: {e}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during Perplexity API request: {e}", exc_info=True)
            raise ExternalAPIError(f"Unexpected error during Perplexity API call: {e}") from e

    def get_market_insights(self, query: str, model: str = "sonar-small-online") -> Optional[str]:
        """
        Queries Perplexity for market insights or news related to a specific topic.

        Args:
            query: The research query (e.g., "Latest news on AAPL stock").
            model: The Perplexity model to use (default: sonar-small-online).

        Returns:
            The text content of the Perplexity response, or None if an error occurs or no content is found.
        """
        if not self.api_key:
            logger.warning("Cannot get market insights, Perplexity API key not set.")
            return None

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an AI assistant providing concise market research insights."},
                {"role": "user", "content": query}
            ]
        }
        endpoint = "/chat/completions" # Standard chat completions endpoint

        try:
            response_data = self._make_request(endpoint, payload)
            # Extract the content from the response structure
            # Adjust based on the actual Perplexity API response format
            if response_data and 'choices' in response_data and len(response_data['choices']) > 0:
                message = response_data['choices'][0].get('message')
                if message and 'content' in message:
                    return message['content'].strip()
            logger.warning(f"Could not extract content from Perplexity response for query '{query}'. Response: {response_data}")
            return None
        except ExternalAPIError as e:
            logger.error(f"Failed to get market insights from Perplexity for query '{query}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing Perplexity response for query '{query}': {e}", exc_info=True)
            return None

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # Ensure you have a .env file with PERPLEXITY_API_KEY in the project root
    # or set the environment variable directly before running.
    # Example: export PERPLEXITY_API_KEY='your_key_here'
    from dotenv import load_dotenv
    import os
    # Load .env from the project root (assuming this script is run from src/interfaces)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path, override=True)
        print(f"Loaded .env from {dotenv_path}")
    else:
        print(f".env file not found at {dotenv_path}, ensure PERPLEXITY_API_KEY is set.")


    logging.basicConfig(level=logging.INFO)
    perplexity_client = PerplexityInterface()

    if perplexity_client.api_key:
        test_query = "What is the latest sentiment around NVIDIA stock?"
        print(f"\nQuerying Perplexity: '{test_query}'")
        insights = perplexity_client.get_market_insights(test_query)

        if insights:
            print("\n--- Perplexity Response ---")
            print(insights)
            print("-------------------------\n")
        else:
            print("\nFailed to get insights from Perplexity.")
    else:
        print("\nSkipping Perplexity test as API key is not configured.")
