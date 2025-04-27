import os
import json
import time
from typing import List, Dict, Any, Optional

from .storage import MemoryStorage, NEW_DIR, CUR_DIR
from ...interfaces.large_language_model import LLMInterface
from ...models.memory_entry import MemoryEntry, MemoryMetadata, MemoryEntryType
from ...utils.logger import log
from ...utils.exceptions import MemoryServiceError, MemdirIOError, LLMError
from ... import config

# --- Constants ---
ORGANIZER_SOURCE_SERVICE = "MemoryOrganizer"
DEFAULT_PROCESS_BATCH_SIZE = 100 # Process N files per run
DEFAULT_PROCESS_DELAY_SECONDS = 0.1 # Small delay between processing files

# Example prompt structure (adapt as needed)
MEMORY_TAGGER_PROMPT_TEMPLATE = """
You are an AI assistant responsible for organizing trading system memory entries.
Analyze the following memory entry (JSON format) which represents a single event or data point logged by the system.
Based ONLY on the content provided in the JSON, perform the following tasks:
1.  Identify relevant keywords (max 5, comma-separated). Focus on symbols, actions, statuses, error types, or key metrics.
2.  Write a concise one-sentence summary of the event described in the memory entry.
3.  Suggest relevant flags (choose from the allowed list below) that categorize this entry. Include the original entry_type as a flag if applicable (e.g., Flag_Trade, Flag_Error). Add specific flags like Symbol_XYZ based on the payload content.

Allowed Flags: {allowed_flags}

Memory Entry JSON:
```json
{memory_json_content}
```

Output ONLY a valid JSON object containing the fields "keywords", "summary", and "suggested_flags". Do not include any other text before or after the JSON object.
Example Output:
{{
  "keywords": "AAPL, buy, filled, order",
  "summary": "Successfully executed buy order for 10 shares of AAPL.",
  "suggested_flags": ["Flag_Trade", "Symbol_AAPL", "Status_Filled"]
}}
"""

# Define allowed flags dynamically or statically
ALLOWED_FLAGS = [
    f"Flag_{mem_type.value}" for mem_type in MemoryEntryType
] + [
    "Status_Filled", "Status_Rejected", "Status_Error", "Status_Success",
    "Action_Buy", "Action_Sell", "Action_Hold",
    "Sentiment_Positive", "Sentiment_Negative", "Sentiment_Neutral",
    "Risk_High", "Risk_Low",
    "Important"
    # Add Symbol_XYZ dynamically based on content later if needed, or rely on keywords
]


class MemoryOrganizer:
    """
    Processes new memory files, uses AI to add metadata (tags, summary, flags),
    and moves them to the 'cur' directory.
    """

    def __init__(self, storage: MemoryStorage, llm_interface: LLMInterface):
        self.storage = storage
        self.llm = llm_interface
        # Use the specific model configured for memory organization
        self.tagging_model = config.MEMORY_ORGANIZATION_LLM_MODEL
        log.info(f"MemoryOrganizer initialized. Using model '{self.tagging_model}' for tagging.")

    def _generate_metadata(self, entry: MemoryEntry) -> Optional[MemoryMetadata]:
        """Uses LLM to generate keywords, summary, and flags for a memory entry."""
        try:
            entry_json_str = entry.model_dump_json()

            # Prepare the prompt
            allowed_flags_str = ", ".join(ALLOWED_FLAGS)
            prompt = MEMORY_TAGGER_PROMPT_TEMPLATE.format(
                allowed_flags=allowed_flags_str,
                memory_json_content=entry_json_str
            )

            # Use LLMInterface to get JSON response
            # Use a potentially cheaper/faster model if configured and available
            response_json = self.llm.generate_json_response(
                prompt=prompt,
                model_name=self.tagging_model,
                temperature=0.2, # Lower temperature for more deterministic tagging
                max_tokens=200 # Adjust as needed
            )

            # Validate and parse the response
            if not isinstance(response_json, dict):
                 log.error(f"LLM metadata response is not a dictionary for entry {entry.entry_id}. Response: {response_json}")
                 return None

            keywords_str = response_json.get("keywords")
            summary = response_json.get("summary")
            suggested_flags = response_json.get("suggested_flags")

            # Basic validation
            if not isinstance(keywords_str, str) or not isinstance(summary, str) or not isinstance(suggested_flags, list):
                 log.error(f"Invalid format in LLM metadata response for entry {entry.entry_id}. Response: {response_json}")
                 return None

            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            # Filter suggested flags against allowed list? Optional, depends on trust level.
            valid_suggested_flags = [flag for flag in suggested_flags if isinstance(flag, str)] # Basic type check

            metadata = MemoryMetadata(
                keywords=keywords,
                summary=summary,
                suggested_flags=valid_suggested_flags
                # relationships can be added later if needed
            )
            log.debug(f"Generated metadata for entry {entry.entry_id}: {metadata.model_dump()}")
            return metadata

        except LLMError as e:
            log.error(f"LLM error generating metadata for entry {entry.entry_id}: {e}", exc_info=True)
            return None # Proceed without metadata on LLM failure
        except Exception as e:
            log.error(f"Unexpected error generating metadata for entry {entry.entry_id}: {e}", exc_info=True)
            return None

    def process_single_entry(self, filename_new: str) -> bool:
        """Processes a single file from the 'new' directory."""
        log.debug(f"Processing new memory file: {filename_new}")
        new_filepath = os.path.join(self.storage.new_path, filename_new)
        processed_successfully = False
        tmp_proc_filepath = None # Initialize here

        try:
            # 1. Read the original entry
            entry = self.storage.read_memory(NEW_DIR, filename_new)

            # 2. Generate AI Metadata
            ai_metadata = self._generate_metadata(entry)

            # 3. Update the entry object
            if ai_metadata:
                entry.metadata = ai_metadata
                log.info(f"Added AI metadata to entry {entry.entry_id}")
            else:
                log.warning(f"Proceeding without AI metadata for entry {entry.entry_id} ({filename_new})")

            # 4. Determine final flags
            final_flags = set("S") # Add 'Seen' flag
            if ai_metadata and ai_metadata.suggested_flags:
                 # Add suggested flags, potentially filtering/validating them further
                 # For now, add all string flags returned
                 valid_ai_flags = {flag for flag in ai_metadata.suggested_flags if isinstance(flag, str)}
                 final_flags.update(valid_ai_flags)
                 # Add symbol flag if present in payload
                 if 'symbol' in entry.payload and isinstance(entry.payload['symbol'], str):
                      final_flags.add(f"Symbol_{entry.payload['symbol'].upper()}")

            final_flags_str = "".join(sorted(list(final_flags)))

            # 5. Save updated entry to a temporary location (using storage's atomic save logic indirectly)
            # We need to write the *updated* content. Let's write directly to tmp, then move to cur.
            updated_entry_json = entry.model_dump_json(indent=2)
            updated_entry_bytes = updated_entry_json.encode('utf-8')

            # Create a temporary filename in the tmp dir
            tmp_proc_filename = f"proc_{filename_new}" # Add prefix to avoid collision
            tmp_proc_filepath = os.path.join(self.storage.tmp_path, tmp_proc_filename)

            with open(tmp_proc_filepath, 'wb') as f:
                f.write(updated_entry_bytes)

            # 6. Determine final filename in 'cur'
            parsed_original = self.storage._parse_filename(filename_new)
            if not parsed_original:
                 raise MemdirIOError(f"Cannot process file: Failed to parse original filename {filename_new}")

            filename_base = f"{parsed_original['timestamp_ns']}.{parsed_original['unique_id']}.{parsed_original['hostname']}"
            # Ensure :2, is added only if flags exist
            if final_flags_str:
                cur_filename = f"{filename_base}:2,{final_flags_str}"
            else:
                # According to Maildir spec, if no flags, the :2, part is omitted.
                cur_filename = filename_base
            cur_filepath = os.path.join(self.storage.cur_path, cur_filename)

            # 7. Atomically move the processed temporary file to the final 'cur' location
            os.rename(tmp_proc_filepath, cur_filepath)
            log.debug(f"Moved processed file to {cur_filepath}")

            # 8. Delete the original file from 'new'
            try:
                os.remove(new_filepath)
                log.info(f"Successfully processed and moved '{filename_new}' to '{cur_filename}' in cur.")
                processed_successfully = True
            except OSError as e:
                log.error(f"Failed to remove original file {new_filepath} after processing: {e}. Manual cleanup might be needed.", exc_info=True)
                # The processed file is already in 'cur', so we don't rollback, just log the cleanup error.

        except (MemdirIOError, FileNotFoundError) as e:
            log.error(f"Filesystem error processing {filename_new}: {e}", exc_info=True)
            # Depending on the error, might move to an error dir instead of leaving in new
        except Exception as e:
            log.error(f"Unexpected error processing {filename_new}: {e}", exc_info=True)

        finally:
             # Clean up tmp file if it still exists (e.g., if rename failed)
             # Check if tmp_proc_filepath was assigned before checking existence
             if tmp_proc_filepath and os.path.exists(tmp_proc_filepath):
                  try:
                       os.remove(tmp_proc_filepath)
                  except OSError as cleanup_e:
                       log.error(f"Failed to clean up temporary processed file {tmp_proc_filepath}: {cleanup_e}")

        return processed_successfully


    def process_new_memories(self, batch_size: int = DEFAULT_PROCESS_BATCH_SIZE) -> int:
        """
        Processes a batch of files from the 'new' directory.

        Args:
            batch_size: The maximum number of files to process in this run.

        Returns:
            The number of files successfully processed.
        """
        processed_count = 0
        try:
            new_files = self.storage.list_files(NEW_DIR)
            if not new_files:
                log.debug("No new memory files to process.")
                return 0

            log.info(f"Found {len(new_files)} new memory files. Processing up to {batch_size}...")

            # Sort files (e.g., oldest first) to process in order
            new_files.sort()

            for i, filename in enumerate(new_files):
                if i >= batch_size:
                    log.info(f"Reached batch size limit ({batch_size}). Will process remaining files later.")
                    break

                if self.process_single_entry(filename):
                    processed_count += 1

                # Optional small delay to avoid overwhelming resources/APIs
                time.sleep(DEFAULT_PROCESS_DELAY_SECONDS)


        except MemdirIOError as e:
            log.error(f"Failed to list files in 'new' directory: {e}", exc_info=True)
        except Exception as e:
            log.error(f"Unexpected error during processing of new memories: {e}", exc_info=True)

        log.info(f"Finished processing batch. Successfully processed {processed_count} files.")
        return processed_count

# Example Usage (can be removed or moved to tests)
# if __name__ == "__main__":
#     print("Testing MemoryOrganizer...")
#     # Requires MemoryStorage and LLMInterface to be initialized
#     try:
#         storage = MemoryStorage()
#         llm_interface = LLMInterface() # Assumes config is set up
#         organizer = MemoryOrganizer(storage, llm_interface)

#         # Create some dummy files in 'new' for testing
#         print("Creating dummy files in 'new'...")
#         entry_trade = MemoryEntry(entry_type=MemoryEntryType.TRADE, source_service="TestSetup", payload={"symbol": "TSLA", "side": "buy", "qty": 10, "status": "filled"})
#         entry_error = MemoryEntry(entry_type=MemoryEntryType.ERROR, source_service="AIService", payload={"error_message": "API connection timeout", "details": "..."})
#         fname_trade = storage.save_memory(entry_trade)
#         fname_error = storage.save_memory(entry_error)
#         print(f"Created: {fname_trade}, {fname_error}")

#         # Run processing
#         print("\nRunning process_new_memories...")
#         processed = organizer.process_new_memories(batch_size=5)
#         print(f"Processed {processed} files.")

#         # Check 'cur' directory
#         print("\nFiles in 'cur' after processing:")
#         cur_files = storage.list_files(CUR_DIR)
#         print(cur_files)

#         # Optionally read one back to check metadata
#         if cur_files:
#              try:
#                   read_back = storage.read_memory(CUR_DIR, cur_files[0])
#                   print(f"\nMetadata for {cur_files[0]}:")
#                   print(read_back.metadata.model_dump_json(indent=2) if read_back.metadata else "None")
#              except Exception as read_e:
#                   print(f"Error reading back processed file: {read_e}")


#     except (ConfigError, MemoryServiceError, LLMError) as e:
#         print(f"\nError during MemoryOrganizer test setup or execution: {e}")
#     except Exception as e:
#         print(f"\nUnexpected error during MemoryOrganizer test: {e}")
