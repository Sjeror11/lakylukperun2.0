import openai
import google.generativeai as genai
from typing import Optional, Dict, Any, Literal
import time
import json

from .. import config
from ..utils.logger import log
from ..utils.exceptions import LLMError, ConfigError

# --- Constants ---
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY_SECONDS = 5

class LLMInterface:
    """
    Interface for interacting with different Large Language Models (LLMs)
    like OpenAI's GPT models and Google's Gemini models.
    Handles authentication, API calls, and basic error handling/retries.
    """

    def __init__(self):
        log.info("Initializing LLMInterface...")
        self.openai_client = None
        self.gemini_model = None

        # --- OpenAI Initialization ---
        if config.OPENAI_API_KEY:
            try:
                # Use the new OpenAI client initialization
                self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                # Test connection (optional, e.g., list models)
                # self.openai_client.models.list()
                log.info("OpenAI client initialized successfully.")
            except openai.AuthenticationError as e:
                log.error(f"OpenAI Authentication Error: {e}. Check your OPENAI_API_KEY.", exc_info=True)
                # Don't raise here, allow partial initialization if other LLMs work
            except Exception as e:
                log.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
        else:
            log.warning("OPENAI_API_KEY not found in configuration. OpenAI models will be unavailable.")

        # --- Gemini Initialization ---
        if config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=config.GEMINI_API_KEY)
                # Initialize a default model instance - adjust model name as needed
                # Use a known valid model like gemini-1.5-pro-latest
                gemini_model_name = "gemini-1.5-pro-latest"
                self.gemini_model = genai.GenerativeModel(gemini_model_name)
                # Test connection (optional, e.g., generate dummy content)
                # self.gemini_model.generate_content("test")
                log.info(f"Google Gemini client configured successfully for model '{gemini_model_name}'.")
            except Exception as e:
                log.error(f"Failed to configure Google Gemini client: {e}", exc_info=True)
        else:
            log.warning("GEMINI_API_KEY not found in configuration. Gemini models will be unavailable.")

        if not self.openai_client and not self.gemini_model:
            raise ConfigError("No LLM clients could be initialized. Check API keys in configuration.")

    def _is_openai_model(self, model_name: str) -> bool:
        """Checks if the model name likely belongs to OpenAI."""
        # Simple check, can be made more robust
        return model_name.lower().startswith(('gpt-', 'text-'))

    def _is_gemini_model(self, model_name: str) -> bool:
        """Checks if the model name likely belongs to Google Gemini."""
        return model_name.lower().startswith('gemini-')

    def generate_response(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        system_prompt: Optional[str] = None,
        json_mode: bool = False, # For OpenAI JSON mode
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        retry_delay: int = DEFAULT_RETRY_DELAY_SECONDS
    ) -> str:
        """
        Generates a text response from the specified LLM.

        Args:
            prompt: The main user prompt.
            model_name: The specific model to use (e.g., 'gpt-4o', 'gemini-pro').
                        Defaults to config.DEFAULT_LLM_MODEL.
            temperature: Controls randomness (0.0 to 1.0+).
            max_tokens: Maximum number of tokens to generate.
            system_prompt: An optional system-level instruction (primarily for chat models).
            json_mode: If True, attempts to use OpenAI's JSON mode (requires specific prompt instructions).
            retry_attempts: Number of times to retry on transient errors.
            retry_delay: Delay in seconds between retries.

        Returns:
            The generated text response from the LLM.

        Raises:
            LLMError: If the API call fails after retries or configuration is invalid.
            ValueError: If the specified model is not supported or configured.
        """
        selected_model = model_name or config.DEFAULT_LLM_MODEL
        if not selected_model:
             raise ValueError("No LLM model specified and no default configured.")

        log.info(f"Generating LLM response using model: {selected_model}")
        # log.debug(f"Prompt (first 100 chars): {prompt[:100]}...") # Avoid logging full sensitive prompts

        last_exception = None
        for attempt in range(retry_attempts):
            try:
                if self._is_openai_model(selected_model):
                    if not self.openai_client:
                        raise LLMError("OpenAI client not initialized. Check API key.")

                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})

                    response_format = {"type": "json_object"} if json_mode else {"type": "text"}

                    start_time = time.time()
                    response = self.openai_client.chat.completions.create(
                        model=selected_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=response_format,
                        # Add other parameters like top_p, frequency_penalty if needed
                    )
                    end_time = time.time()
                    log.debug(f"OpenAI API call took {end_time - start_time:.2f} seconds.")

                    # Extract text content
                    content = response.choices[0].message.content
                    if content is None:
                         raise LLMError("OpenAI response content is None.")
                    log.info(f"Received response from {selected_model}.")
                    # log.debug(f"Response (first 100 chars): {content[:100]}...")
                    return content.strip()

                elif self._is_gemini_model(selected_model):
                    if not self.gemini_model:
                        raise LLMError("Gemini client not initialized. Check API key.")

                    # Adjust model instance if needed (though usually configured once)
                    if self.gemini_model.model_name != selected_model:
                         log.warning(f"Switching Gemini model instance to {selected_model} (consider configuring specific instances if needed).")
                         self.gemini_model = genai.GenerativeModel(selected_model)

                    # Construct prompt for Gemini (can include system instructions implicitly or explicitly)
                    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

                    # Configure generation parameters
                    generation_config = genai.types.GenerationConfig(
                        # candidate_count=1, # Default is 1
                        # stop_sequences=['...'],
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                        # top_p=...,
                        # top_k=...
                    )
                    # Note: Gemini doesn't have an explicit JSON mode like OpenAI's latest API.
                    # You need to instruct it within the prompt to output JSON.

                    start_time = time.time()
                    response = self.gemini_model.generate_content(
                        full_prompt,
                        generation_config=generation_config,
                        # safety_settings=... # Add safety settings if needed
                    )
                    end_time = time.time()
                    log.debug(f"Gemini API call took {end_time - start_time:.2f} seconds.")

                    # Handle potential blocks or errors in response
                    if not response.candidates:
                         block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Unknown"
                         log.error(f"Gemini response blocked. Reason: {block_reason}")
                         raise LLMError(f"Gemini response blocked: {block_reason}")
                    if not hasattr(response.candidates[0].content, 'parts') or not response.candidates[0].content.parts:
                         finish_reason = response.candidates[0].finish_reason if response.candidates else "Unknown"
                         log.error(f"Gemini response missing content parts. Finish Reason: {finish_reason}")
                         raise LLMError(f"Gemini response missing content. Finish Reason: {finish_reason}")


                    content = response.text # Access the combined text directly
                    log.info(f"Received response from {selected_model}.")
                    # log.debug(f"Response (first 100 chars): {content[:100]}...")
                    return content.strip()

                else:
                    raise ValueError(f"Unsupported or unknown model type: {selected_model}")

            except (openai.APIError, openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError, genai.types.generation_types.StopCandidateException) as e:
                last_exception = e
                log.warning(f"LLM API error on attempt {attempt + 1}/{retry_attempts} for model {selected_model}: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            except Exception as e:
                # Catch unexpected errors
                last_exception = e
                log.error(f"Unexpected error during LLM call (attempt {attempt + 1}/{retry_attempts}) for model {selected_model}: {e}", exc_info=True)
                time.sleep(retry_delay)

        # If all retries fail
        log.error(f"LLM API call failed after {retry_attempts} attempts for model {selected_model}.")
        raise LLMError(f"LLM API call failed after {retry_attempts} attempts: {last_exception}") from last_exception

    def generate_json_response(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Generates a response expected to be in JSON format and parses it.

        Uses generate_response and adds JSON parsing with error handling.
        Instructs the model (especially Gemini) via prompt to return JSON.
        For OpenAI, sets json_mode=True if not already set.
        """
        model_name = kwargs.get('model_name', config.DEFAULT_LLM_MODEL)
        prompt = args[0] if args else kwargs.get('prompt', '')

        # Modify prompt/kwargs for JSON output
        if self._is_openai_model(model_name):
            kwargs['json_mode'] = True
            # Ensure prompt instructs JSON output for OpenAI's JSON mode
            if "json" not in prompt.lower():
                 log.warning("Using OpenAI JSON mode, but prompt might not explicitly ask for JSON.")
                 # Consider adding a standard suffix like "\n\nOutput ONLY JSON." if needed.
        elif self._is_gemini_model(model_name):
            # Explicitly instruct Gemini to output JSON
            if "json" not in prompt.lower():
                prompt += "\n\nImportant: Respond ONLY with valid JSON that conforms to the requested structure. Do not include any explanatory text before or after the JSON object."
                if args:
                    args = (prompt,) + args[1:]
                else:
                    kwargs['prompt'] = prompt
        else:
             log.warning(f"JSON mode requested for unknown model type {model_name}. Relying on prompt instructions.")


        raw_response = self.generate_response(*args, **kwargs)

        try:
            # Basic cleaning: Gemini might sometimes include ```json ... ``` markers
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            parsed_json = json.loads(cleaned_response)
            log.info("Successfully parsed JSON response.")
            return parsed_json
        except json.JSONDecodeError as e:
            log.error(f"Failed to decode LLM response as JSON. Error: {e}", exc_info=True)
            log.error(f"Raw response was:\n{raw_response}")
            raise LLMError(f"Failed to parse LLM response as JSON: {e}. Raw response: {raw_response[:500]}...") from e
        except Exception as e:
             log.error(f"Unexpected error parsing JSON response: {e}", exc_info=True)
             log.error(f"Raw response was:\n{raw_response}")
             raise LLMError(f"Unexpected error parsing JSON response: {e}") from e


# Example Usage (can be removed or moved to tests)
# if __name__ == '__main__':
#     try:
#         llm_interface = LLMInterface()

#         # --- Test OpenAI (if configured) ---
#         if llm_interface.openai_client:
#             print("\n--- Testing OpenAI ---")
#             try:
#                 # Simple text generation
#                 openai_prompt = "Explain the concept of market volatility in simple terms."
#                 openai_response = llm_interface.generate_response(openai_prompt, model_name="gpt-3.5-turbo") # Use a cheaper model for testing
#                 print(f"OpenAI Response:\n{openai_response}")

#                 # JSON generation test
#                 openai_json_prompt = "Create a JSON object representing a user with name 'Alice' and age 30."
#                 openai_json_response = llm_interface.generate_json_response(openai_json_prompt, model_name="gpt-3.5-turbo")
#                 print(f"\nOpenAI JSON Response:\n{openai_json_response}")

#             except (LLMError, ValueError) as e:
#                 print(f"OpenAI Test Error: {e}")
#         else:
#             print("\n--- Skipping OpenAI Tests (Not Configured) ---")


#         # --- Test Gemini (if configured) ---
#         if llm_interface.gemini_model:
#             print("\n--- Testing Gemini ---")
#             try:
#                 # Simple text generation
#                 gemini_prompt = "What are the main differences between stocks and bonds?"
#                 gemini_response = llm_interface.generate_response(gemini_prompt, model_name="gemini-pro")
#                 print(f"Gemini Response:\n{gemini_response}")

#                 # JSON generation test
#                 gemini_json_prompt = "Generate a JSON object describing a product with fields 'name' (string) and 'price' (float). Example: name='Laptop', price=1200.50."
#                 # Prompt needs explicit JSON instruction for Gemini
#                 gemini_json_response = llm_interface.generate_json_response(gemini_json_prompt, model_name="gemini-pro")
#                 print(f"\nGemini JSON Response:\n{gemini_json_response}")

#             except (LLMError, ValueError) as e:
#                 print(f"Gemini Test Error: {e}")
#         else:
#             print("\n--- Skipping Gemini Tests (Not Configured) ---")


#     except ConfigError as ce:
#         print(f"Configuration Error: {ce}")
#     except Exception as ex:
#         print(f"An unexpected error occurred: {ex}")
