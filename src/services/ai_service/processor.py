import os
import json
import uuid
from datetime import datetime, timezone # Import timezone
from typing import Optional, Dict, Any, List

from ... import config
from ...utils.logger import log
from ...utils.exceptions import AIServiceError, LLMError, MemoryServiceError, ConfigError
from ...models.signal import TradingSignal, SignalAction, SignalSource
from ...models.memory_entry import MemoryEntry, MemoryEntryType
from ...models.market_data import MarketDataSnapshot
from ...models.portfolio import Portfolio
from ...interfaces.large_language_model import LLMInterface
from ...interfaces.brokerage import BrokerageInterface # Needed for context if required by prompt
from ...interfaces.perplexity import PerplexityInterface # Import Perplexity
from ..memory_service.storage import MemoryStorage # Direct storage access for now

# --- Constants ---
AI_SERVICE_SOURCE = "AIService"
DEFAULT_PROMPT_FILENAME = "default_trading_prompt.txt" # Example prompt file

class AIServiceProcessor:
    """
    Handles the AI-driven analysis and trading signal generation process.
    Uses LLMs to analyze market data, portfolio status, and historical context.
    """

    def __init__(
        self,
        llm_interface: LLMInterface,
        brokerage_interface: BrokerageInterface, # Pass brokerage for potential context
        memory_storage: MemoryStorage,
        perplexity_interface: Optional[PerplexityInterface] = None # Add Perplexity interface
    ):
        self.llm = llm_interface
        self.brokerage = brokerage_interface # Store for context if needed
        self.memory_storage = memory_storage
        self.perplexity = perplexity_interface # Store Perplexity interface
        self.prompts_path = config.PROMPTS_PATH
        log.info("AIServiceProcessor initialized.")
        if not self.perplexity:
            log.warning("PerplexityInterface not provided to AIServiceProcessor. Market research insights will be unavailable.")

    def _load_prompt(self, prompt_name: str) -> str:
        """Loads a prompt template from the configured prompts directory."""
        # Simple loading for now, could involve versioning later via OptimizationService
        prompt_filepath = os.path.join(self.prompts_path, "trading", prompt_name)
        log.debug(f"Loading prompt from: {prompt_filepath}")
        try:
            with open(prompt_filepath, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            return prompt_template
        except FileNotFoundError:
            log.error(f"Prompt file not found: {prompt_filepath}")
            raise ConfigError(f"Required prompt file missing: {prompt_filepath}")
        except Exception as e:
            log.error(f"Error loading prompt file {prompt_filepath}: {e}", exc_info=True)
            raise ConfigError(f"Failed to load prompt {prompt_filepath}: {e}") from e

    def _format_input_data(
        self,
        prompt_template: str,
        market_data: MarketDataSnapshot,
        portfolio: Portfolio,
        recent_history: Optional[List[MemoryEntry]] = None, # Example history
        perplexity_insights: Optional[str] = None # Add perplexity insights
    ) -> str:
        """Formats the input data, including optional Perplexity insights, into the prompt string."""
        # This needs careful implementation based on the specific prompt structure.
        # Convert complex objects (like market data, portfolio) into a concise
        # text or JSON representation suitable for the LLM.

        # Example formatting (highly dependent on prompt design):
        # Use model_dump directly to get dict, then json.dumps to include None values if needed by prompt
        market_summary = json.dumps(market_data.model_dump(mode='json'), indent=2)
        portfolio_summary = json.dumps(portfolio.model_dump(mode='json', exclude={'positions'}), indent=2) # Exclude detailed positions for brevity maybe?
        positions_summary = json.dumps(
            {sym: pos.model_dump(mode='json') for sym, pos in portfolio.positions.items()},
            indent=2 # Correctly placed inside json.dumps()
        )
        history_summary = "No recent history available."
        if recent_history:
             history_summary = "\n".join([
                 f"- {entry.timestamp.isoformat()}: {entry.entry_type.value} - {entry.payload.get('summary', json.dumps(entry.payload))}"
                 for entry in recent_history[:5] # Limit history length
             ])

        # Prepare perplexity insights string for formatting
        perplexity_summary = perplexity_insights if perplexity_insights else "No market research insights available from Perplexity."

        # Replace placeholders in the template
        try:
            formatted_prompt = prompt_template.format(
                current_datetime_utc=datetime.now(timezone.utc).isoformat(), # Use timezone-aware UTC time
                market_data_json=market_summary,
                portfolio_summary_json=portfolio_summary,
                positions_json=positions_summary,
                recent_history_summary=history_summary,
                target_symbols=", ".join(config.DEFAULT_SYMBOLS), # Example: provide target symbols
                perplexity_insights=perplexity_summary # Add perplexity insights placeholder
                # Add other relevant context variables here
            )
            return formatted_prompt
        except KeyError as e:
             log.error(f"Missing placeholder in prompt template: {e}", exc_info=True)
             raise ConfigError(f"Prompt template formatting error: Missing key {e}")
        except Exception as e:
             log.error(f"Error formatting prompt data: {e}", exc_info=True)
             raise AIServiceError(f"Failed to format prompt data: {e}") from e


    def _parse_llm_response(self, response_json: Dict[str, Any]) -> Optional[TradingSignal]:
        """Parses the LLM's JSON response and validates it into a TradingSignal."""
        try:
            action_str = response_json.get("action")
            symbol = response_json.get("symbol")
            confidence = response_json.get("confidence")
            rationale = response_json.get("rationale")
            target_price = response_json.get("target_price")
            stop_loss_price = response_json.get("stop_loss_price")

            # --- Validation ---
            if not action_str or not symbol:
                log.warning(f"LLM response missing required fields 'action' or 'symbol'. Response: {response_json}")
                return None

            try:
                action = SignalAction(action_str.lower())
            except ValueError:
                log.warning(f"Invalid signal action '{action_str}' in LLM response.")
                return None

            # Only create BUY/SELL signals, treat others (like HOLD) as None for now
            if action not in [SignalAction.BUY, SignalAction.SELL]:
                 log.info(f"LLM recommended action '{action.value}' for {symbol}. No trade signal generated.")
                 # Could generate a 'HOLD' memory entry if needed
                 return None

            # Validate confidence (optional but recommended)
            try:
                confidence_float = float(confidence) if confidence is not None else None
                if confidence_float is not None and not (0.0 <= confidence_float <= 1.0):
                     log.warning(f"Invalid confidence value '{confidence_float}'. Setting to None.")
                     confidence_float = None
            except (ValueError, TypeError):
                log.warning(f"Invalid confidence format '{confidence}'. Setting to None.")
                confidence_float = None

            # Validate prices (optional)
            try:
                 target_price_float = float(target_price) if target_price is not None else None
            except (ValueError, TypeError):
                 log.warning(f"Invalid target_price format '{target_price}'. Setting to None.")
                 target_price_float = None
            try:
                 stop_loss_price_float = float(stop_loss_price) if stop_loss_price is not None else None
            except (ValueError, TypeError):
                 log.warning(f"Invalid stop_loss_price format '{stop_loss_price}'. Setting to None.")
                 stop_loss_price_float = None


            # --- Create Signal ---
            signal = TradingSignal(
                signal_id=f"sig_{uuid.uuid4()}",
                symbol=str(symbol).upper(), # Ensure symbol is uppercase
                action=action,
                source=SignalSource.AI_ANALYSIS,
                confidence=confidence_float,
                target_price=target_price_float,
                stop_loss_price=stop_loss_price_float,
                rationale=str(rationale) if rationale else None,
                # originating_memory_id will be set after saving the analysis memory
            )
            log.info(f"Successfully parsed LLM response into Trading Signal for {signal.symbol}: {action.value}") # Use action enum member here
            return signal

        except Exception as e:
            log.error(f"Error parsing LLM response JSON: {e}. Response: {response_json}", exc_info=True)
            raise AIServiceError(f"Failed to parse LLM response: {e}") from e

    def generate_trading_signal(
        self,
        market_data: MarketDataSnapshot,
        portfolio: Portfolio,
        prompt_name: str = DEFAULT_PROMPT_FILENAME,
        # Add parameters for fetching relevant history if needed
    ) -> Optional[TradingSignal]:
        """
        The main method to generate a trading signal using the AI process.

        Args:
            market_data: Current market data snapshot.
            portfolio: Current portfolio state.
            prompt_name: The name of the prompt file to use (in prompts/trading/).

        Returns:
            A TradingSignal object if a valid signal is generated, otherwise None.
        """
        log.info(f"Starting AI signal generation using prompt: {prompt_name}")
        # Use the specific model configured for trading analysis
        model_to_use = config.TRADING_ANALYSIS_LLM_MODEL
        analysis_memory_payload = {
             "prompt_name": prompt_name,
             "model_used": model_to_use,
             "inputs_summary": { # Store summaries of inputs used
                  "market_data_ts": market_data.timestamp.isoformat(),
                  "portfolio_ts": portfolio.timestamp.isoformat(),
                  "symbols_considered": list(market_data.latest_quotes.keys() if market_data.latest_quotes else []),
             }
        }
        analysis_memory_entry = MemoryEntry(
             entry_type=MemoryEntryType.ANALYSIS,
             source_service=AI_SERVICE_SOURCE,
             payload=analysis_memory_payload
        ) # Create entry early to get its ID

        try:
            # 1. Load Prompt
            prompt_template = self._load_prompt(prompt_name)

            # 2. Get Perplexity Insights (Optional)
            perplexity_query = None
            perplexity_response = None
            if self.perplexity and config.PERPLEXITY_API_KEY:
                # Construct a query based on target symbols or market data
                target_symbols_str = ", ".join(config.DEFAULT_SYMBOLS)
                perplexity_query = f"Provide recent market news and sentiment analysis for the following symbols: {target_symbols_str}."
                log.info(f"Querying Perplexity for market insights: '{perplexity_query}'")
                try:
                    perplexity_response = self.perplexity.get_market_insights(perplexity_query)
                    if perplexity_response:
                        log.info("Received market insights from Perplexity.")
                        analysis_memory_payload["perplexity_query"] = perplexity_query
                        analysis_memory_payload["perplexity_response"] = perplexity_response
                    else:
                        log.warning("No insights received from Perplexity.")
                        analysis_memory_payload["perplexity_query"] = perplexity_query
                        analysis_memory_payload["perplexity_response"] = "Failed to retrieve or empty response."
                except Exception as p_err:
                    log.error(f"Error querying Perplexity: {p_err}", exc_info=True)
                    analysis_memory_payload["perplexity_query"] = perplexity_query
                    analysis_memory_payload["perplexity_error"] = str(p_err)
            else:
                log.info("Perplexity interface not available or API key not set. Skipping market research query.")


            # 3. Format Input Data (Fetch history if needed by the prompt)
            # TODO: Implement fetching relevant history from MemoryStorage based on prompt requirements
            recent_history = None # Placeholder
            formatted_prompt = self._format_input_data(
                prompt_template,
                market_data,
                portfolio,
                recent_history,
                perplexity_response # Pass insights to formatter
            )
            analysis_memory_payload["prompt_sent"] = formatted_prompt # Store the actual prompt sent

            # 4. Call LLM
            llm_response_json = self.llm.generate_json_response(
                prompt=formatted_prompt,
                model_name=model_to_use, # Use the configured trading model
                # Pass temperature, max_tokens from config or defaults?
            )
            analysis_memory_payload["raw_llm_response"] = llm_response_json # Store raw response

            # 5. Parse Response
            signal = self._parse_llm_response(llm_response_json)

            # 6. Finalize and Save Memory
            if signal:
                signal.originating_memory_id = analysis_memory_entry.entry_id
                analysis_memory_payload["generated_signal"] = signal.model_dump(mode='json')
                analysis_memory_entry.payload = analysis_memory_payload # Update payload
                log.info(f"Generated Signal: {signal.action.value} {signal.symbol} (Confidence: {signal.confidence})")
                # Save signal as its own memory entry? Optional.
                # signal_memory = MemoryEntry(entry_type=MemoryEntryType.SIGNAL, ...)
                # self.memory_storage.save_memory(signal_memory)
            else:
                 analysis_memory_payload["generated_signal"] = None
                 analysis_memory_entry.payload = analysis_memory_payload
                 log.info("No actionable trading signal generated by AI.")

            self.memory_storage.save_memory(analysis_memory_entry)
            log.debug(f"Saved analysis memory entry: {analysis_memory_entry.entry_id}")

            return signal

        except (LLMError, MemoryServiceError, ConfigError, AIServiceError) as e:
            log.error(f"Error during AI signal generation pipeline: {e}", exc_info=True)
            # Save error memory entry
            error_payload = {
                 "error_type": type(e).__name__,
                 "error_message": str(e),
                 "stage": "SignalGeneration",
                 "prompt_name": prompt_name,
                 "analysis_memory_id": analysis_memory_entry.entry_id # Link to the analysis attempt
            }
            error_entry = MemoryEntry(
                 entry_type=MemoryEntryType.ERROR,
                 source_service=AI_SERVICE_SOURCE,
                 payload=error_payload
            )
            try:
                 self.memory_storage.save_memory(error_entry)
            except MemoryServiceError as mem_err:
                 log.error(f"Failed to save AI service error memory entry: {mem_err}")
            except MemoryServiceError as mem_err:
                 log.error(f"Failed to save AI service error memory entry: {mem_err}")
            # Still return the signal if it was generated, even if saving failed
            # Use locals() to check if 'signal' was assigned before the exception
            return locals().get('signal', None) # Correct indentation
        except Exception as e:
             log.critical(f"Unexpected critical error in AI signal generation: {e}", exc_info=True)
             # Save critical error memory entry
             error_payload = {
                 "error_type": type(e).__name__,
                 "error_message": str(e),
                 "stage": "SignalGenerationCritical",
                 "prompt_name": prompt_name,
                 "analysis_memory_id": analysis_memory_entry.entry_id
             }
             error_entry = MemoryEntry(entry_type=MemoryEntryType.ERROR, source_service=AI_SERVICE_SOURCE, payload=error_payload)
             try: # Correctly indented try for saving critical error
                 self.memory_storage.save_memory(error_entry)
             except MemoryServiceError as mem_err: # Correctly indented except
                  log.error(f"Failed to save AI service critical error memory entry: {mem_err}")
             # Still return the signal if it was generated, even if saving failed
             return locals().get('signal', None) # Correctly indented return


# Example Usage (Requires setting up interfaces and storage)
# if __name__ == '__main__':
#     print("Testing AIServiceProcessor...")
#     # This requires mocking or initializing:
#     # - config (implicitly done via import)
#     # - LLMInterface
#     # - BrokerageInterface
#     # - MemoryStorage
#     # - A dummy prompt file at trading_system/prompts/trading/default_trading_prompt.txt

#     # --- Setup Mocks/Dummies (Replace with actual initialization) ---
#     from unittest.mock import MagicMock
#     mock_llm = MagicMock(spec=LLMInterface)
#     mock_brokerage = MagicMock(spec=BrokerageInterface)
#     mock_storage = MagicMock(spec=MemoryStorage)

#     # Configure mock LLM response
#     mock_llm.generate_json_response.return_value = {
#         "action": "buy",
#         "symbol": "TEST",
#         "confidence": 0.75,
#         "rationale": "Mock rationale based on positive indicators.",
#         "target_price": 110.0,
#         "stop_loss_price": 95.0
#     }
#     mock_storage.save_memory.return_value = "mock_memory_filename" # Simulate saving

#     # Create dummy market/portfolio data
#     dummy_market_data = MarketDataSnapshot() # Populate if needed by prompt
#     dummy_portfolio = Portfolio(account_id="test_acc", cash=10000, equity=10000, buying_power=20000, portfolio_value=10000) # Populate if needed

#     # Create dummy prompt file
#     prompt_dir = os.path.join(config.PROJECT_ROOT, "prompts", "trading")
#     os.makedirs(prompt_dir, exist_ok=True)
#     dummy_prompt_path = os.path.join(prompt_dir, DEFAULT_PROMPT_FILENAME)
#     dummy_prompt_content = """
#     Analyze the market for {target_symbols}.
#     Market Data: {market_data_json}
#     Portfolio: {portfolio_summary_json}
#     Positions: {positions_json}
#     History: {recent_history_summary}
#     Recommend BUY, SELL, or HOLD for one symbol. Output JSON:
#     {{
#       "action": "buy|sell|hold",
#       "symbol": "SYMBOL",
#       "confidence": 0.0-1.0 (only for buy/sell),
#       "rationale": "...",
#       "target_price": float (optional),
#       "stop_loss_price": float (optional)
#     }}
#     """
#     with open(dummy_prompt_path, "w") as f:
#         f.write(dummy_prompt_content)
#     # --- End Setup ---

#     try:
#         ai_processor = AIServiceProcessor(mock_llm, mock_brokerage, mock_storage)
#         print("AI Processor Initialized.")

#         signal = ai_processor.generate_trading_signal(dummy_market_data, dummy_portfolio)

#         if signal:
#             print("\nGenerated Signal:")
#             print(signal.model_dump_json(indent=2))
#         else:
#             print("\nNo signal generated.")

#         # Verify LLM call
#         mock_llm.generate_json_response.assert_called_once()
#         # Verify memory save calls (should be at least one for analysis)
#         print(f"\nMemory save called {mock_storage.save_memory.call_count} times.")
#         # print(f"Analysis Memory Entry Saved: {mock_storage.save_memory.call_args_list[0]}")


#     except Exception as e:
#         print(f"\nError during AI Service test: {e}")
#     finally:
#          # Clean up dummy prompt
#          if os.path.exists(dummy_prompt_path):
#               os.remove(dummy_prompt_path)
