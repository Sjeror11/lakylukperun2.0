import pytest
import os
import sys
import json

# Adjust path to import from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Imports from the trading system
from src.interfaces.large_language_model import LLMInterface
from src.utils.exceptions import LLMError, ConfigError
from src import config # Ensure config is loaded

# --- Test Fixture ---

@pytest.fixture(scope="module")
def llm_interface():
    """Provides an initialized LLMInterface instance."""
    try:
        interface = LLMInterface()
        return interface
    except ConfigError as e:
        pytest.fail(f"Failed to initialize LLMInterface due to ConfigError: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error initializing LLMInterface: {e}")

# --- OpenAI Tests ---

@pytest.mark.skipif(not config.OPENAI_API_KEY, reason="OpenAI API key not configured.")
def test_openai_text_generation(llm_interface):
    """Tests basic text generation using an OpenAI model."""
    assert llm_interface.openai_client is not None
    prompt = "Briefly explain what an API is."
    model = "gpt-3.5-turbo" # Use a common/cheaper model for testing
    print(f"\n[LLM Test] Testing OpenAI text generation with model: {model}")
    try:
        response = llm_interface.generate_response(prompt, model_name=model, max_tokens=50)
        assert isinstance(response, str)
        assert len(response) > 5 # Check for non-empty response
        assert "application programming interface" in response.lower() or "api" in response.lower()
        print(f"  OpenAI Response (preview): {response[:80]}...")
    except LLMError as e:
        pytest.fail(f"LLMError during OpenAI text generation: {e}")
    except ValueError as e:
         pytest.fail(f"ValueError during OpenAI text generation (likely model issue): {e}")

@pytest.mark.skipif(not config.OPENAI_API_KEY, reason="OpenAI API key not configured.")
def test_openai_json_generation(llm_interface):
    """Tests JSON generation using an OpenAI model with JSON mode."""
    assert llm_interface.openai_client is not None
    prompt = "Create a JSON object with two keys: 'name' set to 'Test Product' and 'price' set to 99.99."
    model = "gpt-3.5-turbo" # Ensure model supports JSON mode if using older ones
    print(f"\n[LLM Test] Testing OpenAI JSON generation with model: {model}")
    try:
        # generate_json_response automatically sets json_mode=True for OpenAI
        response_dict = llm_interface.generate_json_response(prompt, model_name=model)
        assert isinstance(response_dict, dict)
        assert response_dict.get("name") == "Test Product"
        assert response_dict.get("price") == 99.99
        print(f"  OpenAI JSON Response: {response_dict}")
    except LLMError as e:
        # Check if it's a JSON parsing error specifically
        if "Failed to parse LLM response as JSON" in str(e):
             pytest.fail(f"OpenAI failed to return valid JSON: {e}")
        else:
             pytest.fail(f"LLMError during OpenAI JSON generation: {e}")
    except ValueError as e:
         pytest.fail(f"ValueError during OpenAI JSON generation: {e}")
    except json.JSONDecodeError as e:
         pytest.fail(f"JSONDecodeError parsing OpenAI response: {e}")


# --- Gemini Tests ---

@pytest.mark.skipif(not config.GEMINI_API_KEY, reason="Gemini API key not configured.")
def test_gemini_text_generation(llm_interface):
    """Tests basic text generation using a Gemini model."""
    assert llm_interface.gemini_model is not None
    prompt = "What is the primary function of a CPU in a computer?"
    model = "gemini-1.5-flash-latest" # Use a valid, faster model for testing
    print(f"\n[LLM Test] Testing Gemini text generation with model: {model}")
    try:
        response = llm_interface.generate_response(prompt, model_name=model, max_tokens=60)
        assert isinstance(response, str)
        assert len(response) > 5
        assert "central processing unit" in response.lower() or "execute instructions" in response.lower()
        print(f"  Gemini Response (preview): {response[:80]}...")
    except LLMError as e:
        pytest.fail(f"LLMError during Gemini text generation: {e}")
    except ValueError as e:
         pytest.fail(f"ValueError during Gemini text generation: {e}")


@pytest.mark.skipif(not config.GEMINI_API_KEY, reason="Gemini API key not configured.")
def test_gemini_json_generation(llm_interface):
    """Tests JSON generation using a Gemini model (relies on prompt instructions)."""
    assert llm_interface.gemini_model is not None
    # Prompt explicitly asks for JSON only
    prompt = "Generate ONLY a valid JSON object representing coordinates with 'latitude' (float) and 'longitude' (float) keys. Example: latitude=40.7128 longitude=-74.0060."
    model = "gemini-1.5-flash-latest" # Use a valid, faster model for testing
    print(f"\n[LLM Test] Testing Gemini JSON generation with model: {model}")
    try:
        # generate_json_response adds extra instructions for Gemini if needed
        response_dict = llm_interface.generate_json_response(prompt, model_name=model)
        assert isinstance(response_dict, dict)
        assert "latitude" in response_dict
        assert "longitude" in response_dict
        assert isinstance(response_dict["latitude"], float)
        assert isinstance(response_dict["longitude"], float)
        print(f"  Gemini JSON Response: {response_dict}")
    except LLMError as e:
        if "Failed to parse LLM response as JSON" in str(e):
             pytest.fail(f"Gemini failed to return valid JSON: {e}")
        else:
             pytest.fail(f"LLMError during Gemini JSON generation: {e}")
    except ValueError as e:
         pytest.fail(f"ValueError during Gemini JSON generation: {e}")
    except json.JSONDecodeError as e:
         pytest.fail(f"JSONDecodeError parsing Gemini response: {e}")

# Add tests for error handling, retries if implemented more explicitly
