import os
import json
import shutil
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from ... import config
from ...utils.logger import log
from ...utils.exceptions import OptimizationServiceError, MemoryQueryError, LLMError, ConfigError, MemdirIOError
from ...models.memory_entry import MemoryEntry, MemoryEntryType
from ..memory_service.storage import MemoryStorage
from ...interfaces.large_language_model import LLMInterface

# --- Constants ---
OPTIMIZATION_SERVICE_SOURCE = "OptimizationService"
PROMPT_EVALUATION_SUBDIR = "evaluation"
PROMPT_TRADING_SUBDIR = "trading"
PROMPT_ARCHIVE_SUBDIR = "archive" # Subdirectory within prompts/trading for old versions

# Example prompt structure (adapt as needed)
PROMPT_EVALUATION_TEMPLATE = """
You are an AI assistant evaluating the effectiveness of trading prompts used by another AI.
Analyze the historical performance associated with the following prompt version.

Prompt Content (Version {prompt_version}):
```
{prompt_content}
```

Historical Performance Summary (Last {days_history} days):
- Signals Generated: {signals_generated}
- Trades Executed: {trades_executed}
- Win Rate: {win_rate:.2f}%
- Average Profit/Loss per Trade: {avg_pl:.2f} {currency}
- Key Errors Encountered (Count): {error_summary}
- Example Successful Signal Rationale: {example_success_rationale}
- Example Failed Signal Rationale: {example_fail_rationale}

Task:
1.  Critique the prompt based on the performance data. Identify potential weaknesses or areas for improvement (e.g., clarity, missing context, leading instructions).
2.  Suggest specific, actionable improvements to the prompt content to potentially enhance trading performance (e.g., request specific data points, refine output format instructions, add risk considerations).
3.  Estimate the potential performance impact of your suggested changes (e.g., slight improvement, moderate improvement, significant improvement).

Output ONLY a valid JSON object containing the fields "critique", "suggested_prompt_changes", and "estimated_impact".
Example Output:
{{
  "critique": "The prompt is clear but lacks specific instructions on handling volatile market conditions. The output format could be more strictly defined.",
  "suggested_prompt_changes": "Add a section asking the AI to consider current market volatility (e.g., VIX). Specify JSON output schema more rigidly, including required fields and types.",
  "estimated_impact": "moderate improvement"
}}
"""

class OptimizationEngine:
    """
    Automates the improvement of system performance by tuning AI prompts
    (and potentially strategy parameters later).
    """

    def __init__(
        self,
        memory_storage: MemoryStorage,
        llm_interface: LLMInterface
    ):
        self.memory = memory_storage
        self.llm = llm_interface
        self.prompts_path = config.PROMPTS_PATH
        self.prompt_trading_path = os.path.join(self.prompts_path, PROMPT_TRADING_SUBDIR)
        self.prompt_archive_path = os.path.join(self.prompt_trading_path, PROMPT_ARCHIVE_SUBDIR)
        self.prompt_evaluation_path = os.path.join(self.prompts_path, PROMPT_EVALUATION_SUBDIR)

        os.makedirs(self.prompt_trading_path, exist_ok=True)
        os.makedirs(self.prompt_archive_path, exist_ok=True)
        os.makedirs(self.prompt_evaluation_path, exist_ok=True)

        log.info("OptimizationEngine initialized.")

    def _get_prompt_performance_data(self, prompt_name: str, days_history: int) -> Dict[str, Any]:
        """
        Queries memory for performance metrics associated with a specific prompt.
        This is a simplified example; real implementation needs robust tracking.
        """
        log.debug(f"Querying performance data for prompt '{prompt_name}' over last {days_history} days.")
        # This requires that MemoryEntry payloads for ANALYSIS, SIGNAL, TRADE, ERROR
        # consistently include the 'prompt_name' or 'prompt_version' used.
        # This is a complex query and likely slow without proper indexing.

        # --- Placeholder Implementation ---
        # In a real system, you'd query MemoryStorage for entries related to
        # `prompt_name` within the time range and calculate metrics like:
        # - Number of signals generated by analyses using this prompt
        # - Number of trades resulting from those signals
        # - P/L of those trades
        # - Error rates associated with analyses using this prompt
        # This requires linking signals/trades back to the analysis entry.
        log.warning(f"Performance data querying for prompt '{prompt_name}' is a placeholder.")
        return {
            "prompt_version": "v1.0", # Placeholder version
            "signals_generated": 50,
            "trades_executed": 40,
            "win_rate": 55.0, # %
            "avg_pl": 15.50, # $
            "currency": "USD",
            "error_summary": {"ParsingError": 5, "Timeout": 2},
            "example_success_rationale": "Identified strong uptrend based on moving averages.",
            "example_fail_rationale": "Missed sudden news impact causing reversal."
        }
        # --- End Placeholder ---

    def _load_prompt_content(self, prompt_name: str) -> str:
        """Loads the content of a specific trading prompt."""
        filepath = os.path.join(self.prompt_trading_path, prompt_name)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            log.error(f"Trading prompt file not found: {filepath}")
            raise ConfigError(f"Trading prompt file missing: {filepath}")
        except Exception as e:
            log.error(f"Error loading trading prompt {filepath}: {e}", exc_info=True)
            raise ConfigError(f"Failed to load trading prompt {filepath}: {e}") from e

    def _archive_prompt(self, prompt_name: str, version: str) -> str:
        """Moves the current prompt file to the archive directory with a version suffix."""
        current_filepath = os.path.join(self.prompt_trading_path, prompt_name)
        archive_filename = f"{os.path.splitext(prompt_name)[0]}_{version}{os.path.splitext(prompt_name)[1]}"
        archive_filepath = os.path.join(self.prompt_archive_path, archive_filename)
        log.info(f"Archiving prompt '{prompt_name}' (version {version}) to '{archive_filepath}'")
        try:
            shutil.move(current_filepath, archive_filepath)
            return archive_filepath
        except OSError as e:
            log.error(f"Failed to archive prompt {prompt_name} to {archive_filepath}: {e}", exc_info=True)
            raise OptimizationServiceError(f"Failed to archive prompt {prompt_name}: {e}") from e

    def _save_new_prompt(self, prompt_name: str, new_content: str) -> str:
        """Saves the new prompt content, overwriting the file in the trading directory."""
        filepath = os.path.join(self.prompt_trading_path, prompt_name)
        log.info(f"Saving new version of prompt '{prompt_name}'")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return filepath
        except OSError as e:
            log.error(f"Failed to save new prompt {prompt_name}: {e}", exc_info=True)
            raise OptimizationServiceError(f"Failed to save new prompt {prompt_name}: {e}") from e

    def optimize_prompt(
        self,
        prompt_name: str, # e.g., "default_trading_prompt.txt"
        evaluation_prompt_name: str = "default_evaluation_prompt.txt", # Prompt used for evaluation itself
        days_history: int = config.OPTIMIZATION_MEMORY_QUERY_DAYS,
        improvement_threshold: float = config.OPTIMIZATION_PROMPT_THRESHOLD
        ) -> bool:
        """
        Performs one cycle of prompt optimization for a given trading prompt.

        Args:
            prompt_name: The filename of the trading prompt to optimize.
            evaluation_prompt_name: The filename of the prompt used for evaluation.
            days_history: How many days of performance data to consider.
            improvement_threshold: Minimum estimated improvement needed to apply changes (not strictly enforced yet).

        Returns:
            True if a new prompt version was saved, False otherwise.
        """
        log.info(f"Starting optimization cycle for prompt: {prompt_name}")
        optimization_payload = {
            "optimization_type": "prompt",
            "target_prompt": prompt_name,
            "evaluation_prompt": evaluation_prompt_name,
            "days_history": days_history,
            "improvement_threshold": improvement_threshold,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        prompt_updated = False

        try:
            # 1. Load Current Prompt Content
            current_prompt_content = self._load_prompt_content(prompt_name)
            optimization_payload["current_prompt_content_preview"] = current_prompt_content[:200] + "..."

            # 2. Get Performance Data (Placeholder)
            performance_data = self._get_prompt_performance_data(prompt_name, days_history)
            optimization_payload["performance_data_summary"] = performance_data

            # 3. Load Evaluation Prompt Template
            eval_prompt_template_path = os.path.join(self.prompt_evaluation_path, evaluation_prompt_name)
            try:
                 with open(eval_prompt_template_path, 'r', encoding='utf-8') as f:
                      eval_prompt_template = f.read()
            except FileNotFoundError:
                 log.error(f"Evaluation prompt file not found: {eval_prompt_template_path}. Using default template.")
                 # Fallback to the default template defined as constant
                 eval_prompt_template = PROMPT_EVALUATION_TEMPLATE # Use the constant if file missing
            except Exception as e:
                 log.error(f"Error loading evaluation prompt {eval_prompt_template_path}: {e}. Using default template.", exc_info=True)
                 eval_prompt_template = PROMPT_EVALUATION_TEMPLATE


            # 4. Format Evaluation Prompt
            formatted_eval_prompt = eval_prompt_template.format(
                prompt_version=performance_data.get("prompt_version", "unknown"),
                prompt_content=current_prompt_content,
                days_history=days_history,
                **performance_data # Pass performance metrics directly
            )
            optimization_payload["evaluation_prompt_sent"] = formatted_eval_prompt[:500] + "..." # Log preview

            # 5. Call LLM for Evaluation and Suggestions
            log.debug("Calling LLM for prompt evaluation and suggestions...")
            # Use the specific model configured for optimization tasks
            optimization_model = config.OPTIMIZATION_LLM_MODEL
            eval_response_json = self.llm.generate_json_response(
                prompt=formatted_eval_prompt,
                model_name=optimization_model,
                temperature=0.5 # Moderate temperature for creative suggestions
            )
            optimization_payload["evaluation_llm_response"] = eval_response_json
            optimization_payload["evaluation_model_used"] = optimization_model # Record model used

            # 6. Parse Evaluation Response
            critique = eval_response_json.get("critique")
            suggested_changes = eval_response_json.get("suggested_prompt_changes")
            estimated_impact = eval_response_json.get("estimated_impact", "unknown")
            log.info(f"LLM Evaluation: Critique='{critique}', Suggestions='{suggested_changes}', Impact='{estimated_impact}'")

            # 7. Decide whether to apply changes (Simple logic for now)
            # TODO: Implement more robust decision logic based on estimated_impact and threshold
            apply_changes = bool(suggested_changes) # Apply if any suggestions are made
            optimization_payload["decision_to_apply"] = apply_changes

            if apply_changes:
                log.info(f"Applying suggested changes to prompt '{prompt_name}'.")
                # This is a simplification - ideally, the LLM would output the *entire* new prompt.
                # For now, we append suggestions as comments or try basic replacement if possible.
                # A better approach involves a separate LLM call to *rewrite* the prompt based on suggestions.
                new_prompt_content = current_prompt_content + "\n\n# --- Suggested Improvements (v" + datetime.now().strftime('%Y%m%d%H%M') + ") ---\n" + suggested_changes

                # 8. Archive Old Prompt
                archived_path = self._archive_prompt(prompt_name, performance_data.get("prompt_version", "unknown"))
                optimization_payload["archived_prompt_path"] = archived_path

                # 9. Save New Prompt
                saved_path = self._save_new_prompt(prompt_name, new_prompt_content)
                optimization_payload["new_prompt_path"] = saved_path
                optimization_payload["new_prompt_content_preview"] = new_prompt_content[:200] + "..."
                prompt_updated = True
                log.info(f"Successfully updated prompt '{prompt_name}'. Archived old version to '{archived_path}'.")

                # Save a PROMPT_UPDATE memory entry
                update_payload = {
                    "prompt_name": prompt_name,
                    "old_version": performance_data.get("prompt_version", "unknown"),
                    "new_version": "v" + datetime.now().strftime('%Y%m%d%H%M'), # Simple timestamp version
                    "changes_applied": suggested_changes,
                    "evaluation_critique": critique,
                    "estimated_impact": estimated_impact,
                    "optimization_run_id": optimization_payload.get("run_id", None) # Link if part of a larger run
                }
                update_entry = MemoryEntry(entry_type=MemoryEntryType.PROMPT_UPDATE, source_service=OPTIMIZATION_SERVICE_SOURCE, payload=update_payload)
                self.memory.save_memory(update_entry)

            else:
                log.info(f"No changes applied to prompt '{prompt_name}' based on evaluation.")


        except (MemoryQueryError, LLMError, ConfigError, OptimizationServiceError, MemdirIOError) as e:
            log.error(f"Optimization cycle failed for prompt '{prompt_name}': {e}", exc_info=True)
            optimization_payload["error"] = str(e)
            optimization_payload["status"] = "failed"
        except Exception as e:
            log.critical(f"Unexpected critical error during prompt optimization for '{prompt_name}': {e}", exc_info=True)
            optimization_payload["error"] = f"Critical: {str(e)}"
            optimization_payload["status"] = "critical_failure"

        # Save optimization run details to memory
        optimization_payload.setdefault("status", "completed")
        run_entry = MemoryEntry(
            entry_type=MemoryEntryType.OPTIMIZATION_RUN,
            source_service=OPTIMIZATION_SERVICE_SOURCE,
            payload=optimization_payload
        )
        try:
            self.memory.save_memory(run_entry)
        except MemoryServiceError as mem_err:
            log.error(f"Failed to save optimization run memory entry: {mem_err}")

        return prompt_updated

    def run_optimization_cycle(self):
        """Runs the optimization process for configured components."""
        log.info("Starting scheduled optimization cycle...")

        if not config.OPTIMIZATION_ENABLED:
            log.info("Optimization cycle skipped: Disabled in configuration.")
            return

        # --- Optimize Prompts ---
        # Find all prompts in the trading directory (excluding archive)
        try:
            trading_prompts = [
                f for f in os.listdir(self.prompt_trading_path)
                if os.path.isfile(os.path.join(self.prompt_trading_path, f)) and f != os.path.basename(self.prompt_archive_path)
            ]
            log.info(f"Found trading prompts to potentially optimize: {trading_prompts}")

            for prompt_file in trading_prompts:
                 self.optimize_prompt(prompt_file) # Use default evaluation prompt

        except OSError as e:
             log.error(f"Failed to list trading prompts in {self.prompt_trading_path}: {e}", exc_info=True)
        except Exception as e:
             log.error(f"Error during prompt optimization loop: {e}", exc_info=True)


        # --- Optimize Frequency ---
        # (FrequencyAnalyzer is called separately, likely by Orchestrator before main loop)

        # --- Optimize Strategy Parameters (Future) ---
        # log.info("Strategy parameter tuning not yet implemented.")

        log.info("Optimization cycle finished.")


# Example Usage (Requires setting up interfaces and storage)
# if __name__ == '__main__':
#     print("Testing OptimizationEngine...")
#     # Requires MemoryStorage, LLMInterface, config, and dummy prompt files

#     from unittest.mock import MagicMock
#     mock_storage = MagicMock(spec=MemoryStorage)
#     mock_llm = MagicMock(spec=LLMInterface)

#     # --- Mock LLM Eval Response ---
#     mock_llm.generate_json_response.return_value = {
#         "critique": "Needs more detail on risk.",
#         "suggested_prompt_changes": "Add instruction: 'Consider max drawdown risk.'",
#         "estimated_impact": "moderate improvement"
#     }
#     # --- Mock Memory ---
#     mock_storage.query_memories.return_value = [] # Simulate no relevant history for simplicity
#     mock_storage.save_memory.return_value = "mock_opt_filename"
#     # --- Mock Filesystem ---
#     engine = OptimizationEngine(mock_storage, mock_llm) # Creates dirs

#     # Create dummy trading prompt
#     dummy_trading_prompt_name = "test_trade_prompt.txt"
#     dummy_trading_path = os.path.join(engine.prompt_trading_path, dummy_trading_prompt_name)
#     with open(dummy_trading_path, "w") as f:
#         f.write("Initial prompt content.\nAnalyze {symbol}.")

#     # Create dummy evaluation prompt (or let it use default constant)
#     dummy_eval_prompt_name = "test_eval_prompt.txt"
#     dummy_eval_path = os.path.join(engine.prompt_evaluation_path, dummy_eval_prompt_name)
#     # with open(dummy_eval_path, "w") as f:
#     #     f.write(PROMPT_EVALUATION_TEMPLATE) # Write the default template

#     # --- End Setup ---

#     try:
#         print(f"Optimizing prompt: {dummy_trading_prompt_name}")
#         updated = engine.optimize_prompt(dummy_trading_prompt_name, dummy_eval_prompt_name)
#         print(f"Prompt updated: {updated}")

#         # Verify mocks
#         mock_llm.generate_json_response.assert_called_once()
#         # Check if prompt was archived (moved) and new one saved (written)
#         # This requires more complex filesystem mocking or actual file checks

#         # Check if memory entries were saved (optimization run + prompt update)
#         print(f"Memory save calls: {mock_storage.save_memory.call_count}")
#         # print(mock_storage.save_memory.call_args_list)


#     except Exception as e:
#         print(f"\nError during OptimizationEngine test: {e}")
#     finally:
#         # Clean up dummy files/dirs
#         shutil.rmtree(config.PROMPTS_PATH, ignore_errors=True)
